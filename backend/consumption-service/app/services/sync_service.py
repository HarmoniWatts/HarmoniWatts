from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import uuid4
from loguru import logger
from fastapi import HTTPException

from app.services.external_client import InelcaClient
from app.services.external_client_ener import EnertotalClient
from app.services.meter_mapper import MeterMapper
from app.repositories.sync_repository import SyncRepository
from app.services.ports import ViviendaResolverPort, TarifaResolverPort
from app.config import settings


class SyncService:
    """
    Orquesta la sincronización desde INELCA a MongoDB.
    
    Dependencias inyectadas:
        - vivienda_resolver: resuelve meter_no → id_vivienda
        - tarifa_resolver: resuelve tarifa vigente por timestamp
    """
    
    def __init__(
        self,
        vivienda_resolver: ViviendaResolverPort,
        tarifa_resolver: TarifaResolverPort,
        inelca_client: Optional[InelcaClient] = None,
        retail_client: Optional[EnertotalClient] = None,
        mapper: Optional[MeterMapper] = None,
        repo: Optional[SyncRepository] = None,
    ):
        self.vivienda_resolver = vivienda_resolver
        self.tarifa_resolver = tarifa_resolver
        self.client = inelca_client or InelcaClient()
        self.client_enertotal = retail_client or EnertotalClient()
        self.mapper = mapper or MeterMapper()
        self.repo = repo or SyncRepository()
        
    
    # =====================================================
    # SINCRONIZACIÓN POR NUMERO DE CONTRATO
    # =====================================================
    
    async def sincronizar_contrato(
        self,
        no_contrato: int,
        cod_retail: str,
        id_cliente: Optional[int] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ):
        """
        Sincroniza el medidor de un contrato o cuenta en un rango de fechas.
        
        - Ejecuta la sincronización (en background o síncrona según config).
        """
        id_sincronizacion = f"sync_{uuid4().hex[:8]}"
        inicio = datetime.utcnow()
        
        await self.repo.crear_sync_estado(
            id_sincronizacion=id_sincronizacion,
            no_contrato=no_contrato,
            cod_comercializadora=cod_retail,
            meter_no="",
            id_cliente=id_cliente,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        
        
        await self.repo.actualizar_sync_estado(
            id_sincronizacion, estado="en_proceso"
        )
        
        # Las lecturas se identifican por (no_contrato, cod_comercializadora);
        # la vivienda no hace falta para consultarlas.
        id_vivienda = None
        
        if cod_retail == "ENERTOTAL":
            self.client_retail = self.client_enertotal
            
        conteo = await self.client_retail.contar_lecturas(
            no_account=str(no_contrato),
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        logger.info(
            f"Sincronizando {no_contrato}: {conteo['total']} registros "
            f"en {conteo['totalPages']} páginas"
        )
        
        # 3. Iterar y procesar
        batch: List[Dict[str, Any]] = []
        total_obtenidos = 0
        total_insertados = 0
        total_actualizados = 0
        errores: List[str] = []
        
        # Cache de tarifas por (id_cliente, fecha) para evitar consultas repetidas
        tarifa_cache: Dict[str, Optional[Dict]] = {}
        # Se toma de las lecturas; queda vacío si la comercializadora no devuelve ninguna
        meter_no = ""
        
        async for lectura in self.client_retail.iter_meter_readings(
            no_account=str(no_contrato), fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
        ):
            total_obtenidos += 1
            #logger.info(f'lectura:{lectura}')
            timestamp = self.mapper._parse_timestamp(lectura["DATE_TIME"])
            if not timestamp:
                errores.append(
                    f"Timestamp inválido: {lectura['DATE_TIME']}"
                )
                continue
            
            #Resolser meter_no
            meter_no = lectura["METER_NO"]
            
            # Resolver tarifa (con cache por cliente+fecha)
            consumo_mensual = lectura["IMPORT_KWH_MENSUAL"]
            tarifa_data = None
            if id_cliente is not None:
                cache_key = f"{id_cliente}:{timestamp.strftime('%Y-%m-%d %H')}"
                if cache_key not in tarifa_cache:
                    tarifa_cache[cache_key] = await self.tarifa_resolver.resolver(
                        id_cliente=id_cliente,
                        timestamp=timestamp,
                        consumo_mensual=consumo_mensual
                    )
                tarifa_data = tarifa_cache[cache_key]
            #logger.debug(f'Tarifa: {tarifa_data}')
            # Transformar
            doc = self.mapper.transformar(
                lectura,
                no_contrato=no_contrato,
                cod_comercializadora=cod_retail,
                id_cliente=id_cliente,
                tarifa_data=tarifa_data,
            )
            # logger.debug(f'Doc: {doc}')
            
            if doc:
                batch.append(doc)
            
            # Procesar lote
            if len(batch) >= settings.SYNC_BATCH_SIZE:
                resultado = await self.repo.upsert_consumos_batch(batch)
                total_insertados += resultado["insertados"]
                total_actualizados += resultado["actualizados"]
                batch = []
        
        # Último lote
        if batch:
            resultado = await self.repo.upsert_consumos_batch(batch)
            total_insertados += resultado["insertados"]
            total_actualizados += resultado["actualizados"]
        
        # Finalizar
        duracion = int((datetime.utcnow() - inicio).total_seconds())
        await self.repo.actualizar_sync_estado(
            id_sincronizacion,
            estado="completado",
            registros_obtenidos=total_obtenidos,
            registros_insertados=total_insertados,
            registros_duplicados=total_actualizados,
            errores=errores,
            finalizada_en=datetime.utcnow(),
        )
        
        await self.repo.registrar_historial(
            id_sincronizacion=id_sincronizacion,
            no_contrato=no_contrato,
            cod_comercializadora=cod_retail,
            meter_no=meter_no,
            estado="completado",
            registros_obtenidos=total_obtenidos,
            registros_insertados=total_insertados,
            registros_duplicados=total_actualizados,
            errores=errores,
            duracion_seg=duracion,
        )
        
        return {
            "id_sincronizacion": id_sincronizacion,
            "estado": "completado",
            "no_contrato": no_contrato,
            "cod_comercializadora": cod_retail,
            "id_cliente": id_cliente,
            "id_vivienda": id_vivienda,
            "serie_medidor": meter_no,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        }
    
    # =====================================================
    # SINCRONIZACIÓN POR VIVIENDA
    # =====================================================
    
    async def sincronizar_vivienda(
        self,
        id_vivienda: int,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ):
        """
        Sincroniza todos los medidores de una vivienda en un rango de fechas.
        
        - Valida que la vivienda pertenezca al cliente autenticado.
        - Itera sobre los medidores de la vivienda.
        - Ejecuta la sincronización (en background o síncrona según config).
        """
        # 1. Validar que la vivienda pertenece al cliente
        # (el user-service valida esto; aquí confiamos en el JWT)
        # TODO: si el user-service expone /viviendas/{id}, validar aquí
        # if not await user_service.cliente_tiene_vivienda(cliente_autenticado.id_cliente, id_vivienda):
        #     raise HTTPException(403, "No autorizado")
        
        # 2. Obtener los medidores de la vivienda
        medidores = await self.vivienda_resolver.obtener_por_vivienda(id_vivienda)
        
        if not medidores:
            raise HTTPException(
                status_code=404,
                detail=f"La vivienda {id_vivienda} no tiene medidores asociados",
            )
        
        # 3. Disparar sincronización (síncrona por ahora)
        resultados = []
        for meter_no in medidores:
            resultado = await self.sincronizar_medidor(
                meter_no=meter_no,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                id_vivienda=id_vivienda,
            )
            resultados.append(resultado)
        
        # 4. Consolidar respuesta
        exitosos = [r for r in resultados if r["estado"] == "completado"]
        fallidos = [r for r in resultados if r["estado"] == "error"]
        
        return {
            "id_sincronizacion": f"sync_v{id_vivienda}_{len(resultados)}",
            "estado": "completado" if not fallidos else "parcial",
            "id_vivienda": id_vivienda,
            "medidores": medidores,
            "total_medidores": len(medidores),
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "mensaje" : (
                f"Sincronizados {len(exitosos)}/{len(medidores)} medidores. "
                f"{len(fallidos)} fallidos."
            ),
            "detalles": resultados, 
        }
    
    
    # =====================================================
    # SINCRONIZACIÓN POR CLIENTE
    # =====================================================
    async def sincronizar_cliente(
        self,
        id_cliente: int,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ):
        """
        Sincroniza todos los medidores de una cliente en un rango de fechas.
        
        - Valida que la cliente pertenezca al cliente autenticado.
        - Itera sobre los medidores de la cliente.
        - Ejecuta la sincronización (en background o síncrona según config).
        """
        # 1. Validar que la cliente pertenece al cliente
        # (el user-service valida esto; aquí confiamos en el JWT)
        # TODO: si el user-service expone /viviendas/{id}, validar aquí
        # if not await user_service.cliente_tiene_vivienda(cliente_autenticado.id_cliente, id_vivienda):
        #     raise HTTPException(403, "No autorizado")
        
        # 1. Resolver id_vivienda. Mientras no exista un servicio que relacione
        #    clientes y viviendas se asume una vivienda por cliente con el mismo
        #    id (el mismo supuesto que hace TarifaResolverHTTP).
        id_vivienda = id_cliente

        # 2. Obtener los medidores del cliente
        medidores = await self.vivienda_resolver.obtener_por_vivienda(id_vivienda)
        
        if not medidores:
            raise HTTPException(
                status_code=404,
                detail=f"El cliente {id_cliente} no tiene medidores asociados",
            )
        
        # 3. Disparar sincronización (síncrona por ahora)
        resultados = []
        for meter_no in medidores:
            resultado = await self.sincronizar_medidor(
                meter_no=meter_no,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                id_vivienda=id_vivienda,
            )
            resultados.append(resultado)
        
        # 4. Consolidar respuesta
        exitosos = [r for r in resultados if r["estado"] == "completado"]
        fallidos = [r for r in resultados if r["estado"] == "error"]
        
        return {
            "id_sincronizacion": f"sync_v{id_vivienda}_{len(resultados)}",
            "estado": "completado" if not fallidos else "parcial",
            "id_cliente": id_cliente,
            "id_vivienda": id_vivienda,
            "medidores": medidores,
            "total_medidores": len(medidores),
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "mensaje" : (
                f"Sincronizados {len(exitosos)}/{len(medidores)} medidores. "
                f"{len(fallidos)} fallidos."
            ),
            "detalles": resultados, 
        }
            
    
    # =====================================================
    # SINCRONIZACIÓN POR MEDIDOR
    # =====================================================
    async def sincronizar_medidor(
        self,
        meter_no: str,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        id_vivienda: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Sincroniza todas las lecturas de un medidor."""
        id_sincronizacion = f"sync_{uuid4().hex[:8]}"
        inicio = datetime.utcnow()
        
        await self.repo.crear_sync_estado(
            id_sincronizacion=id_sincronizacion,
            meter_no=meter_no,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        
        
        await self.repo.actualizar_sync_estado(
            id_sincronizacion, estado="en_proceso"
        )
        
        # 1. Resolver id_vivienda (si no viene)
        if id_vivienda is None:
            id_vivienda = await self.vivienda_resolver.resolver(meter_no)
            if id_vivienda is None:
                logger.warning(
                    f"No se pudo resolver vivienda para medidor {meter_no}. "
                    f"Se guardarán las lecturas con id_vivienda=null."
                )
        
        # 2. Contar registros
        conteo = await self.client.contar_lecturas(
            meter_no, fecha_inicio, fecha_fin
        )
        logger.info(
            f"Sincronizando {meter_no}: {conteo['total']} registros "
            f"en {conteo['totalPages']} páginas"
        )
        
        # 3. Iterar y procesar
        batch: List[Dict[str, Any]] = []
        total_obtenidos = 0
        total_insertados = 0
        total_actualizados = 0
        errores: List[str] = []
        
        # Cache de tarifas por (id_cliente, fecha) para evitar consultas repetidas
        tarifa_cache: Dict[str, Optional[Dict]] = {}
        
        async for lectura in self.client.iter_meter_readings(
            meter_no, fecha_inicio, fecha_fin
        ):
            total_obtenidos += 1
            #logger.info(f'lectura:{lectura}')
            timestamp = self.mapper._parse_timestamp(lectura["DATE_TIME"])
            if not timestamp:
                errores.append(
                    f"Timestamp inválido: {lectura['DATE_TIME']}"
                )
                continue
            
            # Resolver tarifa (con cache por cliente+fecha)
            consumo_mensual = lectura["IMPORT_KWH_MENSUAL"]
            tarifa_data = None
            if id_vivienda is not None:
                cache_key = f"{id_vivienda}:{timestamp.strftime('%Y-%m-%d %H')}"
                if cache_key not in tarifa_cache:
                    tarifa_cache[cache_key] = await self.tarifa_resolver.resolver(
                        id_cliente=id_vivienda,
                        timestamp=timestamp,
                        consumo_mensual=consumo_mensual
                    )
                tarifa_data = tarifa_cache[cache_key]
            #logger.debug(f'Tarifa: {tarifa_data}')
            # Transformar
            doc = self.mapper.transformar(
                lectura,
                id_vivienda=id_vivienda,
                tarifa_data=tarifa_data,
            )
            # logger.debug(f'Doc: {doc}')
            
            if doc:
                batch.append(doc)
            
            # Procesar lote
            if len(batch) >= settings.SYNC_BATCH_SIZE:
                resultado = await self.repo.upsert_consumos_batch(batch)
                total_insertados += resultado["insertados"]
                total_actualizados += resultado["actualizados"]
                batch = []
        
        # Último lote
        if batch:
            resultado = await self.repo.upsert_consumos_batch(batch)
            total_insertados += resultado["insertados"]
            total_actualizados += resultado["actualizados"]
        
        # Finalizar
        duracion = int((datetime.utcnow() - inicio).total_seconds())
        await self.repo.actualizar_sync_estado(
            id_sincronizacion,
            estado="completado",
            registros_obtenidos=total_obtenidos,
            registros_insertados=total_insertados,
            registros_duplicados=total_actualizados,
            errores=errores,
            finalizada_en=datetime.utcnow(),
        )
        
        await self.repo.registrar_historial(
            id_sincronizacion=id_sincronizacion,
            no_contrato=None,
            cod_comercializadora=None,
            meter_no=meter_no,
            estado="completado",
            registros_obtenidos=total_obtenidos,
            registros_insertados=total_insertados,
            registros_duplicados=total_actualizados,
            errores=errores,
            duracion_seg=duracion,
        )
        
        return {
            "id_sincronizacion": id_sincronizacion,
            "estado": "completado",
            "meter_no": meter_no,
            "id_vivienda": id_vivienda,
            "registros_obtenidos": total_obtenidos,
            "registros_insertados": total_insertados,
            "registros_duplicados": total_actualizados,
            "errores": errores,
            "duracion_seg": duracion,
        }
        
    # =====================================================
    # SINCRONIZACIÓN MASIVA
    # =====================================================
    
    async def sincronizar_todos(
        self,
        medidores: List[Dict[str, Any]],
        horas_atras: int = 24,
    ) -> Dict[str, Any]:
        fecha_fin = date.today()
        fecha_inicio = fecha_fin - timedelta(days=horas_atras // 24 or 1)
        
        resultados = []
        for medidor in medidores:
            resultado = await self.sincronizar_medidor(
                meter_no=medidor["meter_no"],
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                id_vivienda=medidor.get("id_vivienda"),
            )
            resultados.append(resultado)
        
        exitosos = [r for r in resultados if r["estado"] == "completado"]
        fallidos = [r for r in resultados if r["estado"] == "error"]
        
        return {
            "total": len(medidores),
            "exitosos": len(exitosos),
            "fallidos": len(fallidos),
            "registros_insertados": sum(
                r.get("registros_insertados", 0) for r in exitosos
            ),
            "detalles": resultados,
        }