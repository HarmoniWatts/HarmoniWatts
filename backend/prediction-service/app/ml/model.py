"""Modelo pyfunc: MLP centralizado por clúster + fine-tuning por medidor."""
import json

import joblib
import mlflow.pyfunc
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from app.ml.features import MIN_HISTORY_H, prepare_inputs


class MLP(nn.Module):
    def __init__(self, d_in, hidden=(64, 32)):
        super().__init__()
        layers, d = [], d_in
        for h in hidden:
            layers += [nn.Linear(d, h), nn.ReLU()]
            d = h
        layers.append(nn.Linear(d, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x).squeeze(-1)


class CentralFTForecaster(mlflow.pyfunc.PythonModel):
    """Entrada: DataFrame [METER_NO, DATE_TIME, kwh] con >=504 h horarias previas por medidor.
    Salida: DataFrame [METER_NO, DATE_TIME, forecast_kwh] con las 168 h siguientes."""

    def load_context(self, context):
        self.meta = json.load(open(context.artifacts["meta"]))
        states = torch.load(context.artifacts["states"], map_location="cpu")

        def build(sd):
            net = MLP(self.meta["f_in"], tuple(self.meta["hidden"]))
            net.load_state_dict(sd)
            return net.eval()

        self.cluster_nets = {int(c): build(sd) for c, sd in states["cluster"].items()}
        self.meter_nets = {str(m): build(sd) for m, sd in states["meter"].items()}
        self.cluster_model = joblib.load(context.artifacts["cluster_model"]) if "cluster_model" in context.artifacts else None

    def _assign(self, series):
        """Clúster de un medidor nuevo según la forma de su perfil semanal (>= 3 semanas de historia)."""
        s = series.iloc[-MIN_HISTORY_H:]
        prof = s.groupby(s.index.dayofweek * 24 + s.index.hour).mean().reindex(range(168))
        if self.cluster_model is None or prof.isna().any():
            return int(self.meta["fallback_cluster"])
        z = prof.values.astype(float)
        z = (z - z.mean()) / (z.std() if z.std() > 1e-9 else 1.0)
        return int(self.cluster_model.predict(z[None, :, None])[0])

    def predict(self, context, model_input, params=None):
        prep = prepare_inputs(model_input, self.meta["scale_n"])
        out = []
        with torch.no_grad():
            for j, m in enumerate(prep["meters"]):
                net = self.meter_nets.get(m)                               # 1) red personalizada
                if net is None:                                           # 2) red de su clúster (conocido o asignado por forma)
                    c = self.meta["labels"].get(m)
                    c = self._assign(prep["history"][m]) if c is None else int(c)
                    net = self.cluster_nets[c]
                y = net(torch.from_numpy(prep["X"][:, j, :])).numpy() * prep["scale"][j]
                out.append(pd.DataFrame({"METER_NO": m, "DATE_TIME": prep["fidx"], "forecast_kwh": np.clip(y, 0, None)}))
        return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=["METER_NO", "DATE_TIME", "forecast_kwh"])
