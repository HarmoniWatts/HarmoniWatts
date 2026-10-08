from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import Optional, List, Dict, Any
from datetime import date
from loguru import logger

from app.models.postgres.tarifa import Tarifa
from app.models.postgres.periodo_tarifario import PeriodoTarifario
from app.models.postgres.tarifa_valor import TarifaValor
from app.models.postgres.componente_valor_mes import ComponenteValorMes
from app.models.postgres.franja_horaria import FranjaHoraria
from app.models.postgres.configuracion_horaria import ConfiguracionHoraria


class TarifaRepository:
    """
    Repositorio para operaciones CRUD de tarifas en el modelo TAP.
    
    Maneja:
    - Tarifa (cabecera)
    - PeriodoTarifario (versiones mensuales)
    - TarifaValor (valores por franja o monomia)
    - ComponenteValorMes (G, T, D, Cv, PR, R)
    - FranjaHoraria y ConfiguracionHoraria
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # =====================================================
    # TARIFA (cabecera)
    # =====================================================
    
    def get_by_id(self, id_tarifa: int) -> Optional[Tarifa]:
        """Obtiene una tarifa por su ID"""
        return self.db.query(Tarifa).filter(Tarifa.id_tarifa == id_tarifa).first()
    
    def get_by_codigo(self, codigo_tarifa: str) -> Optional[Tarifa]:
        """Busca una tarifa por su código único"""
        return self.db.query(Tarifa).filter(
            Tarifa.codigo_tarifa == codigo_tarifa
        ).first()
    
    def get_by_combinacion(
        self,
        cod_comercializadora: str,
        cod_mercado: str,
        cod_nivel: str,
        cod_tipo_tarifa: Optional[str] = None
    ) -> List[Tarifa]:
        """
        Busca tarifas por combinación de comercializadora + mercado + nivel.
        """
        query = self.db.query(Tarifa).filter(
            Tarifa.cod_comercializadora == cod_comercializadora,
            Tarifa.cod_mercado == cod_mercado,
            Tarifa.cod_nivel == cod_nivel
        )
        
        if cod_tipo_tarifa:
            query = query.filter(Tarifa.cod_tipo_tarifa == cod_tipo_tarifa)
        
        return query.all()
    
    def get_activas(self) -> List[Tarifa]:
        """Obtiene todas las tarifas activas"""
        return self.db.query(Tarifa).filter(Tarifa.activa == True).all()
    
    def get_by_mercado(self, cod_mercado: str) -> List[Tarifa]:
        """Obtiene todas las tarifas de un mercado"""
        return self.db.query(Tarifa).filter(
            Tarifa.cod_mercado == cod_mercado,
            Tarifa.activa == True
        ).all()
    
    def crear(self, tarifa_data: Dict[str, Any]) -> Tarifa:
        """Crea una nueva tarifa"""
        tarifa = Tarifa(**tarifa_data)
        self.db.add(tarifa)
        self.db.commit()
        self.db.refresh(tarifa)
        return tarifa
    
    def actualizar(self, id_tarifa: int, datos: Dict[str, Any]) -> Optional[Tarifa]:
        """Actualiza una tarifa existente"""
        tarifa = self.get_by_id(id_tarifa)
        if tarifa:
            for key, value in datos.items():
                setattr(tarifa, key, value)
            self.db.commit()
            self.db.refresh(tarifa)
        return tarifa
    
    def eliminar(self, id_tarifa: int) -> bool:
        """Elimina una tarifa"""
        tarifa = self.get_by_id(id_tarifa)
        if tarifa:
            self.db.delete(tarifa)
            self.db.commit()
            return True
        return False
    
    # =====================================================
    # PERIODO TARIFARIO (versiones mensuales)
    # =====================================================
    
    def get_periodo(
        self,
        id_tarifa: int,
        anio: int,
        mes: int,
        version: Optional[int] = None,
        estado: Optional[str] = None
    ) -> Optional[PeriodoTarifario]:
        """
        Obtiene un período tarifario específico.
        Si no se especifica versión, retorna la publicada.
        """
        query = self.db.query(PeriodoTarifario).filter(
            PeriodoTarifario.id_tarifa == id_tarifa,
            PeriodoTarifario.anio == anio,
            PeriodoTarifario.mes == mes
        )
        
        if version:
            query = query.filter(PeriodoTarifario.numero_version == version)
        elif estado:
            query = query.filter(PeriodoTarifario.estado == estado)
        else:
            # Por defecto, la publicada
            query = query.filter(PeriodoTarifario.estado == 'PUBLICADA')
        
        return query.first()
    
    def get_periodos_by_tarifa(self, id_tarifa: int) -> List[PeriodoTarifario]:
        """Obtiene todos los períodos de una tarifa"""
        return (
            self.db.query(PeriodoTarifario)
            .filter(PeriodoTarifario.id_tarifa == id_tarifa)
            .order_by(desc(PeriodoTarifario.anio), desc(PeriodoTarifario.mes))
            .all()
        )
    
    def get_periodo_vigente(
        self,
        id_tarifa: int,
        fecha: date
    ) -> Optional[PeriodoTarifario]:
        """
        Obtiene el período vigente para una fecha específica.
        """
        return (
            self.db.query(PeriodoTarifario)
            .filter(
                PeriodoTarifario.id_tarifa == id_tarifa,
                PeriodoTarifario.fecha_inicio <= fecha,
                PeriodoTarifario.fecha_fin >= fecha,
                PeriodoTarifario.estado == 'PUBLICADA'
            )
            .first()
        )
    
    def crear_periodo(self, periodo_data: Dict[str, Any]) -> PeriodoTarifario:
        """Crea un nuevo período tarifario"""
        periodo = PeriodoTarifario(**periodo_data)
        self.db.add(periodo)
        self.db.commit()
        self.db.refresh(periodo)
        return periodo
    
    def upsert_periodo(
        self,
        id_tarifa: int,
        anio: int,
        mes: int,
        datos: Dict[str, Any]
    ) -> PeriodoTarifario:
        """
        Inserta o actualiza un período tarifario.
        Si ya existe la versión PUBLICADA, la marca como SUPERADA y crea una nueva.
        """
        existente = self.get_periodo(id_tarifa, anio, mes, estado='PUBLICADA')
        
        if existente:
            # Marcar como SUPERADA
            existente.estado = 'SUPERADA'
            self.db.commit()
            
            # Crear nueva versión
            datos['numero_version'] = existente.numero_version + 1
            datos['id_tarifa'] = id_tarifa
            datos['anio'] = anio
            datos['mes'] = mes
            return self.crear_periodo(datos)
        else:
            # Primera versión
            datos['numero_version'] = 1
            datos['id_tarifa'] = id_tarifa
            datos['anio'] = anio
            datos['mes'] = mes
            return self.crear_periodo(datos)
    
    # =====================================================
    # TARIFA VALOR (valores por franja o monomia)
    # =====================================================
    
    def get_valores_by_periodo(
        self,
        id_periodo_tarifario: int
    ) -> List[TarifaValor]:
        """Obtiene todos los valores de un período"""
        return (
            self.db.query(TarifaValor)
            .filter(TarifaValor.id_periodo_tarifario == id_periodo_tarifario)
            .all()
        )
    
    def get_valores_by_franja(
        self,
        id_periodo_tarifario: int,
        codigo_franja: str
    ) -> Optional[TarifaValor]:
        """Obtiene el valor de una franja específica"""
        return (
            self.db.query(TarifaValor)
            .join(FranjaHoraria)
            .filter(
                TarifaValor.id_periodo_tarifario == id_periodo_tarifario,
                FranjaHoraria.codigo == codigo_franja
            )
            .first()
        )
    
    def get_valor_monomia(
        self,
        id_periodo_tarifario: int
    ) -> Optional[TarifaValor]:
        """Obtiene el valor de una monomia sencilla (sin franja)"""
        return (
            self.db.query(TarifaValor)
            .filter(
                TarifaValor.id_periodo_tarifario == id_periodo_tarifario,
                TarifaValor.id_franja_horaria.is_(None)
            )
            .first()
        )
    
    def crear_valor(self, valor_data: Dict[str, Any]) -> TarifaValor:
        """Crea un nuevo valor de tarifa"""
        valor = TarifaValor(**valor_data)
        self.db.add(valor)
        self.db.commit()
        self.db.refresh(valor)
        return valor
    
    def crear_valores_batch(
        self,
        id_periodo_tarifario: int,
        valores: List[Dict[str, Any]]
    ) -> List[TarifaValor]:
        """Crea múltiples valores en lote"""
        valores_creados = []
        for v in valores:
            v['id_periodo_tarifario'] = id_periodo_tarifario
            valor = TarifaValor(**v)
            self.db.add(valor)
            valores_creados.append(valor)
        self.db.commit()
        return valores_creados
    
    # =====================================================
    # COMPONENTE VALOR MES (G, T, D, Cv, PR, R)
    # =====================================================
    
    def get_componentes_by_periodo(
        self,
        id_periodo_tarifario: int
    ) -> List[ComponenteValorMes]:
        """Obtiene todos los componentes de un período"""
        return (
            self.db.query(ComponenteValorMes)
            .filter(ComponenteValorMes.id_periodo_tarifario == id_periodo_tarifario)
            .all()
        )
    
    def get_componente(
        self,
        id_periodo_tarifario: int,
        cod_componente: str
    ) -> Optional[ComponenteValorMes]:
        """Obtiene un componente específico"""
        return (
            self.db.query(ComponenteValorMes)
            .filter(
                ComponenteValorMes.id_periodo_tarifario == id_periodo_tarifario,
                ComponenteValorMes.cod_componente == cod_componente
            )
            .first()
        )
    
    def crear_componentes_batch(
        self,
        id_periodo_tarifario: int,
        componentes: List[Dict[str, Any]]
    ) -> List[ComponenteValorMes]:
        """Crea los componentes de un período"""
        creados = []
        for c in componentes:
            c['id_periodo_tarifario'] = id_periodo_tarifario
            comp = ComponenteValorMes(**c)
            self.db.add(comp)
            creados.append(comp)
        self.db.commit()
        return creados
    
    # =====================================================
    # UPSERT COMPLETO (para extracción automática)
    # =====================================================
    
    def upsert_tarifa_completa(
        self,
        tarifa_data: Dict[str, Any],
        periodo_data: Dict[str, Any],
        valores: List[Dict[str, Any]],
        componentes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Inserta o actualiza una tarifa completa:
        - Tarifa (cabecera)
        - PeriodoTarifario (versión mensual)
        - TarifaValor (franjas)
        - ComponenteValorMes (G, T, D, Cv, PR, R)
        
        Retorna un resumen de la operación.
        """
        resultado = {
            'tarifa_creada': False,
            'periodo_creado': False,
            'valores_creados': 0,
            'componentes_creados': 0
        }
        
        try:
            # 1. Buscar o crear la Tarifa
            tarifa = self.get_by_codigo(tarifa_data['codigo_tarifa'])
            
            if not tarifa:
                tarifa = self.crear(tarifa_data)
                resultado['tarifa_creada'] = True
                logger.info(f"Tarifa creada: {tarifa.codigo_tarifa}")
            
            # 2. Buscar o crear el PeriodoTarifario
            periodo = self.get_periodo(
                tarifa.id_tarifa,
                periodo_data['anio'],
                periodo_data['mes'],
                estado='PUBLICADA'
            )
            
            if not periodo:
                periodo_data['id_tarifa'] = tarifa.id_tarifa
                periodo = self.crear_periodo(periodo_data)
                resultado['periodo_creado'] = True
                logger.info(f"Período creado: {periodo.anio}-{periodo.mes}")
            else:
                # Verificar si ya tiene valores
                valores_existentes = self.get_valores_by_periodo(periodo.id_periodo_tarifario)
                if valores_existentes:
                    logger.info(f"Período ya existe con valores: {periodo.anio}-{periodo.mes}")
                    resultado['valores_creados'] = 0
                    return resultado
            
            # 3. Crear los valores de franjas
            if valores:
                self.crear_valores_batch(periodo.id_periodo_tarifario, valores)
                resultado['valores_creados'] = len(valores)
                logger.info(f"Valores creados: {len(valores)}")
            
            # 4. Crear los componentes
            if componentes:
                self.crear_componentes_batch(periodo.id_periodo_tarifario, componentes)
                resultado['componentes_creados'] = len(componentes)
                logger.info(f"Componentes creados: {len(componentes)}")
            
            return resultado
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error en upsert_tarifa_completa: {e}")
            raise
    
    # =====================================================
    # CONSULTAS PARA EL DASHBOARD
    # =====================================================
    
    def get_tarifa_vigente_completa(
        self,
        id_cliente: int,
        fecha: date
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene la tarifa vigente completa para un cliente en una fecha.
        Incluye: tarifa, período, valores y componentes.
        """
        from app.models.postgres.cliente import Cliente
        
        # Obtener el cliente
        cliente = self.db.query(Cliente).filter(
            Cliente.id_cliente == id_cliente
        ).first()
        
        if not cliente:
            return None
        
        # Buscar tarifa que coincida con la clasificación del cliente
        tarifa = (
            self.db.query(Tarifa)
            .filter(
                Tarifa.cod_comercializadora == cliente.cod_comercializadora,
                Tarifa.cod_mercado == cliente.cod_mercado,
                Tarifa.cod_nivel == cliente.cod_nivel,
                Tarifa.activa == True
            )
            .first()
        )
        
        if not tarifa:
            return None
        
        # Obtener período vigente
        periodo = self.get_periodo_vigente(tarifa.id_tarifa, fecha)
        
        if not periodo:
            return None
        
        # Obtener valores y componentes
        valores = self.get_valores_by_periodo(periodo.id_periodo_tarifario)
        componentes = self.get_componentes_by_periodo(periodo.id_periodo_tarifario)
        
        return {
            'tarifa': tarifa,
            'periodo': periodo,
            'valores': valores,
            'componentes': componentes
        }
    
    def get_precio_por_hora(
        self,
        id_cliente: int,
        fecha: date,
        hora: int
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene el precio para una hora específica.
        Usa la configuración horaria aplicable al mercado+nivel del cliente.
        """
        from app.models.postgres.configuracion_aplicable import ConfiguracionAplicable
        from app.models.postgres.configuracion_hora import ConfiguracionHora
        from app.models.postgres.cliente import Cliente
        
        # Obtener cliente
        cliente = self.db.query(Cliente).filter(
            Cliente.id_cliente == id_cliente
        ).first()
        
        if not cliente:
            return None
        
        # Obtener configuración aplicable
        config_aplicable = (
            self.db.query(ConfiguracionAplicable)
            .filter(
                ConfiguracionAplicable.cod_comercializadora == cliente.cod_comercializadora,
                ConfiguracionAplicable.cod_mercado == cliente.cod_mercado,
                ConfiguracionAplicable.cod_nivel == cliente.cod_nivel,
                ConfiguracionAplicable.vigente_desde <= fecha,
                or_(
                    ConfiguracionAplicable.vigente_hasta.is_(None),
                    ConfiguracionAplicable.vigente_hasta >= fecha
                )
            )
            .first()
        )
        
        if not config_aplicable:
            return None
        
        # Obtener franja para esa hora
        config_hora = (
            self.db.query(ConfiguracionHora)
            .filter(
                ConfiguracionHora.id_configuracion_horaria == config_aplicable.id_configuracion_horaria,
                ConfiguracionHora.hora == hora
            )
            .first()
        )
        
        if not config_hora:
            return None
        
        # Obtener tarifa y período
        tarifa_data = self.get_tarifa_vigente_completa(id_cliente, fecha)
        if not tarifa_data:
            return None
        
        # Buscar el valor de esa franja
        franja = self.db.query(FranjaHoraria).filter(
            FranjaHoraria.id_franja_horaria == config_hora.id_franja_horaria
        ).first()
        
        valor = next(
            (v for v in tarifa_data['valores'] 
             if v.id_franja_horaria == config_hora.id_franja_horaria),
            None
        )
        
        if not valor:
            return None
        
        return {
            'hora': hora,
            'codigo_franja': franja.codigo if franja else None,
            'precio': float(valor.valor),
            'unidad': valor.unidad
        }
    
    def get_precios_dia(
        self,
        id_cliente: int,
        fecha: date
    ) -> List[Dict[str, Any]]:
        """
        Obtiene los precios de las 24 horas del día para un cliente.
        Útil para el gráfico del dashboard.
        """
        return [
            self.get_precio_por_hora(id_cliente, fecha, hora)
            for hora in range(1, 25)
        ]