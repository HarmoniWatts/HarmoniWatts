from typing import Dict, Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from loguru import logger
import holidays


class MeterMapper:
    """
    Transforma los registros crudos de comercializador al documento MongoDB
    de la colección `consumos_enriquecidos`.
    """
    
    # Mapeo de tipos de hora comercializador → modelo
    # (si comercializador no lo provee, se calcula con la tarifa)
    
    
    def transformar(
        self,
        lectura_comercializador: Dict[str, Any],
        id_vivienda: Optional[int] = None,
        tarifa_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Transforma una lectura de comercializador al documento MongoDB.
        
        Args:
            lectura_comercializador: registro crudo de comercializador
            id_vivienda: ID de vivienda asociada (lookup en PostgreSQL)
            tarifa_data: tarifa vigente en el timestamp (del tariff-service)
        
        Returns:
            Documento MongoDB listo para upsert, o None si falla
        """
        try:
            # 1. Parsear timestamp
            timestamp = self._parse_timestamp(lectura_comercializador["DATE_TIME"])
            if not timestamp:
                logger.warning(
                    f"Timestamp inválido: {lectura_comercializador.get('DATE_TIME')}"
                )
                return None
            
            # 2. Construir documento base
            doc = {
                # Referencias
                "id_vivienda": id_vivienda,
                "id_medidor": lectura_comercializador["METER_NO"],
                # "rnum": lectura_comercializador.get("RNUM"),
                
                # Timestamp
                "timestamp": timestamp,
                
                # Lecturas de energía
                "lectura_acumulada_kwh": self._safe_float(lectura_comercializador.get("IMPORT_KWH")),
                "lectura_acumulada_mensual_kwh": self._safe_float(lectura_comercializador.get("IMPORT_KWH_MENSUAL")),
                "valor_kwh": self._safe_float(lectura_comercializador.get("LP_IMPORT_KWH")),
                "valor_kvarh": self._safe_float(lectura_comercializador.get("LP_IMPORT_KVARH")),
                "valor_export_kwh": self._safe_float(lectura_comercializador.get("LP_EXPORT_KWH")),
                "valor_export_kvarh": self._safe_float(lectura_comercializador.get("LP_EXPORT_KVARH")),
                
                # Fases (opcional)
                # "corriente_l1": self._safe_float(lectura_comercializador.get("CURRENT_L1")),
                # "corriente_l2": self._safe_float(lectura_comercializador.get("CURRENT_L2")),
                # "corriente_l3": self._safe_float(lectura_comercializador.get("CURRENT_L3")),
                # "voltaje_l1": self._safe_float(lectura_comercializador.get("VOLTAGE_L1")),
                # "voltaje_l2": self._safe_float(lectura_comercializador.get("VOLTAGE_L2")),
                # "voltaje_l3": self._safe_float(lectura_comercializador.get("VOLTAGE_L3")),
                
                # Metadata
                # "estado_facturacion": lectura_comercializador.get("BILLING_STATUS_2"),
                
                # Fuente
                "fuente": "api_externa",
                "calidad_dato": "real",
                "fecha_registro": datetime.utcnow().replace(tzinfo=ZoneInfo("America/Bogota")),
                "version_schema": "2.0",
            }
            
            # 3. Contexto temporal
            doc["contexto_temporal"] = self._contexto_temporal(timestamp)
            
            # 4. Tarifa aplicada (si se conoce)
            if tarifa_data:
                doc["tarifa_aplicada"] = self._construir_tarifa_aplicada(
                    tarifa_data, doc["valor_kwh"]
                )
                doc["tarifas_alternativas"] = tarifa_data.get("alternativas", [])
                
            else:
                doc["tarifa_aplicada"] = self._tarifa_aplicada_vacia()
                doc["tarifas_alternativas"] = []
            
            return doc
            
        except Exception as e:
            logger.error(f"Error transformando lectura: {e}")
            return None
    
    # =====================================================
    # HELPERS
    # =====================================================
    
    def _parse_timestamp(self, date_time_str: str) -> Optional[datetime]:
        """Parsea 'DD/MM/YYYY HH:mm:ss' → datetime."""
        if not date_time_str:
            return None
        try:
            return datetime.strptime(date_time_str, "%d/%m/%Y %H:%M:%S").replace(
                tzinfo=ZoneInfo("America/Bogota")
            )
        except ValueError:
            return None
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Convierte a float de forma segura."""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _contexto_temporal(self, timestamp: datetime) -> Dict[str, Any]:
        """Calcula el contexto temporal de un timestamp."""
            
        return {
            "dia_semana": timestamp.isoweekday(),   # 1=lunes, 7=domingo
            "es_festivo": self._es_festivo(timestamp),                     # TODO: calcular con calendario
            "hora_del_dia": timestamp.hour or 24,    # 1-24
            "mes": timestamp.month,
            "anio": timestamp.year,
            "estacion": self._estacion(timestamp.month),
        }
        
    def _es_festivo(self, timestamp: datetime) -> str:
        
        # 1. Configurar los festivos de Colombia para el año en curso
        festivos_co = holidays.Colombia(years=timestamp.year)
        es_festivo = False
        # 2. Extraer solo la fecha (.date()) para evaluar el festivo
        if timestamp.date() in festivos_co:
            es_festivo = True
        else:
            es_festivo = False
            
        return es_festivo
    
    def _estacion(self, mes: int) -> str:
        """Determina la estación del año (Colombia: solo seca/lluviosa)."""
        # Colombia no tiene 4 estaciones; ajustar según negocio
        if mes in (12, 1, 2, 3):
            return "verano"
        if mes in (6, 7, 8, 9):
            return "invierno"
        return "N.A"
    
    def _construir_tarifa_aplicada(
        self,
        tarifa_data: Dict[str, Any],
        valor_kwh: float,
    ) -> Dict[str, Any]:
        """Construye el objeto tarifa_aplicada."""
        precio_franja = tarifa_data.get("precio_franja", 0)
        precio_monomia = tarifa_data.get("precio_monomia", 0)
        
        return {
            "id_tarifa": tarifa_data.get("id_tarifa"),
            "cod_tipo_tarifa": tarifa_data.get("cod_tipo_tarifa"),
            "periodo": tarifa_data.get("periodo"),
            "configuracion_horaria": tarifa_data.get("configuracion_horaria"),
            "franja_aplicada": tarifa_data.get("franja_aplicada"),
            "tipo_hora": tarifa_data.get("tipo_hora"),
            "modo": tarifa_data.get("modo", "TOU"),
            "precio_kwh_franja": precio_franja,
            "precio_kwh_monomia": precio_monomia,
            "costo_total_franja": round(valor_kwh * precio_franja, 2),
            "costo_total_monomia": round(valor_kwh * precio_monomia, 2),
            "moneda": "COP",
        }
        
    def _tarifa_aplicada_vacia(
        self
    ) -> Dict[str, Any]:
        """Tarifa por defecto cuando no se pudo resolver."""
        return {
            "id_tarifa": 0,
            "cod_tipo_tarifa": "SIN_TARIFA",
            "periodo": 0,
            "configuracion_horaria": None,
            "franja_aplicada": None,
            "tipo_hora": None,
            "modo": "MONOMIA",
            "precio_kwh_franja": 0.0,
            "precio_kwh_monomia": 0.0,
            "costo_total_franja": 0.0,
            "costo_total_monomia": 0.0,
            "moneda": "COP",
        }