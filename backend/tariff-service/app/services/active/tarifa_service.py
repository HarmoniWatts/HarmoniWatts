# app/services/active/tarifa_service.py

from datetime import date
from email.policy import default
from typing import Optional, Dict, Any
from loguru import logger

from app.repositories.postgres.tarifa_repository import TarifaRepository
from app.repositories.postgres.cliente_repository import ClienteRepository
from app.services.business.tarifa_selector import TarifaSelector


class TarifaActivaService:
    """
    Lógica de negocio para tarifas activas.
    
    Responsabilidades:
        - Obtener la tarifa vigente de un cliente
        - Validar que exista tarifa para la fecha
        - Formatear la respuesta para la API
    """
    
    def __init__(self, repo: TarifaRepository, cliente_repo: ClienteRepository, selector: TarifaSelector):
        self.repo = repo
        self.cliente_repo = cliente_repo
        self.selector = selector
    
    def obtener_tarifa_vigente(
        self,
        id_cliente: int,
        fecha: Optional[date] = None,
        consumo_mensual_kwh: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene la tarifa vigente completa de un cliente.
        
        Args:
            id_cliente: ID del cliente
            fecha: fecha de consulta (por defecto, hoy)
        
        Returns:
            Dict con la tarifa completa o None si no existe
        """
        fecha_consulta = fecha or date.today()
        cliente = self.cliente_repo.get_by_id(id_cliente)
        cod_tipo_tarifa = self.selector.seleccionar_tipo_tarifa(cliente, consumo_mensual_kwh=consumo_mensual_kwh)
        
        # tarifa = self.repo.get_tarifa_por_clasificacion(
        #     cod_comercializadora=cliente.cod_comercializadora,
        #     cod_mercado=cliente.cod_mercado,
        #     cod_nivel=cliente.cod_nivel,
        #     cod_tipo_tarifa=cod_tipo_tarifa,
        #     fecha=fecha
        # )
        
        # Delegar al repositorio
        tarifa_data = self.repo.get_tarifa_vigente_completa(
            id_cliente=id_cliente,
            fecha=fecha_consulta,
            cod_tipo_tarifa=cod_tipo_tarifa
        )
        # print(f"tarifa_data: {tarifa_data}")
        
        if not tarifa_data:
            logger.warning(
                f"Sin tarifa vigente para cliente Id:{id_cliente} "
                f"en fecha {fecha_consulta}"
            )
            return None
        
        # Formatear para la respuesta
        return self._formatear_respuesta(tarifa_data, fecha_consulta)
    
    def _formatear_respuesta(
        self,
        tarifa_data: Dict[str, Any],
        fecha: date
    ) -> Dict[str, Any]:
        """Formatea la respuesta de la tarifa vigente."""
        tarifa = tarifa_data['tarifa']
        periodo = tarifa_data['periodo']
        valores = tarifa_data['valores']
        componentes = tarifa_data['componentes']
                
        
        return {
            'id_cliente': tarifa_data.get('id_cliente'),
            'fecha_consulta': fecha,
            'tarifa': {
                'id_tarifa': tarifa.id_tarifa,
                'codigo_tarifa': tarifa.codigo_tarifa,
                'nombre_tarifa': tarifa.nombre_tarifa,
                'cod_comercializadora': tarifa.cod_comercializadora,
                'cod_mercado': tarifa.cod_mercado,
                'cod_nivel': tarifa.cod_nivel,
                'cod_tipo_tarifa': tarifa.cod_tipo_tarifa,
                'resolucion_regulatoria': tarifa.resolucion_regulatoria,
            },
            'periodo': {
                'id_periodo_tarifario': periodo.id_periodo_tarifario,
                'anio': periodo.anio,
                'mes': periodo.mes,
                'fecha_inicio': periodo.fecha_inicio,
                'fecha_fin': periodo.fecha_fin,
                'numero_version': periodo.numero_version,
                'estado': periodo.estado,
                'fecha_publicacion': periodo.fecha_publicacion,
            },
            'monomia': tarifa_data.get('monomia'),
            'valores': [
                {
                    'hora': self._get_field(v, 'hora'),
                    'codigo_franja': (
                        self._get_field(v, 'codigo_franja')
                        or self._get_field(v, 'franja')
                    ),
                    'tipo_hora': self._get_field(v, 'tipo_hora'),
                    'valor': float(self._get_field(v, 'valor', 0)),
                    'unidad': self._get_field(v, 'unidad') or 'COP/kWh',
                }
                for v in valores
            ],
            'componentes': [
                {
                    'cod_componente': c.cod_componente,
                    'valor': float(c.valor) if hasattr(c, 'valor') else None,
                }
                for c in componentes
            ],
        }
    
    def _get_field(self, obj, key: str, default=None):
        """
        Obtiene un campo de un objeto o dict.
        Maneja dicts, Row de SQLAlchemy y objetos ORM.
        """
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)