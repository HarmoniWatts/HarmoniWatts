# app/services/active/franja_service.py

from datetime import date, datetime
from typing import Optional, Dict, Any, List
from loguru import logger

from app.repositories.postgres.tarifa_repository import TarifaRepository
from app.repositories.postgres.cliente_repository import ClienteRepository
from app.services.business.tarifa_selector import TarifaSelector


class FranjaService:
    """
    Lógica de negocio para franjas horarias y precios.
    
    Responsabilidades:
        - Obtener la curva de precios de las 24 horas
        - Resolver la franja para una hora específica
        - Determinar la franja actual del sistema
    """
    
    def __init__(
        self,
        repo: TarifaRepository,
        cliente_repo: Optional[ClienteRepository] = None,
        selector: Optional[TarifaSelector] = None
    ):
        self.repo = repo
        self.cliente_repo = cliente_repo
        self.selector = selector
    
    # =====================================================
    # PRECIOS DEL DÍA
    # =====================================================
    
    def obtener_precios_dia(
        self,
        id_cliente: int,
        fecha: Optional[date] = None,
        consumo_mensual_kwh: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Obtiene la curva de precios de las 24 horas del día.
        
        Returns:
            Dict con 'fecha', 'id_cliente' y lista de 'precios'
        """
        fecha_consulta = fecha or date.today()
        
        precios = self.repo.get_precios_dia(
            id_cliente=id_cliente,
            fecha=fecha_consulta,
            cod_tipo_tarifa=self._tipo_tarifa(id_cliente, consumo_mensual_kwh)
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
        hora: Optional[int] = None,
        consumo_mensual_kwh: Optional[float] = None
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
            hora=hora_consulta,
            cod_tipo_tarifa=self._tipo_tarifa(id_cliente, consumo_mensual_kwh)
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
    
    def _tipo_tarifa(
        self,
        id_cliente: int,
        consumo_mensual_kwh: Optional[float]
    ) -> Optional[str]:
        """
        Tipo de tarifa (A, B, C, D) del cliente según TarifaSelector.
        None si no hay selector o el cliente no existe (el repositorio
        usa entonces su criterio por defecto).
        """
        if not (self.cliente_repo and self.selector):
            return None
        cliente = self.cliente_repo.get_by_id(id_cliente)
        if cliente is None:
            return None
        return self.selector.seleccionar_tipo_tarifa(
            cliente, consumo_mensual_kwh=consumo_mensual_kwh
        )
    
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