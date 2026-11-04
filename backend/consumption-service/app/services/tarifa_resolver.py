from datetime import datetime
from typing import Optional, Dict, List
from loguru import logger

from app.services.ports import TarifaResolverPort


class TarifaResolverHTTP(TarifaResolverPort):
    """
    Implementación que consulta el tariff-service para obtener la tarifa
    aplicada a un timestamp concreto.
    
    Envuelve la respuesta del endpoint:
        GET /api/v1/tariff/active/current/{id_cliente}?fecha=YYYY-MM-DD
    """
    
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
    
    async def resolver(
        self,
        id_cliente: int,
        timestamp: datetime,
        consumo_mensual: float
    ) -> Optional[Dict]:
        """
        Consulta el tariff-service y extrae la tarifa aplicada para el
        timestamp dado, calculando el precio de la hora correspondiente.
        """
        from app.core.http_client import HTTPClientManager
        
        try:
            client = await HTTPClientManager.get_client()
            
            fecha_str = timestamp.strftime("%Y-%m-%d")
            hora = timestamp.hour if timestamp.hour > 0 else 24
            
            # 1. Obtener tarifa completa
            response = await client.get(
                f"{self.base_url}/api/v1/tariff/active/current/{id_cliente}",
                params={"fecha": fecha_str, "consumo_mensual_kwh": consumo_mensual},
                timeout=self.timeout,
            )
            
            if response.status_code == 404:
                logger.warning(
                    f"Sin tarifa vigente para cliente {id_cliente} "
                    f"en {fecha_str}"
                )
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # 2. Extraer precio de la hora
            return self._extraer_tarifa_aplicada(data, hora)
            
        except Exception as e:
            logger.error(f"Error consultando tariff-service: {e}")
            logger.error(f"{self.base_url}/api/v1/tariff/active/current/{id_cliente}")
            return None
    
    def _extraer_tarifa_aplicada(
        self,
        tarifa_data: Dict,
        hora: int,
    ) -> Optional[Dict]:
        """
        Extrae la tarifa aplicada para una hora específica desde la
        respuesta del tariff-service.
        """
        tarifa = tarifa_data.get("tarifa", {})
        periodo = tarifa_data.get("periodo", {})
        configuracion_horaria = tarifa_data.get("cod_configuracion_horaria")
        modo = tarifa_data.get("modo_tarifa", "SIN_VALORES")
        monomia = tarifa_data.get("monomia")
        valores = tarifa_data.get("valores", [])
        
        # Buscar la franja de la hora
        franja = next(
            (v for v in valores if v.get("hora") == hora),
            None,
        )
        
        precio_franja = franja.get("valor", 0.0) if franja else 0.0
        precio_monomia = monomia.get("valor", 0.0) if monomia else 0.0
        
        return {
            "id_tarifa": tarifa.get("id_tarifa"),
            "cod_tipo_tarifa": tarifa.get("cod_tipo_tarifa"),
            "periodo": periodo.get("id_periodo_tarifario"),
            "configuracion_horaria": configuracion_horaria, 
            "franja_aplicada": franja.get("codigo_franja") if franja else None,
            "tipo_hora": franja.get("tipo_hora") if franja else None,
            "modo": "MONOMIA" if modo == "MONOMIA" else "TOU",
            "precio_franja": float(precio_franja),
            "precio_monomia": float(precio_monomia),
            "alternativas": [],   # TODO: si el servicio las expone
        }


class TarifaResolverMock(TarifaResolverPort):
    """
    Implementación mock con precios fijos.
    Útil como fallback cuando el tariff-service no está disponible.
    """
    
    # Precios por tipo de hora (COP/kWh)
    PRECIOS = {
        "VALLE": 854.38,
        "MEDIA": 867.81,
        "PICO": 877.99,
    }
    
    async def resolver(
        self,
        id_cliente: int,
        timestamp: datetime,
        consumo_mensual: Optional[float] = None,
    ) -> Optional[Dict]:
        hora = timestamp.hour if timestamp.hour > 0 else 24
        tipo_hora = self._tipo_hora(hora)
        
        return {
            "id_tarifa": 0,
            "cod_tipo_tarifa": "MOCK",
            "periodo": 0,
            "configuracion_horaria": "CH00",
            "franja_aplicada": "F1",
            "tipo_hora": tipo_hora,
            "modo": "TOU",
            "precio_franja": self.PRECIOS[tipo_hora],
            "precio_monomia": 0.0,
            "alternativas": [],
        }
    
    def _tipo_hora(self, hora: int) -> str:
        if 1 <= hora <= 6 or hora == 24:
            return "VALLE"
        if 19 <= hora <= 22:
            return "PICO"
        return "MEDIA"