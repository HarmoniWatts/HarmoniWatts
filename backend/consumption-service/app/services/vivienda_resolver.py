from typing import Optional, Dict, List
from loguru import logger

from app.services.ports import ViviendaResolverPort


class ViviendaResolverMock(ViviendaResolverPort):
    """
    Implementación mock de ViviendaResolver.
    
    Útil mientras no hay acceso al user-service.
    Usa un diccionario estático en memoria o una variable de entorno.
    """
    
    # Diccionario estático meter_no → id_vivienda
    DEFAULT_MAP: Dict[str, int] = {
        "MNDD305C0D60": 1,
        "MN233D2ED722": 2,
        "MN9E60ABC91C": 3,
        "MNC391C85C85": 4,
        "MN1860D3B3B7": 5,
        "MNE5D6840091": 6,
        "MND9A83DC2D2": 7,
        "MN809B65A6F1": 8,
        "MN157A243DFE": 9
    }
    
    def __init__(self, mapping: Optional[Dict[str, int]] = None):
        self.mapping = mapping or self.DEFAULT_MAP
        logger.info(f"ViviendaResolverMock inicializado con {len(self.mapping)} medidores")
    
    async def resolver(self, meter_no: str) -> Optional[int]:
        id_vivienda = self.mapping.get(meter_no)
        
        if id_vivienda is None:
            logger.warning(
                f"[MOCK] Medidor {meter_no} no encontrado en el mapa estático"
            )
            return None
        
        logger.debug(f"[MOCK] {meter_no} → vivienda {id_vivienda}")
        return id_vivienda
    
    async def listar_medidores_activos(self) -> List[Dict]:
        return [
            {"meter_no": meter_no, "id_vivienda": id_vivienda}
            for meter_no, id_vivienda in self.mapping.items()
        ]
    
    async def obtener_por_vivienda(self, id_vivienda: int) -> List[str]:
        return [
            meter_no
            for meter_no, vivienda in self.mapping.items()
            if vivienda == id_vivienda
        ]
    
    async def registrar_asociacion(
        self,
        meter_no: str,
        id_vivienda: int,
    ) -> bool:
        # En el mock, solo actualiza el dict en memoria
        self.mapping[meter_no] = id_vivienda
        logger.info(f"[MOCK] Asociación registrada: {meter_no} → {id_vivienda}")
        return True
    
    async def reasignar_lecturas_huerfanas(
        self,
        meter_no: str,
        id_vivienda: int,
    ) -> int:
        # En el mock, no hay MongoDB real que actualizar
        logger.warning(
            f"[MOCK] reasignar_lecturas_huerfanas({meter_no}, {id_vivienda}): "
            f"no implementado en mock"
        )
        return 0


class ViviendaResolverHTTP(ViviendaResolverPort):
    """
    Implementación real de ViviendaResolver consultando el user-service.
    
    TODO: Activar cuando el user-service esté disponible.
    """
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def resolver(self, meter_no: str) -> Optional[int]:
        """
        GET {user_service}/api/v1/dispositivos/por-medidor/{meter_no}
        
        Respuesta esperada:
            {"id_vivienda": 4, "id_dispositivo": 123}
        """
        # from app.core.http_client import HTTPClientManager
        # client = await HTTPClientManager.get_client()
        # response = await client.get(
        #     f"{self.base_url}/api/v1/dispositivos/por-medidor/{meter_no}"
        # )
        # if response.status_code == 404:
        #     return None
        # response.raise_for_status()
        # return response.json()["id_vivienda"]
        
        logger.warning("ViviendaResolverHTTP.resolver: no implementado todavía")
        return None