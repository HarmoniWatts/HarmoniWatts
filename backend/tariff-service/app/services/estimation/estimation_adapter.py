# app/services/estimation/estimation_adapter.py
from datetime import date
import calendar

NIVEL_CODIGO = {
    "N 1.1": "N1_1", "N 1.2": "N1_2", "N 1.2-1.3": "N1_2_1_3",
    "N 1.2-50": "N1_2_50", "N 1.2-1.3-50": "N1_2_1_3_50",
    "N 2": "N2", "N 3": "N3", "N 4": "N4",
}
COMP_MAP = {"Gm": "Gm", "Tm": "Tm", "Dm": "Dm", "Cm": "Cm", "PR": "PRm", "Rm": "Rm", "Cfmj": "Cfmj"}


class EstimationAdapter:
    def __init__(self, tarifa_repo):
        self.tarifa_repo = tarifa_repo

    def to_tarifa_tap(self, est: dict, comercializadora_cod: str) -> dict:
        cod_nivel = NIVEL_CODIGO[est["nivel_tension"]]
        # Resolver codigo_tarifa existente para no duplicar
        tarifas = self.tarifa_repo.get_by_combinacion(
            comercializadora_cod, est["mercado"], cod_nivel, est["tipo_tarifa"]
        )
        if not tarifas:
            raise ValueError(
                f"No existe Tarifa para {comercializadora_cod}/{est['mercado']}/"
                f"{cod_nivel}/{est['tipo_tarifa']}; no se puede estimar sobre una tarifa inexistente"
            )
        codigo_tarifa = tarifas[0].codigo_tarifa

        anio, mes = est["anio"], est["mes"]
        ultimo_dia = calendar.monthrange(anio, mes)[1]

        valores = []
        # Monomia (sin franja)
        valores.append({"codigo_franja": None, "valor": est["cu_aplicado"], "unidad": "COP/kWh"})
        # Franjas
        for fj, v in est["valores_franja"].items():
            if v is not None:
                valores.append({"codigo_franja": fj, "valor": v, "unidad": "COP/kWh"})

        componentes = [
            {"cod_componente": COMP_MAP[k], "valor": v}
            for k, v in est["componentes_cu"].items()
        ]
        componentes.append({"cod_componente": "Cfmj", "valor": est["Cmfj"]})

        return {
            "tarifa": {
                "codigo_tarifa": codigo_tarifa,
                "cod_comercializadora": comercializadora_cod,
                "cod_mercado": est["mercado"],
                "cod_nivel": cod_nivel,
                "cod_tipo_tarifa": est["tipo_tarifa"],
                "nombre_tarifa": tarifas[0].nombre_tarifa,
                "resolucion_regulatoria": tarifas[0].resolucion_regulatoria,
                "activa": True,
            },
            "periodo": {
                "anio": anio,
                "mes": mes,
                "fecha_inicio": date(anio, mes, 1),
                "fecha_fin": date(anio, mes, ultimo_dia),
                "estado": "BORRADOR",
            },
            "valores": valores,
            "componentes": componentes,
        }