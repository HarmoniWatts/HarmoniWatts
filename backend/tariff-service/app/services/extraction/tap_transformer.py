from typing import Dict, Any, List, Optional
from datetime import date
from decimal import Decimal
import calendar
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
        comercializadora_cod: str
    ) -> Dict[str, Any]:
        """
        Transforma una tarifa extraída del PDF en el conjunto completo
        de estructuras TAP listas para persistir.
        
        Returns:
            {
                'tarifa': dict,
                'periodo': dict,
                'valores': list[dict],
                'componentes': list[dict],
            }
            o None si hay errores de normalización
        """
        
         # 1. Normalizar campos
        cod_mercado = self._normalizar_mercado(tarifa_extraida.get('mercado', ''))
        cod_nivel = self._normalizar_nivel(tarifa_extraida.get('nivel_tension', ''))
        cod_tipo_tarifa = tarifa_extraida.get('tipo_tarifa')
        
        if not cod_mercado:
            logger.error(f"Mercado no normalizado: {tarifa_extraida.get('mercado')}")
            return None
        
        if not cod_nivel:
            logger.error(f"Nivel no normalizado: {tarifa_extraida.get('nivel_tension')}")
            return None
        
        # 2. Generar código único
        codigo = self._generar_codigo(tarifa_extraida, comercializadora_cod)
        
        # if tarifa_extraida['mercado'] == "CALI":
        #     print(f"\nTransformando tarifa extraída: {tarifa_extraida}")
        
        # print(f"\nTransformando tarifa extraída: {tarifa_extraida}")
        
        
        # Estructura TAP
        tarifa_data = {
            'cod_comercializadora': comercializadora_cod,
            'cod_mercado': cod_mercado,
            'cod_nivel': cod_nivel,
            'cod_tipo_tarifa': cod_tipo_tarifa,
            'codigo_tarifa': codigo,
            'nombre_tarifa': self._generar_nombre(tarifa_extraida),
            'resolucion_regulatoria': 'CREG 119/2007, CREG 101/2023',
            'activa': True,
        }
        
        # print(f"\nTarifa transformada a TAP: {tarifa_data}")
        
        # 4. Construir PeriodoTarifario
        periodo_data = self._construir_periodo(tarifa_extraida)
        
        # 5. Construir TarifaValor (franjas)
        valores_data = self._construir_valores(tarifa_extraida)
        
        
        # 6. Construir ComponenteValorMes (G, T, D, Cv, PR, R)
        componentes_data = self._construir_componentes(tarifa_extraida)
        
        #return tarifa_tap
        
        return {
            'tarifa': tarifa_data,
            'periodo': periodo_data,
            'valores': valores_data,
            'componentes': componentes_data,
        }
    
    # =====================================================
    # MÉTODOS DE NORMALIZACIÓN
    # =====================================================
    
    def _normalizar_mercado(self, mercado_pdf: str) -> Optional[str]:
        """
        Normaliza el nombre del mercado del PDF al código de BD.
        
        Ejemplos:
            "CALI" → "CALI"
            "CARIBE MAR" → "CARIBE_MAR"
            "NARIÑO" → "NARINO"
        """
        if not mercado_pdf:
            return None
        
        mercado_norm = mercado_pdf.replace(' ', '_').upper()
        mercado_norm = mercado_norm.replace('Ñ', 'N').upper()
        
        return mercado_norm
    
    
    def _normalizar_nivel(self, nivel_pdf: str) -> Optional[str]:
        """
        Normaliza el nivel de tensión del PDF al código de BD.
        
        Ejemplos:
            "Nivel 1.1" → "N1_1"
            "N 1.2* - 50%" → "N1_2_50"
            "Nivel 3" → "N3"
        """
        
        # =====================================================
        # MAPEO DE NIVELES DE TENSIÓN (PDF → BD)
        # =====================================================
        nivel_map = {
            # Nivel 1.1
            'Nivel 1.1': 'N1_1',
            
            # Nivel 1.2
            'Nivel 1.2': 'N1_2',
            
            # Nivel 1.2-1.3
            'N 1.2-1.3': 'N1_2_1_3',
            'N 1.2 - 1.3': 'N1_2_1_3',
            
            # Nivel 1.2* - 50%
            'N 1.2* - 50%': 'N1_2_50',
            'N 1.2*-50%': 'N1_2_50',
            
            # Nivel 1.2*-1.3* -50%
            'N 1.2*-1.3* -50%': 'N1_2_1_3_50',
            'N 1.2*-1.3* -\n50%': 'N1_2_1_3_50',
            
            # Nivel 2
            'Nivel 2': 'N2',
            
            # Nivel 3
            'Nivel 3': 'N3',
            
            # Nivel 4
            'Nivel 4': 'N4',
        }
        
        
        if not nivel_pdf:
            return None
        
        key = nivel_pdf
        
        # Búsqueda exacta
        if key in nivel_map:
            return nivel_map[key]
        
        # Búsqueda parcial
        for patron, codigo in nivel_map.items():
            if patron in key:
                logger.debug(
                    f"Nivel normalizado (parcial): "
                    f"'{nivel_pdf}' → '{codigo}'"
                )
                return codigo
        
        logger.warning(f"Nivel no reconocido: '{nivel_pdf}'")
        print(nivel_pdf)
        return None
    
    def _generar_codigo(self, tarifa: Dict[str, Any], comercializadora_cod: str) -> str:
        """Genera código único: MERCADO-NIVEL-TIPO-YYYYMM"""
        mercado = self._normalizar_mercado(tarifa['mercado']).replace(' ', '')[:10]
        nivel = self._normalizar_nivel(tarifa['nivel_tension']).replace(' ', '')[:10]
        tipo = tarifa.get('tipo_tarifa') or 'SIN'
        return f"{mercado}_{nivel}_{tipo}_{comercializadora_cod}"
    
    def _generar_nombre(self, tarifa: Dict[str, Any]) -> str:
        """Genera nombre descriptivo"""
        return f"Tarifa {tarifa['mercado']} {tarifa['nivel_tension']} - tipo {tarifa['tipo_tarifa']}"
    
    
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
    
    
    # =====================================================
    # CONSTRUCCIÓN DE PERIODO_TARIFARIO
    # =====================================================
    
    def _construir_periodo(self, tarifa_extraida: dict) -> dict:
        """
        Construye la estructura para periodo_tarifario.
        
        Ejemplo:
            {
                'anio': 2024,
                'mes': 1,
                'fecha_inicio': date(2024, 1, 1),
                'fecha_fin': date(2024, 1, 31),
                'numero_version': 1,
                'estado': 'PUBLICADA',
                'fecha_publicacion': date(2024, 1, 1),
                'observaciones': None,
            }
        """
        anio = tarifa_extraida['anio']
        mes = tarifa_extraida['mes']
        
        # Calcular último día del mes
        ultimo_dia = calendar.monthrange(anio, mes)[1]
        
        return {
            'anio': anio,
            'mes': mes,
            'fecha_inicio': date(anio, mes, 1),
            'fecha_fin': date(anio, mes, ultimo_dia),
            'numero_version': 1,
            'estado': 'PUBLICADA',
            'fecha_calculo': date(anio, mes, 1),
            'fecha_publicacion': date(anio, mes, 1),
            'observaciones': None,
            # id_configuracion_horaria: se resuelve con el trigger trg_periodo_config
        }
    
    # =====================================================
    # CONSTRUCCIÓN DE TARIFA_VALOR
    # =====================================================
    
    def _construir_valores(self, tarifa_extraida: dict) -> list[dict]:
        """
        Construye la lista de valores por franja para tarifa_valor.
        
        Ejemplo de salida:
            [
                {'codigo_franja': 'F1', 'valor': Decimal('752.15'), 'unidad': 'COP/kWh'},
                {'codigo_franja': 'F2', 'valor': Decimal('765.76'), 'unidad': 'COP/kWh'},
                ...
            ]
        
        Nota:
            - Si la tarifa es monomia sencilla (sin franjas), retorna []
              y el valor total va en componentes.
            - Solo incluye franjas con valor no nulo.
        """
        valores = []
        franjas = tarifa_extraida.get('valores_franja', {})
        
        for codigo_franja in ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8']:
            valor = franjas.get(codigo_franja)
            
            # Solo incluir franjas con valor
            if valor is None:
                continue
            
            valores.append({
                'codigo_franja': codigo_franja,
                'valor': valor,
                'unidad': 'COP/kWh',
            })
        
        # Si no hay franjas, agregar monomia sencilla
        #print(f"CU aplicado: {tarifa_extraida.get('cu_aplicado')}")
        valores.append({
            'codigo_franja': None,
            'valor': tarifa_extraida.get('cu_aplicado'),
            'unidad': 'COP/kWh',
        })
        
        return valores
    
    # =====================================================
    # CONSTRUCCIÓN DE COMPONENTE_VALOR_MES
    # =====================================================
    
    def _construir_componentes(self, tarifa_extraida: dict) -> list[dict]:
        """
        Construye la lista de componentes del CU para componente_valor_mes.
        
        Componentes esperados:
            Gm  → Generación
            Tm  → Transmisión
            Dm  → Distribución
            Cm  → Comercialización
            PRm → Pérdidas (en PDF puede venir como 'PR')
            Rm  → Restricciones
            COT → Opción Tarifaria (opcional)
            Cfmj → Costo Fijo de Comercialización (opcional)
        
        Ejemplo de salida:
            [
                {'cod_componente': 'Gm',  'valor': Decimal('387.07')},
                {'cod_componente': 'Cm',  'valor': Decimal('32.05')},
                {'cod_componente': 'PRm', 'valor': Decimal('69.74')},
                {'cod_componente': 'Dm',  'valor': Decimal('213.15')},
                {'cod_componente': 'Tm',  'valor': Decimal('54.32')},
                {'cod_componente': 'Rm',  'valor': Decimal('9.75')},
            ]
        """
        
        # =====================================================
        # MAPEO DE COMPONENTES (PDF → BD)
        # =====================================================
        componentes_map = {
            'Gm': 'Gm',      # Generación
            'Cm': 'Cm',      # Comercialización
            'PR': 'PRm',     # Pérdidas (PDF usa 'PR', BD usa 'PRm')
            'PRm': 'PRm',
            'Dm': 'Dm',      # Distribución
            'Tm': 'Tm',      # Transmisión
            'Rm': 'Rm',      # Restricciones
            'COT': 'COT',    # Opción Tarifaria
        }
    
        componentes = []
        componentes_pdf = tarifa_extraida.get('componentes_cu', {})
        
        for cod_pdf, valor in componentes_pdf.items():
            if valor is None:
                continue
            
            # Normalizar código de componente
            cod_bd = componentes_map.get(cod_pdf, cod_pdf)
            
            componentes.append({
                'cod_componente': cod_bd,
                'valor': valor,
            })
        
        # Agregar Cfmj si está presente   
        if tarifa_extraida.get('Cmfj'):
            componentes.append({
                'cod_componente': 'Cfmj',
                'valor': tarifa_extraida['Cmfj'],
            })
        
        # Agregar COT si está presente
        cot = tarifa_extraida.get('cot')
        if cot is not None:
            componentes.append({
                'cod_componente': 'COT',
                'valor': cot,
            })
        
        return componentes
    