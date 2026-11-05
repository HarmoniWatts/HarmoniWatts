# app/services/historical/tendencia_service.py

from datetime import date
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from loguru import logger

from app.services.historical import COMERCIALIZADORA_POR_DEFECTO
from app.services.historical.calculos import (
    a_float,
    indice_mes,
    mayus,
    meses_entre,
    periodo_desde_indice,
    porcentaje,
    redondear,
)

if TYPE_CHECKING:
    from app.repositories.postgres.tarifa_historica_repository import TarifaHistoricaRepository

VENTANA_MESES = 12


class TendenciaService:
    """
    Tendencia de precios (GET /tariff/historical/trends).

    Reglas:
      - precio_promedio mensual = promedio de las horas con precio (ponderado por horas).
      - Los meses sin datos NO se incluyen en ningún cálculo; se informan en `meses_faltantes`.
      - La variación se calcula contra el mes anterior que tenga datos; si entre ambos hay meses
        faltantes, el punto lo indica en `meses_omitidos`.
      - Sin `hasta`, se usa el último mes publicado; sin `desde`, 12 meses hacia atrás desde `hasta`.
    """

    def __init__(self, repo: "TarifaHistoricaRepository"):
        self.repo = repo

    def obtener_tendencia(
        self,
        cod_mercado: str,
        cod_nivel: str,
        cod_tipo_tarifa: str = "A",
        cod_comercializadora: str = COMERCIALIZADORA_POR_DEFECTO,
        desde: Optional[date] = None,
        hasta: Optional[date] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Returns:
            Dict con la serie y las métricas, o None si no hay datos en el rango.

        Raises:
            ValueError: si `desde` es posterior a `hasta`.
        """
        com = mayus(cod_comercializadora)
        mercado = mayus(cod_mercado)
        nivel = mayus(cod_nivel)
        tipo = mayus(cod_tipo_tarifa)

        # --- Rango solicitado (a nivel de mes) ---
        if hasta is not None:
            fin = (hasta.year, hasta.month)
        else:
            ultimo = self.repo.get_ultimo_periodo(com, mercado, nivel, tipo)
            if not ultimo:
                logger.warning(f"Sin tarifas publicadas para {mercado} {nivel} {tipo}")
                return None
            fin = (ultimo["anio"], ultimo["mes"])

        if desde is not None:
            ini = (desde.year, desde.month)
        else:
            ini = periodo_desde_indice(indice_mes(*fin) - (VENTANA_MESES - 1))

        if indice_mes(*ini) > indice_mes(*fin):
            raise ValueError("'desde' no puede ser posterior a 'hasta'")

        filas = self.repo.get_serie_mensual(com, mercado, nivel, tipo, ini, fin)
        if not filas:
            return None

        # --- Serie mensual ---
        advertencias: List[str] = []
        serie: List[Dict[str, Any]] = []
        crudos: List[Dict[str, Any]] = []   # valores sin redondear, para las métricas
        previo: Optional[Dict[str, Any]] = None

        for f in filas:
            idx = indice_mes(f["anio"], f["mes"])
            prom = a_float(f["precio_promedio"])
            pmin = a_float(f["precio_min"])
            pmax = a_float(f["precio_max"])

            if previo is None:
                variacion, omitidos = None, 0
            else:
                variacion = porcentaje(previo["prom"], prom)
                omitidos = idx - previo["idx"] - 1
                if f["configuracion"] != previo["cfg"]:
                    advertencias.append(
                        f"La configuración horaria cambió de {previo['cfg']} a {f['configuracion']} "
                        f"en {f['anio']}-{f['mes']:02d}; el promedio por hora sigue siendo comparable."
                    )

            if f["horas"] != 24:
                advertencias.append(
                    f"{f['anio']}-{f['mes']:02d}: el promedio usa {f['horas']} de 24 horas."
                )

            serie.append({
                "anio": f["anio"],
                "mes": f["mes"],
                "precio_promedio": redondear(prom),
                "precio_min": redondear(pmin),
                "precio_max": redondear(pmax),
                "variacion": variacion,
                "meses_omitidos": omitidos,
                "configuracion": f["configuracion"],
            })
            crudos.append({"idx": idx, "prom": prom, "min": pmin, "max": pmax})
            previo = {"idx": idx, "prom": prom, "cfg": f["configuracion"]}

        # --- Meses sin datos dentro del rango solicitado ---
        con_datos = {(f["anio"], f["mes"]) for f in filas}
        faltantes = [
            {"anio": a, "mes": m} for a, m in meses_entre(ini, fin) if (a, m) not in con_datos
        ]
        if faltantes:
            lista = ", ".join(f"{p['anio']}-{p['mes']:02d}" for p in faltantes)
            advertencias.append(
                f"Meses sin datos publicados (excluidos de los cálculos): {lista}."
            )

        # --- Métricas de los últimos 12 meses (contados hasta el último mes con datos) ---
        limite = crudos[-1]["idx"] - VENTANA_MESES
        ventana = [c for c in crudos if c["idx"] > limite]
        tendencia_anual = (
            porcentaje(ventana[0]["prom"], ventana[-1]["prom"]) if len(ventana) >= 2 else None
        )

        return {
            "cod_comercializadora": com,
            "mercado": mercado,
            "nivel": nivel,
            "tipo_tarifa": tipo,
            "desde": {"anio": ini[0], "mes": ini[1]},
            "hasta": {"anio": fin[0], "mes": fin[1]},
            "unidad": filas[0].get("unidad") or "COP/kWh",
            "serie": serie,
            "meses_faltantes": faltantes,
            "tendencia_anual": tendencia_anual,
            "precio_min_12m": redondear(min(c["min"] for c in ventana)),
            "precio_max_12m": redondear(max(c["max"] for c in ventana)),
            "advertencias": advertencias,
        }