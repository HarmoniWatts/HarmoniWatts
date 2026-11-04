# app/repositories/postgres/tarifa_historica_repository.py

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

Periodo = Tuple[int, int]  # (anio, mes)


class TarifaHistoricaRepository:
    """
    Consultas de solo lectura para los endpoints históricos.

    Trabaja sobre las vistas (ver sql/historical_views_indexes.sql):
        - v_periodo_publicado:     1 fila por período PUBLICADA
        - v_tarifa_publicada_hora: 1 fila por hora (1..24) de cada período PUBLICADA

    Devuelve listas de dicts (no objetos ORM) y no modifica datos.
    """

    def __init__(self, db: Session):
        self.db = db

    # =====================================================
    # Utilidades internas
    # =====================================================

    def _filas(self, stmt, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return [dict(r) for r in self.db.execute(stmt, params or {}).mappings().all()]

    @staticmethod
    def _filtros_tarifa(
        cod_comercializadora: Optional[str] = None,
        cod_mercado: Optional[str] = None,
        cod_nivel: Optional[str] = None,
        cod_tipo_tarifa: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Construye las condiciones opcionales por tarifa. Solo agrega las que llegan con valor
        (así se evita `:param IS NULL`, que algunos drivers no pueden tipar).
        Los nombres de columna son constantes; los valores siempre van como parámetros.
        """
        condiciones = ""
        params: Dict[str, Any] = {}
        for columna, clave, valor in (
            ("cod_comercializadora", "com", cod_comercializadora),
            ("cod_mercado", "mercado", cod_mercado),
            ("cod_nivel", "nivel", cod_nivel),
            ("cod_tipo_tarifa", "tipo", cod_tipo_tarifa),
        ):
            if valor:
                condiciones += f" AND {columna} = :{clave}"
                params[clave] = valor
        return condiciones, params

    # =====================================================
    # Períodos publicados
    # =====================================================

    def get_periodos_publicados(
        self,
        anio: int,
        mes: int,
        cod_comercializadora: Optional[str] = None,
        cod_mercado: Optional[str] = None,
        cod_nivel: Optional[str] = None,
        cod_tipo_tarifa: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Períodos PUBLICADA de un mes, con filtros opcionales por tarifa."""
        extra, params = self._filtros_tarifa(
            cod_comercializadora, cod_mercado, cod_nivel, cod_tipo_tarifa
        )
        params.update({"anio": anio, "mes": mes})
        sql = f"""
            SELECT id_periodo_tarifario, id_tarifa, codigo_tarifa, nombre_tarifa,
                   cod_comercializadora, cod_mercado, cod_nivel, cod_tipo_tarifa,
                   resolucion_regulatoria, anio, mes, fecha_inicio, fecha_fin,
                   numero_version, fecha_publicacion, id_configuracion_horaria, configuracion
            FROM v_periodo_publicado
            WHERE anio = :anio AND mes = :mes{extra}
            ORDER BY cod_mercado, cod_nivel, cod_tipo_tarifa
        """
        return self._filas(text(sql), params)

    def get_ultimo_periodo(
        self,
        cod_comercializadora: str,
        cod_mercado: str,
        cod_nivel: str,
        cod_tipo_tarifa: str,
    ) -> Optional[Dict[str, Any]]:
        """Último mes con tarifa PUBLICADA para una combinación (None si no hay)."""
        extra, params = self._filtros_tarifa(
            cod_comercializadora, cod_mercado, cod_nivel, cod_tipo_tarifa
        )
        sql = f"""
            SELECT anio, mes
            FROM v_periodo_publicado
            WHERE TRUE{extra}
            ORDER BY anio DESC, mes DESC
            LIMIT 1
        """
        filas = self._filas(text(sql), params)
        return filas[0] if filas else None

    # =====================================================
    # Valores y componentes (varios períodos a la vez)
    # =====================================================

    def get_valores_franja(self, ids_periodo: List[int]) -> List[Dict[str, Any]]:
        """Valor por franja de cada período, con las horas que cubre la franja."""
        if not ids_periodo:
            return []
        stmt = text("""
            SELECT id_periodo_tarifario, codigo_franja, tipo_hora, valor, unidad,
                   array_agg(hora ORDER BY hora) AS horas
            FROM v_tarifa_publicada_hora
            WHERE id_periodo_tarifario IN :ids
            GROUP BY id_periodo_tarifario, codigo_franja, tipo_hora, valor, unidad
            ORDER BY id_periodo_tarifario, codigo_franja
        """).bindparams(bindparam("ids", expanding=True))
        return self._filas(stmt, {"ids": list(ids_periodo)})

    def get_monomias(self, ids_periodo: List[int]) -> List[Dict[str, Any]]:
        """Valor de monomia (fila de tarifa_valor sin franja) de cada período."""
        if not ids_periodo:
            return []
        stmt = text("""
            SELECT id_periodo_tarifario, valor, unidad
            FROM tarifa_valor
            WHERE id_periodo_tarifario IN :ids
              AND id_franja_horaria IS NULL
        """).bindparams(bindparam("ids", expanding=True))
        return self._filas(stmt, {"ids": list(ids_periodo)})

    def get_componentes(self, ids_periodo: List[int]) -> List[Dict[str, Any]]:
        """Componentes del CU (Gm, Tm, Dm, ...) de cada período."""
        if not ids_periodo:
            return []
        stmt = text("""
            SELECT id_periodo_tarifario, cod_componente, valor
            FROM componente_valor_mes
            WHERE id_periodo_tarifario IN :ids
            ORDER BY id_periodo_tarifario, cod_componente
        """).bindparams(bindparam("ids", expanding=True))
        return self._filas(stmt, {"ids": list(ids_periodo)})

    # =====================================================
    # Precios por hora (tendencias y comparación)
    # =====================================================

    def get_precios_hora(self, id_periodo_tarifario: int) -> List[Dict[str, Any]]:
        """Precio de cada hora (1..24) de un período."""
        sql = """
            SELECT hora, codigo_franja, tipo_hora, valor, unidad
            FROM v_tarifa_publicada_hora
            WHERE id_periodo_tarifario = :id
            ORDER BY hora
        """
        return self._filas(text(sql), {"id": id_periodo_tarifario})

    def get_serie_mensual(
        self,
        cod_comercializadora: str,
        cod_mercado: str,
        cod_nivel: str,
        cod_tipo_tarifa: str,
        desde: Periodo,
        hasta: Periodo,
    ) -> List[Dict[str, Any]]:
        """
        Agregados mensuales de una combinación entre `desde` y `hasta` (ambos incluidos).

        precio_promedio = promedio de las horas con precio (ponderado por horas, no por franjas).
        Solo devuelve los meses que tienen datos publicados.
        """
        extra, params = self._filtros_tarifa(
            cod_comercializadora, cod_mercado, cod_nivel, cod_tipo_tarifa
        )
        params.update({"a1": desde[0], "m1": desde[1], "a2": hasta[0], "m2": hasta[1]})
        sql = f"""
            SELECT anio, mes,
                   avg(valor)           AS precio_promedio,
                   min(valor)           AS precio_min,
                   max(valor)           AS precio_max,
                   count(*)             AS horas,
                   min(configuracion)   AS configuracion,
                   min(unidad)          AS unidad
            FROM v_tarifa_publicada_hora
            WHERE (anio, mes) >= (:a1, :m1)
              AND (anio, mes) <= (:a2, :m2){extra}
            GROUP BY anio, mes
            ORDER BY anio, mes
        """
        return self._filas(text(sql), params)