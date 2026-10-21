# app/services/historical/tarifa_historica_service.py

from collections import defaultdict
from typing import Any, Dict, Optional, TYPE_CHECKING

from loguru import logger

from app.services.historical.calculos import a_float, mayus

if TYPE_CHECKING:
    from app.repositories.postgres.tarifa_historica_repository import TarifaHistoricaRepository


class TarifaHistoricaService:
    """
    Tarifas publicadas de un mes (GET /tariff/historical/{anio}/{mes}).

    Hace 4 consultas (períodos, valores, monomias y componentes) y arma la respuesta anidada
    en memoria. No se usa un solo join porque valores x componentes multiplicaría las filas.
    """

    def __init__(self, repo: "TarifaHistoricaRepository"):
        self.repo = repo

    def obtener_tarifas_mes(
        self,
        anio: int,
        mes: int,
        cod_comercializadora: Optional[str] = None,
        cod_mercado: Optional[str] = None,
        cod_nivel: Optional[str] = None,
        cod_tipo_tarifa: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Returns:
            Dict con 'anio', 'mes', 'total_tarifas' y 'tarifas', o None si no hay
            tarifas publicadas para esos filtros.
        """
        periodos = self.repo.get_periodos_publicados(
            anio,
            mes,
            cod_comercializadora=mayus(cod_comercializadora),
            cod_mercado=mayus(cod_mercado),
            cod_nivel=mayus(cod_nivel),
            cod_tipo_tarifa=mayus(cod_tipo_tarifa),
        )
        if not periodos:
            logger.warning(f"Sin tarifas publicadas para {anio}-{mes:02d} con los filtros dados")
            return None

        ids = [p["id_periodo_tarifario"] for p in periodos]

        valores = defaultdict(list)
        for v in self.repo.get_valores_franja(ids):
            valores[v["id_periodo_tarifario"]].append({
                "codigo_franja": v["codigo_franja"],
                "tipo_hora": v["tipo_hora"],
                "valor": a_float(v["valor"]),
                "unidad": v["unidad"] or "COP/kWh",
                "horas": list(v["horas"]),
            })

        monomias = {m["id_periodo_tarifario"]: m for m in self.repo.get_monomias(ids)}

        componentes = defaultdict(list)
        for c in self.repo.get_componentes(ids):
            componentes[c["id_periodo_tarifario"]].append({
                "cod_componente": c["cod_componente"],
                "valor": a_float(c["valor"]),
            })

        tarifas = []
        for p in periodos:
            pid = p["id_periodo_tarifario"]
            m = monomias.get(pid)
            tarifas.append({
                # El código no lleva el mes: el período va en campos separados
                "codigo": p["codigo_tarifa"],
                "nombre_tarifa": p["nombre_tarifa"],
                "cod_comercializadora": p["cod_comercializadora"],
                "cod_mercado": p["cod_mercado"],
                "cod_nivel": p["cod_nivel"],
                "cod_tipo_tarifa": p["cod_tipo_tarifa"],
                "resolucion_regulatoria": p["resolucion_regulatoria"],
                "numero_version": p["numero_version"],
                "fecha_inicio": p["fecha_inicio"],
                "fecha_fin": p["fecha_fin"],
                "fecha_publicacion": p["fecha_publicacion"],
                "configuracion_horaria": p["configuracion"],
                "monomia": (
                    {"valor": a_float(m["valor"]), "unidad": m["unidad"] or "COP/kWh", "tipo": "CU"}
                    if m else None
                ),
                "valores": valores.get(pid, []),
                "componentes": componentes.get(pid, []),
            })

        return {"anio": anio, "mes": mes, "total_tarifas": len(tarifas), "tarifas": tarifas}