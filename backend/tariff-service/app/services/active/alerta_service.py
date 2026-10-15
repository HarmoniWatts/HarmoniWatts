# app/services/active/alerta_service.py

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional, Dict, Any, List, Tuple
from loguru import logger

from app.repositories.postgres.tarifa_repository import TarifaRepository
from app.repositories.postgres.cliente_repository import ClienteRepository
from app.services.business.tarifa_selector import TarifaSelector


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
    FRANJAS_pico = {'F3', 'F4'}
    
    def __init__(self, repo: TarifaRepository, cliente_repo: ClienteRepository, selector: TarifaSelector):
        self.repo = repo
        self.cliente_repo = cliente_repo
        self.selector = selector
    
    # =====================================================
    # DETECCIÓN DE VENTANA ALTA
    # =====================================================
    
    def detectar_proxima_ventana_alta(
        self,
        id_cliente: int,
        horizonte_horas: int = 12,
        umbral_pico: bool = True,
        consumo_mensual_kwh: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Detecta la próxima ventana de alta tarifa.
        
        Args:
            id_cliente: ID del cliente
            horizonte_horas: horas a futuro para buscar (1-24)
            umbral_pico: si True, solo considera franjas PUNTA
        
        Returns:
            Dict con la ventana detectada o None si no hay
        """
        # 1. Determinar hora actual
        ahora = datetime.now()
        hora_actual = ahora.hour if ahora.hour > 0 else 24
        fecha_actual = ahora.date()
        
        # 1. Construir lista de (fecha, hora) para el horizonte
        horas_horizonte = self._construir_horizonte(
            fecha_actual, hora_actual, horizonte_horas
        )
        
        cliente = self.cliente_repo.get_by_id(id_cliente)
        cod_tipo_tarifa = self.selector.seleccionar_tipo_tarifa(cliente, consumo_mensual_kwh=consumo_mensual_kwh)
        
        # 2. Obtener precios del día
        
        # Fecha inicial de consulta
        fecha_consulta = date.today()
        
        # 3. Obtener precios del día con retroceso mensual
        MAX_MESES_ATRAS = 6
        fecha_consulta = fecha_actual
        precios_dia = None
        
        for intento in range(MAX_MESES_ATRAS + 1):
            precios_dia = self.repo.get_precios_dia(
                id_cliente=id_cliente,
                fecha=fecha_consulta,
                cod_tipo_tarifa=cod_tipo_tarifa,
            )
            
            # Si hay precios, salir del bucle
            if precios_dia and precios_dia.get('precios'):
                logger.info(
                    f"Precios encontrados para cliente {id_cliente} "
                    f"en {fecha_consulta}"
                )
                break
            
            # Si no hay, retroceder un mes
            logger.warning(
                f"Sin precios para cliente {id_cliente} en {fecha_consulta}, "
                f"retrocediendo un mes (intento {intento + 1}/{MAX_MESES_ATRAS})"
            )
            fecha_consulta = fecha_consulta - relativedelta(months=1)
        
        # Si después de 6 intentos no hay precios
        if not precios_dia or not precios_dia.get('precios'):
            logger.warning(
                f"Sin precios para cliente {id_cliente} "
                f"tras {MAX_MESES_ATRAS} meses hacia atrás"
            )
            return self._respuesta_sin_franja(
                id_cliente, hora_actual,
                "No hay precios disponibles para el cliente"
            )
        
        # 4. Filtrar precios en el horizonte
        #    Cada elemento de horas_horizonte es (fecha, hora)
        #    Los precios del día tienen 'hora' (1-24)
        precios = precios_dia['precios']
        precios_horizonte = self._filtrar_precios_horizonte(
            precios=precios,
            horas_horizonte=horas_horizonte,
        )
        
        logger.debug(f"precios_horizonte: {precios_horizonte}")
        
        if not precios_horizonte:
            return self._respuesta_sin_franja(
                id_cliente, hora_actual,
                "No hay precios en el horizonte especificado"
            )
        
        # 5. Detectar ventana de alta tarifa
        ventana = self._detectar_ventana(
            precios_horizonte,
            precios,
            umbral_pico,
        )
        
        if not ventana:
            return self._respuesta_sin_franja(
                id_cliente, hora_actual,
                "No se detectó una franja de alta tarifa en el horizonte"
            )
        
        # 6. Calcular ahorro potencial
        ahorro = self._calcular_ahorro(ventana, precios)
        
        # 7. Construir respuesta
        return self._construir_respuesta(
            id_cliente=id_cliente,
            hora_actual=hora_actual,
            ventana=ventana,
            ahorro=ahorro,
        )
        
    def _construir_horizonte(
        self,
        fecha_inicio: date,
        hora_inicio: int,
        horizonte_horas: int,
    ) -> List[Tuple[date, int]]:
        """
        Construye una lista de (fecha, hora) para el horizonte,
        considerando el cruce de medianoche.
        
        Returns:
            Lista de tuplas (fecha, hora) donde hora ∈ [1, 24].
        """
        resultado = []
        
        for offset in range(horizonte_horas):
            hora_absoluta = hora_inicio + offset
            
            if hora_absoluta > 24:
                dias_extra = (hora_absoluta - 1) // 24
                fecha_hora = fecha_inicio + timedelta(days=dias_extra)
                hora_normalizada = ((hora_absoluta - 1) % 24) + 1
            else:
                fecha_hora = fecha_inicio
                hora_normalizada = hora_absoluta
            
            resultado.append((fecha_hora, hora_normalizada))
        
        return resultado
    
    def _filtrar_precios_horizonte(
        self,
        precios: List[Dict[str, Any]],
        horas_horizonte: List[Tuple[date, int]],
    ) -> List[Dict[str, Any]]:
        """
        Filtra los precios del día según el horizonte de (fecha, hora).
        
        Como el horizonte puede cruzar medianoche, se asume que `precios`
        corresponde al día de `fecha_actual`. Las horas del día siguiente
        se filtran contra el mismo array (asumiendo que son las mismas
        para el siguiente día).
        """
        horas_set = {hora for _, hora in horas_horizonte}
        
        return [
            p for p in precios
            if p.get('hora') in horas_set
            and p.get('precio') is not None
        ]
    # =====================================================
    # DETECCIÓN INTERNA
    # =====================================================
    
    def _detectar_ventana(
        self,
        precios_horizonte: List[Dict],
        precios_dia: List[Dict],
        umbral_pico: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Detecta la ventana de alta tarifa.
        
        Estrategia:
            - Si umbral_pico=True: busca franjas PUNTA o F3/F4
            - Si umbral_pico=False: busca la hora de mayor precio
        """
        # Estrategia A: buscar franja PUNTA
        if umbral_pico:
            horas_pico = [
                p for p in precios_horizonte
                if p.get('tipo_hora') == 'PICO'
                or p.get('codigo_franja') in self.FRANJAS_pico
            ]
            
            if horas_pico:
                return self._agrupar_ventana(horas_pico)
        
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
        print(f"precios_dia {precios_dia}")
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