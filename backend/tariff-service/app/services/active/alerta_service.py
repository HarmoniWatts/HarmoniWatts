# app/services/active/alerta_service.py

from datetime import date, datetime
from typing import Optional, Dict, Any, List
from loguru import logger

from app.repositories.postgres.tarifa_repository import TarifaRepository
from app.repositories.postgres.cliente_repository import ClienteRepository
from app.services.business.tarifa_selector import TarifaSelector
from app.services.active.franja_service import FranjaService


class AlertaTarifaService:
    """
    Lógica de negocio para detección de ventanas de alta tarifa.
    
    Responsabilidades:
        - Detectar la próxima ventana de alta tarifa
        - Agrupar horas contiguas
        - Calcular ahorro potencial
        - Generar mensajes para el usuario
    """
    
    # Umbral de diferencia para considerar "significativamente alto"
    UMBRAL_DIFERENCIA = 0.20   # 20% más que el mínimo
    
    # Códigos de franja típicos de PUNTA
    FRANJAS_PUNTA = {'F3', 'F4'}
    
    def __init__(
        self,
        repo: TarifaRepository,
        cliente_repo: Optional[ClienteRepository] = None,
        selector: Optional[TarifaSelector] = None
    ):
        self.repo = repo
        # Reutiliza la selección de tipo de tarifa de FranjaService
        self.franja_service = FranjaService(repo, cliente_repo, selector)
    
    # =====================================================
    # DETECCIÓN DE VENTANA ALTA
    # =====================================================
    
    def detectar_proxima_ventana_alta(
        self,
        id_cliente: int,
        horizonte_horas: int = 12,
        umbral_punta: bool = True,
        consumo_mensual_kwh: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Detecta la próxima ventana de alta tarifa.
        
        Args:
            id_cliente: ID del cliente
            horizonte_horas: horas a futuro para buscar (1-24)
            umbral_punta: si True, solo considera franjas PUNTA
        
        Returns:
            Dict con la ventana detectada o None si no hay
        """
        # 1. Determinar hora actual
        ahora = datetime.now()
        hora_actual = ahora.hour if ahora.hour > 0 else 24
        hora_fin = min(hora_actual + horizonte_horas, 24)
        
        # 2. Obtener precios del día
        precios_dia = self.repo.get_precios_dia(
            id_cliente=id_cliente,
            fecha=date.today(),
            cod_tipo_tarifa=self.franja_service._tipo_tarifa(id_cliente, consumo_mensual_kwh)
        )
        
        if not precios_dia:
            logger.warning(f"Sin precios para cliente {id_cliente}")
            return None
        
        # 3. Filtrar precios en el horizonte
        precios_horizonte = [
            p for p in precios_dia
            if hora_actual <= p['hora'] <= hora_fin
            and p.get('precio') is not None
        ]
        
        if not precios_horizonte:
            return self._respuesta_sin_franja(
                id_cliente, hora_actual,
                "No hay precios en el horizonte especificado"
            )
        
        # 4. Detectar ventana
        ventana = self._detectar_ventana(
            precios_horizonte,
            precios_dia,
            umbral_punta
        )
        
        if not ventana:
            return self._respuesta_sin_franja(
                id_cliente, hora_actual,
                "No se detectó una franja de alta tarifa en el horizonte"
            )
        
        # 5. Calcular ahorro potencial
        ahorro = self._calcular_ahorro(ventana, precios_dia)
        
        # 6. Construir respuesta
        return self._construir_respuesta(
            id_cliente=id_cliente,
            hora_actual=hora_actual,
            ventana=ventana,
            ahorro=ahorro
        )
    
    # =====================================================
    # DETECCIÓN INTERNA
    # =====================================================
    
    def _detectar_ventana(
        self,
        precios_horizonte: List[Dict],
        precios_dia: List[Dict],
        umbral_punta: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Detecta la ventana de alta tarifa.
        
        Estrategia:
            - Si umbral_punta=True: busca franjas PUNTA o F3/F4
            - Si umbral_punta=False: busca la hora de mayor precio
        """
        # Estrategia A: buscar franja PUNTA
        if umbral_punta:
            horas_punta = [
                p for p in precios_horizonte
                if p.get('tipo_hora') == 'PUNTA'
                or p.get('codigo_franja') in self.FRANJAS_PUNTA
            ]
            
            if horas_punta:
                return self._agrupar_ventana(horas_punta)
        
        # Estrategia B: buscar hora de mayor precio
        return self._detectar_por_precio(precios_horizonte)
    
    def _detectar_por_precio(
        self,
        precios_horizonte: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        """Detecta la ventana por precio máximo relativo."""
        picos = sorted(precios_horizonte, key=lambda x: x['precio'], reverse=True)
        precio_max = picos[0]['precio']
        precio_min = min(p['precio'] for p in precios_horizonte)
        
        # Solo si es significativamente más alto
        if precio_max <= precio_min * (1 + self.UMBRAL_DIFERENCIA):
            return None
        
        # Horas con precio cercano al máximo (90%+)
        horas_caras = [
            p for p in precios_horizonte
            if p['precio'] >= precio_max * 0.9
        ]
        
        return self._agrupar_ventana(horas_caras)
    
    def _agrupar_ventana(
        self,
        horas: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        """Agrupa horas contiguas en una ventana."""
        if not horas:
            return None
        
        horas_ordenadas = sorted(horas, key=lambda x: x['hora'])
        
        # Encontrar primera ventana contigua
        inicio = horas_ordenadas[0]
        fin = inicio
        
        for h in horas_ordenadas[1:]:
            if h['hora'] == fin['hora'] + 1:
                fin = h
            else:
                break
        
        precios_ventana = [
            p['precio'] for p in horas_ordenadas
            if inicio['hora'] <= p['hora'] <= fin['hora']
        ]
        
        return {
            'hora_inicio': inicio['hora'],
            'hora_fin': fin['hora'],
            'codigo_franja': inicio.get('codigo_franja'),
            'tipo_hora': inicio.get('tipo_hora'),
            'precio_max': max(precios_ventana),
            'precio_min': min(precios_ventana),
            'unidad': inicio.get('unidad', 'COP/kWh'),
            'horas': [
                p['hora'] for p in horas_ordenadas
                if inicio['hora'] <= p['hora'] <= fin['hora']
            ],
        }
    
    # =====================================================
    # CÁLCULO DE AHORRO
    # =====================================================
    
    def _calcular_ahorro(
        self,
        ventana: Dict[str, Any],
        precios_dia: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calcula el ahorro potencial si se desplaza el consumo.
        
        Compara el precio máximo de la ventana con el precio mínimo del día.
        """
        precios = [
            p['precio'] for p in precios_dia
            if p.get('precio') is not None
        ]
        
        if not precios:
            return {'ahorro_potencial': 0, 'precio_valle': 0}
        
        precio_valle = min(precios)
        duracion = ventana['hora_fin'] - ventana['hora_inicio'] + 1
        ahorro = (ventana['precio_max'] - precio_valle) * duracion
        
        return {
            'ahorro_potencial': round(ahorro, 2),
            'precio_valle': precio_valle,
            'duracion_horas': duracion,
        }
    
    # =====================================================
    # CONSTRUCCIÓN DE RESPUESTA
    # =====================================================
    
    def _construir_respuesta(
        self,
        id_cliente: int,
        hora_actual: int,
        ventana: Dict[str, Any],
        ahorro: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Construye la respuesta final."""
        duracion = ahorro['duracion_horas']
        
        mensaje = (
            f"Franja de alta tarifa de {duracion} hora(s) "
            f"desde las {ventana['hora_inicio']}:00 "
            f"hasta las {ventana['hora_fin']}:00. "
            f"Ahorro potencial: {ahorro['ahorro_potencial']} COP/kWh."
        )
        
        return {
            'id_cliente': id_cliente,
            'fecha': date.today(),
            'hora_actual': hora_actual,
            'hay_franja_alta': True,
            'codigo_franja': ventana.get('codigo_franja'),
            'tipo_hora': ventana.get('tipo_hora'),
            'hora_inicio': ventana['hora_inicio'],
            'hora_fin': ventana['hora_fin'],
            'duracion_horas': duracion,
            'precio_max': ventana['precio_max'],
            'precio_valle_referencia': ahorro['precio_valle'],
            'ahorro_potencial': ahorro['ahorro_potencial'],
            'unidad': ventana.get('unidad', 'COP/kWh'),
            'mensaje': mensaje,
        }
    
    def _respuesta_sin_franja(
        self,
        id_cliente: int,
        hora_actual: int,
        mensaje: str
    ) -> Dict[str, Any]:
        """Respuesta cuando no hay franja alta."""
        return {
            'id_cliente': id_cliente,
            'fecha': date.today(),
            'hora_actual': hora_actual,
            'hay_franja_alta': False,
            'mensaje': mensaje,
        }