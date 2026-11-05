from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict


class ViviendaResolverPort(ABC):
    """
    Puerto para resolver la vivienda asociada a un medidor y gestionar
    la relación medidor ↔ vivienda.
    
    Responsabilidades:
        - Resolver meter_no → id_vivienda
        - Registrar asociaciones nuevas (cuando el usuario vincula)
        - Listar medidores activos (para sync masiva)
        - Reasignar lecturas huérfanas cuando se registra un medidor
    """
    
    # =====================================================
    # LECTURA
    # =====================================================
    
    @abstractmethod
    async def resolver(self, meter_no: str) -> Optional[int]:
        """
        Devuelve el id_vivienda asociado a un medidor, o None si no existe.
        
        Args:
            meter_no: número de medidor (ej. "MNFFF016E250")
        
        Returns:
            id_vivienda o None
        """
        pass
    
    @abstractmethod
    async def listar_medidores_activos(self) -> List[Dict]:
        """
        Lista todos los medidores activos con su vivienda asociada.
        
        Usado por la sincronización masiva para saber qué medidores consultar.
        
        Returns:
            Lista de dicts:
                [
                    {"meter_no": "MNFFF016E250", "id_vivienda": 4},
                    {"meter_no": "MNFFF016E251", "id_vivienda": 5},
                ]
        """
        pass
    
    @abstractmethod
    async def obtener_por_vivienda(self, id_vivienda: int) -> List[str]:
        """
        Devuelve los medidores asociados a una vivienda.
        
        Útil para:
            - Mostrar medidores al usuario en el dashboard
            - Sincronizar solo los medidores de una vivienda
            - Validar que un medidor pertenece a una vivienda
        
        Args:
            id_vivienda: ID de la vivienda
        
        Returns:
            Lista de meter_no
        """
        pass
    
    # =====================================================
    # ESCRITURA
    # =====================================================
    
    @abstractmethod
    async def registrar_asociacion(
        self,
        meter_no: str,
        id_vivienda: int,
    ) -> bool:
        """
        Registra la asociación meter_no → id_vivienda.
        
        Se llama cuando:
            - El usuario registra un medidor por primera vez
            - Se importa una lista de medidores desde la comercializadora
            - Se reasigna un medidor a otra vivienda
        
        Args:
            meter_no: número de medidor
            id_vivienda: ID de la vivienda a asociar
        
        Returns:
            True si se registró, False si falló
        """
        pass
    
    @abstractmethod
    async def reasignar_lecturas_huerfanas(
        self,
        meter_no: str,
        id_vivienda: int,
    ) -> int:
        """
        Reasigna las lecturas huérfanas (id_vivienda=null) a una vivienda.
        
        Se llama cuando:
            - Se registra un medidor que ya tenía lecturas en MongoDB
              pero sin vivienda asignada
        
        Args:
            meter_no: número de medidor
            id_vivienda: ID de la vivienda a asignar
        
        Returns:
            Número de documentos actualizados
        """
        pass

class TarifaResolverPort(ABC):
    """Puerto para resolver la tarifa aplicada a un timestamp."""
    
    @abstractmethod
    async def resolver(
        self,
        id_cliente: int,
        timestamp: datetime,
    ) -> Optional[dict]:
        """
        Devuelve un dict con la tarifa aplicada:
            {
                'id_tarifa': int,
                'cod_tipo_tarifa': str,
                'periodo': int,
                'configuracion_horaria': str,
                'franja_aplicada': str,
                'tipo_hora': str,          # VALLE, MEDIA, PICO
                'modo': str,               # TOU, RTP, MONOMIA
                'precio_franja': float,
                'precio_monomia': float,
                'alternativas': list,
            }
        o None si no se puede resolver.
        """
        pass