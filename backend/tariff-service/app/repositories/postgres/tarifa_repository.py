from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import Optional, List, Dict, Any
from datetime import date
from decimal import Decimal
from loguru import logger

from app.models.postgres.tarifa import Tarifa
from app.models.postgres.periodo_tarifario import PeriodoTarifario
from app.models.postgres.tarifa_valor import TarifaValor
from app.models.postgres.componente_valor_mes import ComponenteValorMes
from app.models.postgres.franja_horaria import FranjaHoraria
from app.models.postgres.configuracion_horaria import ConfiguracionHoraria
from app.models.postgres.configuracion_franja import ConfiguracionFranja
from app.models.postgres.configuracion_aplicable import ConfiguracionAplicable
from app.models.postgres.configuracion_hora import ConfiguracionHora
from app.models.postgres.cliente import Cliente
from app.models.postgres.views.v_tarifa_hora import VTarifaHora


class TarifaRepository:
    """
    Repositorio para operaciones CRUD de tarifas en el modelo TAP.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # =====================================================
    # TARIFA (cabecera)
    # =====================================================
    
    def get_by_id(self, id_tarifa: int) -> Optional[Tarifa]:
        return self.db.query(Tarifa).filter(Tarifa.id_tarifa == id_tarifa).first()
    
    def get_by_codigo(self, codigo_tarifa: str) -> Optional[Tarifa]:
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
        query = self.db.query(Tarifa).filter(
            Tarifa.cod_comercializadora == cod_comercializadora,
            Tarifa.cod_mercado == cod_mercado,
            Tarifa.cod_nivel == cod_nivel
        )
        if cod_tipo_tarifa:
            query = query.filter(Tarifa.cod_tipo_tarifa == cod_tipo_tarifa)
        return query.all()
    
    def get_activas(self) -> List[Tarifa]:
        return self.db.query(Tarifa).filter(Tarifa.activa == True).all()
    
    def get_by_mercado(self, cod_mercado: str) -> List[Tarifa]:
        return self.db.query(Tarifa).filter(
            Tarifa.cod_mercado == cod_mercado,
            Tarifa.activa == True
        ).all()
    
    def crear(self, tarifa_data: Dict[str, Any]) -> Tarifa:
        tarifa = Tarifa(**tarifa_data)
        self.db.add(tarifa)
        self.db.commit()
        self.db.refresh(tarifa)
        return tarifa
    
    def actualizar(self, id_tarifa: int, datos: Dict[str, Any]) -> Optional[Tarifa]:
        tarifa = self.get_by_id(id_tarifa)
        if tarifa:
            for key, value in datos.items():
                setattr(tarifa, key, value)
            self.db.commit()
            self.db.refresh(tarifa)
        return tarifa
    
    def eliminar(self, id_tarifa: int) -> bool:
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
            query = query.filter(PeriodoTarifario.estado == 'PUBLICADA')
        return query.first()
    
    def get_periodos_by_tarifa(self, id_tarifa: int) -> List[PeriodoTarifario]:
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
        """
        Crea un nuevo período tarifario.
        El trigger `trg_periodo_config` resolverá `id_configuracion_horaria`
        si no viene especificado.
        """
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
        Si ya existe la versión PUBLICADA, la marca como SUPERADA
        y crea una nueva versión.
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
            logger.info(
                f"Nueva versión creada: {anio}-{mes} v{datos['numero_version']}"
            )
            return self.crear_periodo(datos)
        else:
            datos['numero_version'] = 1
            datos['id_tarifa'] = id_tarifa
            datos['anio'] = anio
            datos['mes'] = mes
            return self.crear_periodo(datos)
    
    # =====================================================
    # RESOLUCIÓN DE FRANJAS (nuevo método privado)
    # =====================================================
    
    def _resolver_id_franja(
        self,
        cod_comercializadora: str,
        codigo_franja: str,
        tipo_dia: str = 'TODOS'
    ) -> Optional[int]:
        """
        Resuelve el ID de franja desde el código ('F1', 'F2', ...).
        
        Args:
            cod_comercializadora: código de la comercializadora
            codigo_franja: 'F1', 'F2', ..., 'F8'
            tipo_dia: 'TODOS', 'LABORAL', etc.
            
        Returns:
            id_franja_horaria o None si no se encuentra
        """
        franja = (
            self.db.query(FranjaHoraria)
            .filter(
                FranjaHoraria.cod_comercializadora == cod_comercializadora,
                FranjaHoraria.codigo == codigo_franja,
                FranjaHoraria.tipo_dia == tipo_dia,
                FranjaHoraria.activo == True
            )
            .first()
        )
        
        if not franja:
            logger.warning(
                f"Franja no encontrada: {cod_comercializadora} / {codigo_franja}"
            )
            return None
        
        return franja.id_franja_horaria
    
    def _resolver_id_configuracion(
        self,
        cod_comercializadora: str,
        cod_mercado: str,
        cod_nivel: str,
        fecha: date
    ) -> Optional[int]:
        """
        Resuelve el ID de configuración horaria aplicable
        según comercializadora + mercado + nivel + fecha.
        """
        aplicable = (
            self.db.query(ConfiguracionAplicable)
            .filter(
                ConfiguracionAplicable.cod_comercializadora == cod_comercializadora,
                ConfiguracionAplicable.cod_mercado == cod_mercado,
                ConfiguracionAplicable.cod_nivel == cod_nivel,
                ConfiguracionAplicable.vigente_desde <= fecha,
                or_(
                    ConfiguracionAplicable.vigente_hasta.is_(None),
                    ConfiguracionAplicable.vigente_hasta >= fecha
                )
            )
            .first()
        )
        
        return aplicable.id_configuracion_horaria if aplicable else None
    
    # =====================================================
    # TARIFA VALOR (valores por franja o monomia)
    # =====================================================
    
    
    def get_valores_by_periodo(
        self,
        id_periodo_tarifario: int
    ) -> List[TarifaValor]:
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
        return (
            self.db.query(TarifaValor)
            .join(FranjaHoraria, TarifaValor.id_franja_horaria == FranjaHoraria.id_franja_horaria)
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
        return (
            self.db.query(TarifaValor)
            .filter(
                TarifaValor.id_periodo_tarifario == id_periodo_tarifario,
                TarifaValor.id_franja_horaria.is_(None)
            )
            .first()
        )
    
    def crear_valor(self, valor_data: Dict[str, Any]) -> TarifaValor:
        valor = TarifaValor(**valor_data)
        self.db.add(valor)
        self.db.commit()
        self.db.refresh(valor)
        return valor
    
    def crear_valores_batch(
        self,
        id_periodo_tarifario: int,
        valores: List[Dict[str, Any]],
        cod_comercializadora: str,
        id_configuracion_horaria: Optional[int] = None
    ) -> List[TarifaValor]:
        """
        Crea múltiples valores en lote.
        
        Cada elemento de `valores` debe contener:
            - codigo_franja: 'F1', 'F2', ...
            - valor: Decimal
            - unidad: 'COP/kWh'
        
        El método resuelve `id_franja_horaria` desde `codigo_franja`.
        Si `id_configuracion_horaria` es None, se asigna NULL a ambas FK.
        """
        creados = []
        
        for v in valores:
            codigo_franja = v.pop('codigo_franja', None)
            
            # Resolver id_franja_horaria
            id_franja_horaria = None
            if codigo_franja:
                id_franja_horaria = self._resolver_id_franja(
                    cod_comercializadora, codigo_franja
                )
                
                if not id_franja_horaria:
                    logger.warning(
                        f"Valor omitido por franja no resuelta: {codigo_franja}"
                    )
                    continue
                
            if id_franja_horaria is None and v['valor'] is not None:
                id_configuracion_horaria = None  # No hay franja, no hay configuración. Es monomia.
            
            # Si hay franja, debe haber configuración (constraint ck_tv_config_franja)
            if id_franja_horaria and not id_configuracion_horaria:
                logger.warning(
                    f"Valor omitido: franja {codigo_franja} sin configuración horaria"
                )
                continue
            
            valor = TarifaValor(
                id_periodo_tarifario=id_periodo_tarifario,
                id_configuracion_horaria=id_configuracion_horaria,
                id_franja_horaria=id_franja_horaria,
                valor=v['valor'],
                unidad=v.get('unidad', 'COP/kWh'),
            )
            self.db.add(valor)
            creados.append(valor)
        
        self.db.commit()
        
        for v in creados:
            self.db.refresh(v)
        
        logger.info(f"Creados {len(creados)} valores para período {id_periodo_tarifario}")
        return creados
    
    # =====================================================
    # VIEW DE TARIFA POR HORA (v_tarifa_hora)
    # =====================================================
    def get_precios_por_hora_desde_vista(
        self,
        id_periodo_tarifario: int
    ) -> list[VTarifaHora]:
        """
        Consulta los precios por hora usando la vista v_tarifa_hora.
        
        Ventaja: no requiere joins manuales entre tarifa_valor,
        configuracion_hora y franja_horaria.
        """
        return (
            self.db.query(VTarifaHora)
            .filter(VTarifaHora.id_periodo_tarifario == id_periodo_tarifario)
            .order_by(VTarifaHora.hora)
            .all()
        )
    
    def get_precio_hora_especifica(
        self,
        id_periodo_tarifario: int,
        hora: int
    ) -> VTarifaHora | None:
        """Obtiene el precio de una hora específica desde la vista."""
        return (
            self.db.query(VTarifaHora)
            .filter(
                VTarifaHora.id_periodo_tarifario == id_periodo_tarifario,
                VTarifaHora.hora == hora
            )
            .first()
        )
    
    # =====================================================
    # COMPONENTE VALOR MES (G, T, D, Cv, PR, R)
    # =====================================================
    
    def get_componentes_by_periodo(
        self,
        id_periodo_tarifario: int
    ) -> List[ComponenteValorMes]:
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
        """
        Crea los componentes de un período.
        Cada elemento debe contener:
            - cod_componente: 'Gm', 'Tm', 'Dm', 'Cm', 'PRm', 'Rm', 'COT', 'Cfmj'
            - valor: Decimal
        """
        creados = []
        
        for c in componentes:
            # Verificar si ya existe (por unique constraint)
            existente = self.get_componente(
                id_periodo_tarifario, c['cod_componente']
            )
            if existente:
                logger.debug(
                    f"Componente ya existe: {c['cod_componente']}"
                )
                continue
            
            comp = ComponenteValorMes(
                id_periodo_tarifario=id_periodo_tarifario,
                cod_componente=c['cod_componente'],
                valor=c['valor'],
            )
            self.db.add(comp)
            creados.append(comp)
        
        self.db.commit()
        
        for c in creados:
            self.db.refresh(c)
        
        logger.info(f"Creados {len(creados)} componentes para período {id_periodo_tarifario}")
        return creados
    
    # =====================================================
    # UPSERT COMPLETO (para extracción automática)
    # =====================================================
    
    def upsert_tarifa_completa(
        self,
        tarifa_tap: Dict[str, Any],
        force_new_version: bool = False
    ) -> Dict[str, Any]:
        """
        Inserta o actualiza una tarifa completa con detección de cambios y versionado.
        
        Args:
        tarifa_tap: estructura completa de la tarifa
        force_new_version: si True, siempre crea nueva versión (ignora comparación)
        
        Flujo:
            1. Buscar/crear Tarifa (cabecera)
            2. Buscar período PUBLICADO existente
            3. Si existe, marcar como SUPERADA y crear nueva versión
            4. Crear tarifa_valor resolviendo id_franja_horaria
            5. Crear componente_valor_mes
            
        Returns:
           Resumen con 'sin_cambios': True si se detectó que ya existía idéntica
        """
        resultado = {
            'tarifa_creada': False,
            'periodo_creado': False,
            'nueva_version': False,
            'sin_cambios': False,
            'valores_creados': 0,
            'componentes_creados': 0,
            'version': None,
        }
        
        tarifa_data = tarifa_tap['tarifa']
        periodo_data = tarifa_tap['periodo']
        valores_nuevos = tarifa_tap.get('valores', [])
        componentes_nuevos = tarifa_tap.get('componentes', [])
        
        try:
            # 1. Buscar o crear la Tarifa
            tarifa = self.get_by_codigo(tarifa_data['codigo_tarifa'])
            
            if not tarifa:
                tarifa = self.crear(tarifa_data)
                resultado['tarifa_creada'] = True
                logger.info(f"Tarifa creada: {tarifa.codigo_tarifa}")
            else:
                logger.info(f"Tarifa existente: {tarifa.codigo_tarifa}")
            
            # 2. Resolver id_configuracion_horaria
            #    (normalmente lo resuelve el trigger, pero lo calculamos aquí
            #     para usarlo al crear los tarifa_valor)
            id_configuracion = self._resolver_id_configuracion(
                tarifa_data['cod_comercializadora'],
                tarifa_data['cod_mercado'],
                tarifa_data['cod_nivel'],
                periodo_data['fecha_inicio']
            )
            
            if id_configuracion:
                logger.info(f"Configuración horaria resuelta: {id_configuracion}")
            else:
                logger.warning(
                    f"No se encontró configuración horaria aplicable para la tarifa {tarifa_data['codigo_tarifa']}. "
                    f"Los valores de franja no se podrán insertar."
                )
            
            # 3. Buscar período PUBLICADO existente
            periodo_existente = self.get_periodo(
                tarifa.id_tarifa,
                periodo_data['anio'],
                periodo_data['mes'],
                estado='PUBLICADA'
            )
            
            
            # 4. Si existe, COMPARAR contenido antes de crear nueva versión
       
            if periodo_existente and not force_new_version:
                sin_cambios = self._comparar_periodo(
                    periodo_existente,
                    periodo_data,
                    valores_nuevos,
                    componentes_nuevos,
                    tarifa_data['cod_comercializadora']
                )
                
                if sin_cambios:
                    logger.info(
                        f"Sin cambios detectados: {tarifa.codigo_tarifa} "
                        f"{periodo_data['anio']}-{periodo_data['mes']}. "
                        f"Se omite la creación de nueva versión."
                    )
                    resultado['sin_cambios'] = True
                    resultado['version'] = periodo_existente.numero_version
                    return resultado
                
            # 5. Hay cambios (o no existía): crear nueva versión
            
            if periodo_existente:
                # Marcar como SUPERADA y crear nueva versión
                periodo_existente.estado = 'SUPERADA'
                self.db.commit()
                
                nueva_version = periodo_existente.numero_version + 1
                periodo_data['id_tarifa'] = tarifa.id_tarifa
                periodo_data['numero_version'] = nueva_version
                
                # Si no viene id_configuracion_horaria, se lo pasamos
                if 'id_configuracion_horaria' not in periodo_data and id_configuracion:
                    periodo_data['id_configuracion_horaria'] = id_configuracion
                
                periodo = self.crear_periodo(periodo_data)
                resultado['periodo_creado'] = True
                resultado['nueva_version'] = True
                resultado['version'] = nueva_version
                
                logger.info(
                    f"Nueva versión creada: {periodo.anio}-{periodo.mes} "
                    f"v{nueva_version}"
                )
            else:
                # Primera versión
                periodo_data['id_tarifa'] = tarifa.id_tarifa
                periodo_data['numero_version'] = 1
                
                if 'id_configuracion_horaria' not in periodo_data and id_configuracion:
                    periodo_data['id_configuracion_horaria'] = id_configuracion
                
                periodo = self.crear_periodo(periodo_data)
                resultado['periodo_creado'] = True
                resultado['version'] = 1
                
                logger.info(f"Período creado: {periodo.anio}-{periodo.mes} v1")
            
            # 6. Crear tarifa_valor (solo si hay franjas)
            if valores_nuevos and id_configuracion:
                valores_creados = self.crear_valores_batch(
                    id_periodo_tarifario=periodo.id_periodo_tarifario,
                    valores=valores_nuevos,
                    cod_comercializadora=tarifa_data['cod_comercializadora'],
                    id_configuracion_horaria=id_configuracion,
                )
                resultado['valores_creados'] = len(valores_creados)
            elif valores_nuevos and not id_configuracion:
                logger.warning(
                    "Valores no insertados: falta configuración horaria. "
                    "Cargue `configuracion_aplicable` para este mercado+nivel."
                )
            
            # 5. Crear componente_valor_mes
            if componentes_nuevos:
                comps_creados = self.crear_componentes_batch(
                    id_periodo_tarifario=periodo.id_periodo_tarifario,
                    componentes=componentes_nuevos,
                )
                resultado['componentes_creados'] = len(comps_creados)
            
            self.db.commit()
            logger.info(f"Upsert completo: {resultado}")
            return resultado
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error en upsert_tarifa_completa: {e}")
            raise
    
    def _comparar_periodo(
        self,
        periodo_existente: PeriodoTarifario,
        periodo_nuevo: Dict[str, Any],
        valores_nuevos: List[Dict[str, Any]],
        componentes_nuevos: List[Dict[str, Any]],
        cod_comercializadora: str
    ) -> bool:
        """
        Compara el período existente con los datos nuevos.
        
        Returns:
            True si son idénticos (sin cambios)
            False si hay diferencias
        """
        # 1. Comparar metadata del período
        if periodo_existente.fecha_inicio != periodo_nuevo['fecha_inicio']:
            logger.debug(f"Diferencia en fecha_inicio: {periodo_existente.fecha_inicio} != {periodo_nuevo['fecha_inicio']}")
            return False
        
        if periodo_existente.fecha_fin != periodo_nuevo['fecha_fin']:
            logger.debug(f"Diferencia en fecha_fin: {periodo_existente.fecha_fin} != {periodo_nuevo['fecha_fin']}")
            return False
        
        # 2. Comparar valores por franja
        valores_existentes = self.get_valores_by_periodo(
            periodo_existente.id_periodo_tarifario
        )
        
        if not self._comparar_valores(
            valores_existentes, valores_nuevos, cod_comercializadora
        ):
            logger.debug(f"Diferencia en valores por franja")
            return False
        
        # 3. Comparar componentes
        componentes_existentes = self.get_componentes_by_periodo(
            periodo_existente.id_periodo_tarifario
        )
        
        if not self._comparar_componentes(componentes_existentes, componentes_nuevos):
            logger.debug(f"Diferencia en componentes")
            return False
        
        # 4. Todo igual
        return True


    def _comparar_valores(
        self,
        valores_existentes: List[TarifaValor],
        valores_nuevos: List[Dict[str, Any]],
        cod_comercializadora: str,
        tolerancia: Decimal = Decimal('0.0001')
    ) -> bool:
        """
        Compara listas de valores por franja.
        Usa tolerancia para evitar problemas de punto flotante.
        """
        # Construir mapa de valores existentes: {codigo_franja: valor}
        mapa_existentes = {}
        for v in valores_existentes:
            if v.id_franja_horaria:
                franja = self.db.query(FranjaHoraria).filter(
                    FranjaHoraria.id_franja_horaria == v.id_franja_horaria
                ).first()
                if franja:
                    mapa_existentes[franja.codigo] = Decimal(str(v.valor))
        
        # Construir mapa de valores nuevos: {codigo_franja: valor}
        mapa_nuevos = {}
        for v in valores_nuevos:
            codigo = v.get('codigo_franja')
            if codigo:
                mapa_nuevos[codigo] = Decimal(str(v['valor']))
        
        # Comparar: misma cantidad de franjas
        if set(mapa_existentes.keys()) != set(mapa_nuevos.keys()):
            logger.debug(
                f"Franjas diferentes: "
                f"existentes={set(mapa_existentes.keys())}, "
                f"nuevos={set(mapa_nuevos.keys())}"
            )
            return False
        
        # Comparar valores con tolerancia
        for codigo in mapa_existentes:
            diff = abs(mapa_existentes[codigo] - mapa_nuevos[codigo])
            if diff > tolerancia:
                logger.debug(
                    f"Diferencia en franja {codigo}: "
                    f"{mapa_existentes[codigo]} != {mapa_nuevos[codigo]}"
                )
                return False
        
        return True


    def _comparar_componentes(
        self,
        componentes_existentes: List[ComponenteValorMes],
        componentes_nuevos: List[Dict[str, Any]],
        tolerancia: Decimal = Decimal('0.0001')
    ) -> bool:
        """Compara listas de componentes."""
        # Mapa de existentes: {cod_componente: valor}
        mapa_existentes = {
            c.cod_componente: Decimal(str(c.valor))
            for c in componentes_existentes
        }
        
        # Mapa de nuevos: {cod_componente: valor}
        mapa_nuevos = {
            c['cod_componente']: Decimal(str(c['valor']))
            for c in componentes_nuevos
        }
        
        # Misma cantidad
        if set(mapa_existentes.keys()) != set(mapa_nuevos.keys()):
            logger.debug(
                f"Componentes diferentes: "
                f"existentes={set(mapa_existentes.keys())}, "
                f"nuevos={set(mapa_nuevos.keys())}"
            )
            return False
        
        # Comparar valores con tolerancia
        for codigo in mapa_existentes:
            diff = abs(mapa_existentes[codigo] - mapa_nuevos[codigo])
            if diff > tolerancia:
                logger.debug(
                    f"Diferencia en componente {codigo}: "
                    f"{mapa_existentes[codigo]} != {mapa_nuevos[codigo]}"
                )
                return False
        
        return True
    
    # =====================================================
    # CONSULTAS PARA EL DASHBOARD
    # =====================================================
    
    
    def get_tarifa_por_clasificacion(
        self,
        cod_comercializadora: str,
        cod_mercado: str,
        cod_nivel: str,
        cod_tipo_tarifa: str
    ) -> Optional[Tarifa]:
        """
        Obtiene la tarifa que coincide con la clasificación completa del cliente.
        
        Args:
            cod_comercializadora: código de la comercializadora
            cod_mercado: código del mercado
            cod_nivel: código del nivel de tensión
            cod_tipo_tarifa: 'A', 'B', 'C', 'D' (determinado por reglas CREG)
            fecha: fecha de vigencia
        
        Returns:
            Tarifa única o None si no existe
        """
        return (
            self.db.query(Tarifa)
            .filter(
                Tarifa.cod_comercializadora == cod_comercializadora,
                Tarifa.cod_mercado == cod_mercado,
                Tarifa.cod_nivel == cod_nivel,
                Tarifa.cod_tipo_tarifa == cod_tipo_tarifa,
                Tarifa.activa == True
            )
            .order_by(desc(Tarifa.fecha_registro))
            .first()
        )
    
    
    
    def get_tarifa_vigente_completa(
        self,
        id_cliente: int,
        fecha: date,
        cod_tipo_tarifa: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene la tarifa vigente completa para un cliente.
        
        Args:
            id_cliente: ID del cliente
            fecha: fecha de consulta
            consumo_mensual_kwh: consumo del mes (para determinar tipo de tarifa)
                                Si es None, usa el CS del cliente
        """
        
        # 1. Obtener el cliente
        cliente = self.db.query(Cliente).filter(
            Cliente.id_cliente == id_cliente
        ).first()
        
        print(f"Cliente encontrado: {cliente}")
        
        if not cliente:
            return None
        
        
        # 3. Buscar la tarifa que coincide con la clasificación
        tarifa = self.get_tarifa_por_clasificacion(
            cod_comercializadora=cliente.cod_comercializadora,
            cod_mercado=cliente.cod_mercado,
            cod_nivel=cliente.cod_nivel,
            cod_tipo_tarifa=cod_tipo_tarifa
        )
        
        logger.info(f"Tarifa encontrada: {tarifa}")
        
        if not tarifa:
            return None
        
        # 4. Obtener período vigente
        periodo = self.get_periodo_vigente(tarifa.id_tarifa, fecha)
        if not periodo:
            return None
        
        # 5. Obtener valores y componentes
        precios = self.get_precios_por_hora_desde_vista(periodo.id_periodo_tarifario)
        componentes = self.get_componentes_by_periodo(periodo.id_periodo_tarifario)
        
        # Separar valores por hora de la monomia (hora IS NULL)
        valores_hora = [p for p in precios if p.hora is not None]
        monomias = [p for p in precios if p.hora is None]

        # Formatear valores por hora
        valores = [
            {   
                'hora': p.hora,
                'codigo_franja': p.franja,
                'tipo_hora': p.tipo_hora,
                'valor': float(p.valor),
                'unidad': p.unidad or 'COP/kWh',
            }
            for p in valores_hora
        ]

        # Extraer la monomia (si existe)
        monomia = None
        if monomias:
            m = monomias[0]
            monomia = {
                'valor': float(m.valor),
                'unidad': m.unidad or 'COP/kWh',
                "tipo": "CU"
            }

        
        
        return {
            'id_cliente': id_cliente,
            'tarifa': tarifa,
            'periodo': periodo,
            'monomia': monomia,
            'valores': valores,
            'componentes': componentes,
        }
        
    
    def get_precios_dia(
        self,
        id_cliente: int,
        fecha: date,
        cod_tipo_tarifa: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene los precios de las 24 horas del día para un cliente
        consultando la vista v_tarifa_hora.
        
        Returns:
            {
                'id_cliente': int,
                'fecha': date,
                'precios': list[dict],   # 24 elementos (o lista vacía si MONOMIA)
                'monomia': dict | None,  # Solo si existe monomia
            }
        """
        # Respuesta base para casos sin datos
        respuesta_vacia = {
            'id_cliente': id_cliente,
            'fecha': fecha,
            'precios': [],
            'monomia': None,
        }
        
        # 1. Obtener tarifa vigente completa
        tarifa_data = self.get_tarifa_vigente_completa(id_cliente, fecha, cod_tipo_tarifa)
        if not tarifa_data:
            logger.warning(f"Sin tarifa vigente para cliente Id:{id_cliente}")
            return respuesta_vacia
        
        # 2. Consultar la vista v_tarifa_hora (1 sola query)
        filas_vista = (
            self.db.query(VTarifaHora)
            .filter(
                VTarifaHora.id_periodo_tarifario == tarifa_data['periodo'].id_periodo_tarifario
            )
            .all()
        )
        
        if not filas_vista:
            logger.warning(
                f"Sin filas en v_tarifa_hora para periodo "
                f"{tarifa_data['periodo'].id_periodo_tarifario}"
            )
            return respuesta_vacia
        
        # 3. Separar filas por hora vs monomia
        precios_por_hora = {f.hora: f for f in filas_vista if f.hora is not None}
        monomia_row = next((f for f in filas_vista if f.hora is None), None)
        
        # 4. Construir precios de las 24 horas
        precios = []
        for hora in range(1, 25):
            fila = precios_por_hora.get(hora)
            
            if not fila:
                precios.append({
                    'hora': hora,
                    'codigo_franja': None,
                    'tipo_hora': None,
                    'precio': None,
                    'unidad': None,
                })
                continue
            
            precios.append({
                'hora': hora,
                'codigo_franja': fila.franja,
                'tipo_hora': fila.tipo_hora,
                'precio': float(fila.valor),
                'unidad': fila.unidad or 'COP/kWh',
            })
        
        # 5. Extraer monomia (si existe)
        monomia = {
            'valor': float(monomia_row.valor),
            'unidad': monomia_row.unidad or 'COP/kWh',
            'tipo': 'CU',
        }
        
        return {
            'id_cliente': id_cliente,
            'fecha': fecha,
            'precios': precios,
            'monomia': monomia,
        }
    
    def get_precio_por_hora(
        self,
        id_cliente: int,
        fecha: date,
        hora: int,
        cod_tipo_tarifa: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene el precio para una hora específica.
        Reutiliza `get_precios_dia` y filtra.
        """
        precios = self.get_precios_dia(id_cliente, fecha, cod_tipo_tarifa).get('precios')
        return next((p for p in precios if p['hora'] == hora), None)
    
    
