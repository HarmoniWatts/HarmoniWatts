# app/services/active/tarifa_service.py

from datetime import date
from email.policy import default
from typing import Optional, Dict, Any
from loguru import logger
from matplotlib.dates import relativedelta

from app.repositories.postgres.tarifa_repository import TarifaRepository
from app.repositories.postgres.cliente_repository import ClienteRepository
from app.services.business.tarifa_selector import TarifaSelector


class TarifaActivaService:
    """
    Lógica de negocio para tarifas activas.
    
    Responsabilidades:
        - Obtener la tarifa vigente de un cliente
        - Validar que exista tarifa para la fecha
        - Formatear la respuesta para la API
    """
    
    def __init__(self, repo: TarifaRepository, cliente_repo: ClienteRepository, selector: TarifaSelector):
        self.repo = repo
        self.cliente_repo = cliente_repo
        self.selector = selector
        

    def obtener_tarifa_vigente(
        self,
        id_cliente: int,
        fecha: Optional[date] = None,
        consumo_mensual_kwh: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        
        MAX_MESES_ATRAS = 6
        
        fecha_consulta = fecha or date.today()
        cliente = self.cliente_repo.get_by_id(id_cliente)
        cod_tipo_tarifa = self.selector.seleccionar_tipo_tarifa(
            cliente, consumo_mensual_kwh=consumo_mensual_kwh
        )

        # --- Nivel 1: PUBLICADA del mes ---
        tarifa_data = self.repo.get_tarifa_vigente_completa(
            id_cliente=id_cliente,
            fecha=fecha_consulta,
            cod_tipo_tarifa=cod_tipo_tarifa,
        )
        if tarifa_data:
            return self._formatear_respuesta(
                tarifa_data, fecha_consulta,
                es_estimado=False, es_fallback=False,
                meses_desfase=0, estado_periodo="PUBLICADA",
            )

        # --- Nivel 2: ESTIMADA del mes ---
        tarifa_est = self.repo.get_tarifa_estimada_completa(
            id_cliente=id_cliente,
            fecha=fecha_consulta,
            cod_tipo_tarifa=cod_tipo_tarifa,
        )
        if tarifa_est:
            logger.info(
                "Usando tarifa ESTIMADA para cliente %s en %s-%02d",
                id_cliente, fecha_consulta.year, fecha_consulta.month,
            )
            return self._formatear_respuesta(
                tarifa_est, fecha_consulta,
                es_estimado=True, es_fallback=False,
                meses_desfase=0, estado_periodo="BORRADOR_ESTIMADA",
            )

        # --- Nivel 3: PUBLICADA de meses anteriores ---
        fecha_busqueda = fecha_consulta - relativedelta(months=1)
        for intento in range(1, MAX_MESES_ATRAS + 1):
            tarifa_data = self.repo.get_tarifa_vigente_completa(
                id_cliente=id_cliente,
                fecha=fecha_busqueda,
                cod_tipo_tarifa=cod_tipo_tarifa,
            )
            if tarifa_data:
                logger.warning(
                    "Usando tarifa PUBLICADA obsoleta (hace %d meses) para cliente %s",
                    intento, id_cliente,
                )
                return self._formatear_respuesta(
                    tarifa_data, fecha_busqueda,
                    es_estimado=False, es_fallback=True,
                    meses_desfase=intento, estado_periodo="PUBLICADA",
                )
            fecha_busqueda = fecha_busqueda - relativedelta(months=1)

        # --- Nivel 4: nada ---
        logger.warning(
            "Sin tarifa para cliente %s en %s (ni estimada ni publicada en %d meses)",
            id_cliente, fecha_consulta, MAX_MESES_ATRAS,
        )
        return None
        
    
    
    def _formatear_respuesta(
        self,
        tarifa_data: Dict[str, Any],
        fecha: date,
        *,
        es_estimado: bool = False,
        es_fallback: bool = False,
        meses_desfase: int = 0,
        estado_periodo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Formatea la respuesta de la tarifa.
        Los kwargs son opcionales: las llamadas antiguas (`_formatear_respuesta(data, fecha)`)
        siguen funcionando y devuelven es_estimado=False, es_fallback=False, meses_desfase=0.
        """
        tarifa = tarifa_data["tarifa"]
        periodo = tarifa_data["periodo"]
        valores = tarifa_data["valores"]
        componentes = tarifa_data["componentes"]

        # Si no se pasa estado_periodo, se deriva del periodo
        if estado_periodo is None:
            estado_periodo = periodo.estado

        return {
            "id_cliente": tarifa_data.get("id_cliente"),
            "fecha_consulta": fecha,
            # --- metadatos de estimación ---
            "es_estimado": es_estimado,
            "es_fallback": es_fallback,
            "meses_desfase": meses_desfase,
            "estado_periodo": estado_periodo,
            # --- tarifa ---
            "tarifa": {
                "id_tarifa": tarifa.id_tarifa,
                "codigo_tarifa": tarifa.codigo_tarifa,
                "nombre_tarifa": tarifa.nombre_tarifa,
                "cod_comercializadora": tarifa.cod_comercializadora,
                "cod_mercado": tarifa.cod_mercado,
                "cod_nivel": tarifa.cod_nivel,
                "cod_tipo_tarifa": tarifa.cod_tipo_tarifa,
                "resolucion_regulatoria": tarifa.resolucion_regulatoria,
            },
            "periodo": {
                "id_periodo_tarifario": periodo.id_periodo_tarifario,
                "anio": periodo.anio,
                "mes": periodo.mes,
                "fecha_inicio": periodo.fecha_inicio,
                "fecha_fin": periodo.fecha_fin,
                "numero_version": periodo.numero_version,
                "estado": periodo.estado,
                "fecha_publicacion": periodo.fecha_publicacion,
            },
            "cod_configuracion_horaria": tarifa_data.get("cod_configuracion_horaria"),
            "monomia": tarifa_data.get("monomia"),
            "valores": [
                {
                    "hora": self._get_field(v, "hora"),
                    "codigo_franja": (
                        self._get_field(v, "codigo_franja")
                        or self._get_field(v, "franja")
                    ),
                    "tipo_hora": self._get_field(v, "tipo_hora"),
                    "valor": float(self._get_field(v, "valor", 0)),
                    "unidad": self._get_field(v, "unidad") or "COP/kWh",
                }
                for v in valores
            ],
            "componentes": [
                {
                    "cod_componente": c.cod_componente,
                    "valor": float(c.valor) if hasattr(c, "valor") else None,
                }
                for c in componentes
            ],
        }
    
    def _get_field(self, obj, key: str, default=None):
        """
        Obtiene un campo de un objeto o dict.
        Maneja dicts, Row de SQLAlchemy y objetos ORM.
        """
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)