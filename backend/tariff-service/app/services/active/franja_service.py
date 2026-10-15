# app/services/active/franja_service.py

from datetime import date, datetime
from typing import Optional, Dict, Any, List
from loguru import logger

from app.repositories.postgres.tarifa_repository import TarifaRepository


class FranjaService:
    """
    Lógica de negocio para franjas horarias y precios.
    
    Responsabilidades:
        - Obtener la curva de precios de las 24 horas
        - Resolver la franja para una hora específica
        - Determinar la franja actual del sistema
    """
    
    def __init__(self, repo: TarifaRepository):
        self.repo = repo
    
    # =====================================================
    # PRECIOS DEL DÍA
    # =====================================================
    
    def obtener_precios_dia(
        self,
        id_cliente: int,
        fecha: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Obtiene la curva de precios de las 24 horas del día.
        
        Returns:
            Dict con 'fecha', 'id_cliente' y lista de 'precios'
        """
        fecha_consulta = fecha or date.today()
        
        precios = self.repo.get_precios_dia(
            id_cliente=id_cliente,
            fecha=fecha_consulta
        )
        
        return {
            'id_cliente': id_cliente,
            'fecha': fecha_consulta,
            'precios': precios,
        }
    
    # =====================================================
    # FRANJA ACTUAL
    # =====================================================
    
    def obtener_franja_actual(
        self,
        id_cliente: int,
        hora: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene la franja horaria actual y su precio.
        
        Args:
            id_cliente: ID del cliente
            hora: hora específica (1-24). Si es None, usa la hora actual.
        
        Returns:
            Dict con la franja actual o None si no existe
        """
        hora_consulta = self._resolver_hora(hora)
        fecha_consulta = date.today()
        
        precio = self.repo.get_precio_por_hora(
            id_cliente=id_cliente,
            fecha=fecha_consulta,
            hora=hora_consulta
        )
        
        if not precio:
            logger.warning(
                f"Sin precio para cliente {id_cliente} "
                f"a las {hora_consulta}:00"
            )
            return None
        
        return {
            'id_cliente': id_cliente,
            'fecha': fecha_consulta,
            'hora_actual': hora_consulta,
            'codigo_franja': precio.get('codigo_franja'),
            'precio': precio.get('precio'),
            'unidad': precio.get('unidad'),
        }
    
    def _resolver_hora(self, hora: Optional[int]) -> int:
        """
        Resuelve la hora a consultar.
        
        Reglas:
            - Si hora es None, usa la hora actual.
            - Si la hora actual es 0 (medianoche), usa 24.
            - Hora 1 = 00:00-01:00, hora 24 = 23:00-24:00.
        """
        if hora is not None:
            return hora
        
        hora_actual = datetime.now().hour
        return hora_actual if hora_actual > 0 else 24