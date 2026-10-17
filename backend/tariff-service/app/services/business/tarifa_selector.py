# app/services/business/tarifa_selector.py

from decimal import Decimal
from typing import Optional


class TarifaSelector:
    """Determina el tipo de tarifa (A, B, C, D) según reglas CREG 119/2007."""
    
    TIPOS_NO_RESIDENCIALES = {'I', 'C', 'O', 'E'}
    
    def seleccionar_tipo_tarifa(
        self,
        cliente,
        consumo_mensual_kwh: Optional[Decimal] = None
    ) -> str:
        """Determina el código del tipo de tarifa."""
        if cliente.cod_tipo_cliente in self.TIPOS_NO_RESIDENCIALES:
            return 'A'
        
        estrato = cliente.estrato
        if estrato in (4, 5, 6):
            return 'A'
        
        cs_kwh = cliente.cs_kwh_mes
        if cs_kwh is None:
            return 'A'
        
        consumo = consumo_mensual_kwh or cs_kwh
        
        if consumo > cs_kwh:
            return 'A'
        
        return {1: 'D', 2: 'C', 3: 'B'}.get(estrato, 'A')