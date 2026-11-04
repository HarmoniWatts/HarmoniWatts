# app/services/historical/comparacion_service.py

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from loguru import logger

from app.services.historical import COMERCIALIZADORA_POR_DEFECTO
from app.services.historical.calculos import (
    a_float,
    mayus,
    porcentaje,
    promedio,
    redondear,
    variacion,
)

if TYPE_CHECKING:
    from app.repositories.postgres.tarifa_historica_repository import TarifaHistoricaRepository

Periodo = Tuple[int, int]
TIPOS_HORA = ("VALLE", "MEDIA", "PICO")


class PeriodoNoDisponibleError(Exception):
    """No hay tarifa PUBLICADA para la combinación en uno de los períodos a comparar."""

    def __init__(self, lado: str, anio: int, mes: int):
        self.lado = lado
        self.anio = anio
        self.mes = mes
        super().__init__(f"No hay tarifa publicada para el período_{lado} {anio}-{mes:02d}")


class ComparacionService:
    """
    Comparación de dos períodos (GET /tariff/historical/compare).

    Las franjas (F1..F8) no significan lo mismo en todas las configuraciones horarias, por eso
    la comparación se hace por hora (1..24) y por tipo de hora (VALLE/MEDIA/PICO, promedio
    ponderado por horas). Si la configuración cambió entre los períodos, se avisa en `advertencias`.
    """

    def __init__(self, repo: "TarifaHistoricaRepository"):
        self.repo = repo

    # -----------------------------------------------------
    def comparar(
        self,
        cod_mercado: str,
        cod_nivel: str,
        periodo_a: Periodo,
        periodo_b: Periodo,
        cod_tipo_tarifa: str = "A",
        cod_comercializadora: str = COMERCIALIZADORA_POR_DEFECTO,
    ) -> Dict[str, Any]:
        """
        Raises:
            PeriodoNoDisponibleError: si alguno de los dos períodos no tiene tarifa publicada.
        """
        com = mayus(cod_comercializadora)
        mercado = mayus(cod_mercado)
        nivel = mayus(cod_nivel)
        tipo = mayus(cod_tipo_tarifa)

        pa = self._periodo("a", periodo_a, com, mercado, nivel, tipo)
        pb = self._periodo("b", periodo_b, com, mercado, nivel, tipo)
        ida, idb = pa["id_periodo_tarifario"], pb["id_periodo_tarifario"]

        horas_a = {r["hora"]: r for r in self.repo.get_precios_hora(ida)}
        horas_b = {r["hora"]: r for r in self.repo.get_precios_hora(idb)}

        monomias = {
            m["id_periodo_tarifario"]: a_float(m["valor"]) for m in self.repo.get_monomias([ida, idb])
        }
        componentes: Dict[int, Dict[str, float]] = defaultdict(dict)
        for c in self.repo.get_componentes([ida, idb]):
            componentes[c["id_periodo_tarifario"]][c["cod_componente"]] = a_float(c["valor"])

        advertencias: List[str] = []

        # --- Configuración horaria ---
        distinta = pa["id_configuracion_horaria"] != pb["id_configuracion_horaria"]
        if distinta:
            advertencias.append(
                f"La configuración horaria cambió ({pa['configuracion']} → {pb['configuracion']}): "
                "las franjas no son comparables entre los períodos; use la variación por hora "
                "y por tipo de hora."
            )

        for lado, horas in (("a", horas_a), ("b", horas_b)):
            if not horas:
                advertencias.append(f"El período_{lado} no tiene valores por franja (solo monomia).")
            elif len(horas) != 24:
                advertencias.append(f"El período_{lado} tiene precio en {len(horas)} de 24 horas.")

        # --- Variación por hora ---
        variacion_horas = []
        for hora in sorted(set(horas_a) | set(horas_b)):
            ra, rb = horas_a.get(hora), horas_b.get(hora)
            variacion_horas.append({
                "hora": hora,
                "codigo_franja_a": ra["codigo_franja"] if ra else None,
                "codigo_franja_b": rb["codigo_franja"] if rb else None,
                "tipo_hora_a": ra["tipo_hora"] if ra else None,
                "tipo_hora_b": rb["tipo_hora"] if rb else None,
                **variacion(a_float(ra["valor"]) if ra else None, a_float(rb["valor"]) if rb else None),
            })

        # --- Variación por tipo de hora (promedio ponderado por horas) ---
        variacion_tipo_hora = []
        for tipo_hora in TIPOS_HORA:
            va = [a_float(r["valor"]) for r in horas_a.values() if r["tipo_hora"] == tipo_hora]
            vb = [a_float(r["valor"]) for r in horas_b.values() if r["tipo_hora"] == tipo_hora]
            if not va and not vb:
                continue
            variacion_tipo_hora.append({
                "tipo_hora": tipo_hora,
                "horas_a": len(va),
                "horas_b": len(vb),
                **variacion(promedio(va), promedio(vb)),
            })

        # --- Variación por componente del CU ---
        ca, cb = componentes.get(ida, {}), componentes.get(idb, {})
        variacion_componentes = [
            {"cod_componente": cod, **variacion(ca.get(cod), cb.get(cod))}
            for cod in sorted(set(ca) | set(cb))
        ]

        # --- Totales ---
        prom_a = promedio(a_float(r["valor"]) for r in horas_a.values())
        prom_b = promedio(a_float(r["valor"]) for r in horas_b.values())
        mono_a, mono_b = monomias.get(ida), monomias.get(idb)

        logger.info(
            f"Comparación {mercado} {nivel} {tipo}: {periodo_a} vs {periodo_b} "
            f"(configuración distinta: {distinta})"
        )

        return {
            "cod_comercializadora": com,
            "mercado": mercado,
            "nivel": nivel,
            "tipo_tarifa": tipo,
            "periodo_a": {"anio": pa["anio"], "mes": pa["mes"], "numero_version": pa["numero_version"]},
            "periodo_b": {"anio": pb["anio"], "mes": pb["mes"], "numero_version": pb["numero_version"]},
            "configuracion_a": pa["configuracion"],
            "configuracion_b": pb["configuracion"],
            "configuracion_distinta": distinta,
            "unidad": "COP/kWh",
            "precio_promedio_a": redondear(prom_a),
            "precio_promedio_b": redondear(prom_b),
            "variacion_total": porcentaje(prom_a, prom_b),
            "variacion_monomia": variacion(mono_a, mono_b) if mono_a is not None and mono_b is not None else None,
            "variacion_horas": variacion_horas,
            "variacion_tipo_hora": variacion_tipo_hora,
            "variacion_componentes": variacion_componentes,
            "advertencias": advertencias,
        }

    # -----------------------------------------------------
    def _periodo(
        self, lado: str, periodo: Periodo, com: Optional[str], mercado: Optional[str],
        nivel: Optional[str], tipo: Optional[str],
    ) -> Dict[str, Any]:
        filas = self.repo.get_periodos_publicados(
            periodo[0], periodo[1],
            cod_comercializadora=com, cod_mercado=mercado, cod_nivel=nivel, cod_tipo_tarifa=tipo,
        )
        if not filas:
            raise PeriodoNoDisponibleError(lado, periodo[0], periodo[1])
        return filas[0]