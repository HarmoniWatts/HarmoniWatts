from typing import List, Dict, Any, Tuple
from datetime import date
from loguru import logger
import calendar

class DataValidator:
    """Valida los datos extraídos del PDF"""
    
    def validar(
        self, 
        tarifa: Dict[str, Any],
        anio: int,
        mes: int
    ) -> Tuple[bool, List[str]]:
        """Valida una tarifa extraída"""
        errores = []
        
        # 1. Validar campos obligatorios
        if not tarifa.get('mercado'):
            errores.append("Campo 'mercado' faltante")
        
        if not tarifa.get('nivel_tension'):
            errores.append("Campo 'nivel_tension' faltante")
        
        # 2. Validar franjas horarias
        franjas = tarifa.get('valores_franja', {})
        valores_validos = [v for v in franjas.values() if v is not None]
        
        if len(valores_validos) == 0:
            errores.append("No hay valores de franja válidos")
        
        # 3. Validar que los valores sean positivos
        for codigo, valor in franjas.items():
            if valor is not None and valor < 0:
                errores.append(f"Franja {codigo} tiene valor negativo: {valor}")
        
        # 4. Validar fechas
        try:
            fecha_inicio = date(anio, mes, 1)
            ultimo_dia = calendar.monthrange(anio, mes)[1]
            fecha_fin = date(anio, mes, ultimo_dia)
            tarifa['fecha_inicio'] = fecha_inicio
            tarifa['fecha_fin'] = fecha_fin
        except ValueError:
            errores.append(f"Fecha inválida: {anio}-{mes}")
        
        # 5. Validar componentes
        cu_base = tarifa.get('cu_base')
        cu_aplicado = tarifa.get('cu_aplicado')
        
        if cu_base and cu_aplicado:
            if cu_aplicado > cu_base:
                logger.warning(f"CU_Aplicado > CU_Base: {cu_aplicado} > {cu_base}")
        
        es_valido = len(errores) == 0
        return es_valido, errores