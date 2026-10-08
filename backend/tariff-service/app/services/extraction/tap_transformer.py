from typing import Dict, Any, List
from datetime import date
from loguru import logger

class TAPTransformer:
    """
    Transforma los datos extraídos del PDF al modelo TAP 
    (6 grupos + bloques)
    """
    
    COMPONENTES_TAP = ['G', 'T', 'D', 'CV', 'PR', 'R']
    
    def transformar(
        self, 
        tarifa_extraida: Dict[str, Any],
        comercializadora_id: int
    ) -> Dict[str, Any]:
        """Transforma una tarifa extraída al modelo TAP"""
        
        # Generar código único
        codigo = self._generar_codigo(tarifa_extraida)
        
        # Estructura TAP
        tarifa_tap = {
            'id_comercializadora': comercializadora_id,
            'mercado': tarifa_extraida['mercado'],
            'nivel_tension': tarifa_extraida['nivel_tension'],
            'tipo_tarifa': tarifa_extraida.get('tipo_tarifa'),
            'codigo_tarifa': codigo,
            'nombre_tarifa': self._generar_nombre(tarifa_extraida),
            'fecha_inicio': tarifa_extraida['fecha_inicio'],
            'fecha_fin': tarifa_extraida['fecha_fin'],
            'activa': True,
            'grupos': self._generar_grupos(tarifa_extraida),
            'franjas': self._generar_franjas(tarifa_extraida),
        }
        
        return tarifa_tap
    
    def _generar_codigo(self, tarifa: Dict[str, Any]) -> str:
        """Genera código único: MERCADO-NIVEL-TIPO-YYYYMM"""
        mercado = tarifa['mercado'].replace(' ', '')[:10]
        nivel = tarifa['nivel_tension'].replace(' ', '')[:10]
        tipo = tarifa.get('tipo_tarifa') or 'SIN'
        periodo = tarifa['fecha_inicio'].strftime('%Y%m')
        return f"{mercado}-{nivel}-{tipo}-{periodo}"
    
    def _generar_nombre(self, tarifa: Dict[str, Any]) -> str:
        """Genera nombre descriptivo"""
        mes = tarifa['fecha_inicio'].strftime('%B')
        anio = tarifa['fecha_inicio'].year
        return f"Tarifa {tarifa['mercado']} {tarifa['nivel_tension']} - {mes} {anio}"
    
    def _generar_grupos(self, tarifa: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera los 6 grupos TAP desde CU_Base/CU_Aplicado"""
        cu_base = tarifa.get('cu_base', 0)
        
        # Distribuir CU_Base en 6 grupos (ejemplo proporcional)
        # En producción, esto vendría de datos desagregados del PDF
        distribucion = {
            'G': 0.40,   # 40% Generación
            'T': 0.15,   # 15% Transmisión
            'D': 0.25,   # 25% Distribución
            'CV': 0.10,  # 10% Comercialización
            'PR': 0.05,  # 5% Pérdidas
            'R': 0.05,   # 5% Restricciones
        }
        
        grupos = []
        for codigo, porcentaje in distribucion.items():
            grupos.append({
                'codigo_grupo': codigo,
                'nombre_grupo': self._nombre_grupo(codigo),
                'valor': cu_base * porcentaje,
                'rate_type_id': 1
            })
        
        return grupos
    
    def _generar_franjas(self, tarifa: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera las franjas horarias"""
        franjas = []
        valores = tarifa.get('valores_franja', {})
        
        for codigo, valor in valores.items():
            if valor is not None:
                franjas.append({
                    'codigo_franja': codigo,
                    'valor': valor,
                    'es_precio_directo': True,
                    'orden': int(codigo[1]),
                })
        
        return franjas
    
    def _nombre_grupo(self, codigo: str) -> str:
        nombres = {
            'G': 'Generación',
            'T': 'Transmisión',
            'D': 'Distribución',
            'CV': 'Comercialización',
            'PR': 'Pérdidas',
            'R': 'Restricciones'
        }
        return nombres.get(codigo, codigo)