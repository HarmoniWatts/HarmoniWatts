# repositories/franja_repo.py
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text



class FranjaRepo:
    def __init__(self, db: Session):
        self.db = db
        self.engine = db.get_bind()   # Engine asociado a la Session
        
    
    def get_franjas(self, mercado: str, nivel: str, tipo: str) -> pd.DataFrame:
        sql = """WITH periodos AS (
                    SELECT pt.id_periodo_tarifario,
                        make_date(pt.anio, pt.mes, 1) AS mes_ts,
                        pt.estado, pt.numero_version,
                        ROW_NUMBER() OVER (
                            PARTITION BY pt.anio, pt.mes
                            ORDER BY (pt.estado = 'PUBLICADA') DESC, pt.numero_version DESC
                        ) AS rn
                    FROM periodo_tarifario pt
                    JOIN tarifa t ON t.id_tarifa = pt.id_tarifa
                    WHERE t.cod_mercado = :mercado
                    AND t.cod_nivel   = :nivel
                    AND t.cod_tipo_tarifa = :tipo
                    AND pt.estado IN ('PUBLICADA','BORRADOR','SUPERADA')
                ),
                elegido AS (
                    SELECT * FROM periodos WHERE rn = 1
                )
                SELECT e.mes_ts, fh.codigo AS franja, tv.valor
                FROM elegido e
                JOIN tarifa_valor tv       ON tv.id_periodo_tarifario = e.id_periodo_tarifario
                JOIN franja_horaria fh     ON fh.id_franja_horaria = tv.id_franja_horaria
                WHERE tv.id_franja_horaria IS NOT NULL
                ORDER BY e.mes_ts, fh.codigo;"""
        
        
        df = pd.read_sql(text(sql), self.engine, params={
            "mercado": mercado, "nivel": nivel, "tipo": tipo,
        })
        if df.empty:
            return df
        df["mes_ts"] = pd.to_datetime(df["mes_ts"])
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        
        return df.set_index("mes_ts").sort_index()