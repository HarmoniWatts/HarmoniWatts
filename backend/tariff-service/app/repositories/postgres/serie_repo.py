# repositories/serie_repo.py
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text



class SerieRepo:
    def __init__(self, db: Session):
        self.db = db
        self.engine = db.get_bind()   # Engine asociado a la Session

    def get_comp_series(self, mercado: str, nivel: str, tipo: str) -> pd.DataFrame:
        sql = """-- :mercado, :nivel, :tipo son parámetros
                WITH periodos AS (
                    SELECT pt.id_periodo_tarifario,
                        pt.anio, pt.mes,
                        make_date(pt.anio, pt.mes, 1) AS mes_ts,
                        pt.estado,
                        pt.numero_version,
                        pt.id_configuracion_horaria,
                        ch.codigo AS config,
                        ROW_NUMBER() OVER (
                            PARTITION BY pt.anio, pt.mes
                            ORDER BY (pt.estado = 'PUBLICADA') DESC, pt.numero_version DESC
                        ) AS rn
                    FROM periodo_tarifario pt
                    JOIN tarifa t ON t.id_tarifa = pt.id_tarifa
                    LEFT JOIN configuracion_horaria ch ON ch.id_configuracion_horaria = pt.id_configuracion_horaria
                    WHERE t.cod_mercado = :mercado
                    AND t.cod_nivel   = :nivel
                    AND t.cod_tipo_tarifa = :tipo
                    AND pt.estado IN ('PUBLICADA','BORRADOR','SUPERADA')  -- incluye estimadas BORRADOR
                ),
                elegido AS (
                    SELECT * FROM periodos WHERE rn = 1
                ),
                comp AS (
                    SELECT e.mes_ts, cv.cod_componente, cv.valor
                    FROM elegido e
                    JOIN componente_valor_mes cv ON cv.id_periodo_tarifario = e.id_periodo_tarifario
                ),
                monomia AS (
                    SELECT e.mes_ts, tv.valor AS monomia
                    FROM elegido e
                    JOIN tarifa_valor tv ON tv.id_periodo_tarifario = e.id_periodo_tarifario
                    WHERE tv.id_franja_horaria IS NULL   -- monomia (sin franja)
                )
                SELECT
                    e.mes_ts,
                    MAX(CASE WHEN c.cod_componente = 'Gm'   THEN c.valor END) AS "Gm",
                    MAX(CASE WHEN c.cod_componente = 'Tm'   THEN c.valor END) AS "Tm",
                    MAX(CASE WHEN c.cod_componente = 'Dm'   THEN c.valor END) AS "Dm",
                    MAX(CASE WHEN c.cod_componente = 'Cm'   THEN c.valor END) AS "Cm",
                    MAX(CASE WHEN c.cod_componente = 'PRm'  THEN c.valor END) AS "PRm",
                    MAX(CASE WHEN c.cod_componente = 'Rm'   THEN c.valor END) AS "Rm",
                    MAX(CASE WHEN c.cod_componente = 'Cfmj' THEN c.valor END) AS "Cfmj",
                    m.monomia,
                    e.config
                FROM elegido e
                LEFT JOIN comp c     ON c.mes_ts = e.mes_ts
                LEFT JOIN monomia m  ON m.mes_ts = e.mes_ts
                GROUP BY e.mes_ts, m.monomia, e.config
                ORDER BY e.mes_ts;""" 
                
        df = pd.read_sql(text(sql), self.engine, params={
            "mercado": mercado, "nivel": nivel, "tipo": tipo,
        })
        if df.empty:
            return df
        df["mes_ts"] = pd.to_datetime(df["mes_ts"])
        df = df.set_index("mes_ts").sort_index()
        # asegurar dtypes float
        for c in ["Gm","Tm","Dm","Cm","PRm","Rm","Cfmj","monomia"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        return df
    
    def get_combinaciones(self, comercializadora_cod: str, min_train: int = 8) -> list[tuple[str, str, str]]:
            sql = """SELECT t.cod_mercado, t.cod_nivel, t.cod_tipo_tarifa
                    FROM tarifa t
                    JOIN periodo_tarifario pt ON pt.id_tarifa = t.id_tarifa
                        WHERE t.cod_comercializadora = :comercializadora_cod
                        AND t.activa = TRUE
                        AND pt.estado IN ('PUBLICADA','BORRADOR','SUPERADA')
                    GROUP BY t.cod_mercado, t.cod_nivel, t.cod_tipo_tarifa
                    HAVING COUNT(DISTINCT make_date(pt.anio, pt.mes, 1)) >= :min_train
                    ORDER BY t.cod_mercado, t.cod_nivel, t.cod_tipo_tarifa;"""  

            rows = self.db.execute(text(sql), {
                "comercializadora_cod": comercializadora_cod,
                "min_train": min_train,
            }).fetchall()
            return [(r[0], r[1], r[2]) for r in rows]