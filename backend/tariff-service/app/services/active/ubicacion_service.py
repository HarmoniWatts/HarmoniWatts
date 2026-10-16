# app/services/active/ubicacion_service.py

from datetime import date
from types import SimpleNamespace
from typing import Optional, Dict, Any, List, Tuple
from loguru import logger
from sqlalchemy.orm import Session

from app.models.postgres.mercado_red import MercadoRed
from app.models.postgres.mercado_zona import MercadoZona
from app.models.postgres.operador_red import OperadorRed
from app.models.postgres.periodo_tarifario import PeriodoTarifario
from app.models.postgres.tarifa import Tarifa
from app.models.postgres.zona_geografica import ZonaGeografica
from app.repositories.postgres.tarifa_repository import TarifaRepository
from app.services.business.tarifa_selector import TarifaSelector


class UbicacionNoEncontrada(Exception):
    """La combinación municipio + mercado no existe en mercado_zona."""


class UbicacionTarifaService:
    """
    Tarifas de una vivienda a partir de su ubicación (municipio + mercado) y su
    estrato, sin requerir un registro en `cliente`.

    Reglas:
        - La vivienda es residencial ('R'); el consumo de subsistencia depende
          de la altura del municipio (CREG: 130 kWh/mes >= 1000 m, 173 kWh/mes < 1000 m).
        - El tipo de tarifa (A, B, C, D) lo decide TarifaSelector.
        - Si la comercializadora no publicó ese tipo / nivel para el mercado, se
          usa la alternativa más cercana y se informa en `seleccion.nota`.
    """

    COMERCIALIZADORA = 'ENERTOTAL'
    # Residencial: nivel 1 propiedad del OR y, en su defecto, los niveles 1 compartidos
    NIVELES_RESIDENCIALES = ('N1_1', 'N1_2_1_3', 'N1_2', 'N1_2_50')
    ALTURA_CS = 1000

    def __init__(self, db: Session, repo: TarifaRepository, selector: TarifaSelector):
        self.db = db
        self.repo = repo
        self.selector = selector

    # =====================================================
    # CATÁLOGO DE CIUDADES
    # =====================================================

    def listar_ciudades(self) -> List[Dict[str, Any]]:
        filas = self._query_ciudades().order_by(ZonaGeografica.municipio, MercadoRed.nombre_mercado).all()
        return [self._ciudad_dict(*f) for f in filas]

    # =====================================================
    # TARIFA VIGENTE (24 h + componentes)
    # =====================================================

    def obtener_tarifa(
        self,
        id_zona: int,
        cod_mercado: str,
        estrato: int,
        fecha: Optional[date] = None,
        consumo_mensual_kwh: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        fecha_consulta = fecha or date.today()
        ciudad = self._get_ciudad(id_zona, cod_mercado)
        seleccion, tarifa = self._seleccionar_tarifa(ciudad, estrato, consumo_mensual_kwh)
        if tarifa is None:
            return None

        periodo = self.repo.get_periodo_vigente(tarifa.id_tarifa, fecha_consulta)
        if periodo is None:
            logger.warning(f"Sin período publicado para {tarifa.codigo_tarifa} en {fecha_consulta}")
            return None

        precios, monomia = self._precios_24(periodo.id_periodo_tarifario)
        componentes = self.repo.get_componentes_by_periodo(periodo.id_periodo_tarifario)

        return {
            'fecha': fecha_consulta,
            'ciudad': ciudad,
            'seleccion': seleccion,
            'tarifa': tarifa,
            'periodo': periodo,
            'monomia': monomia,
            'precios': precios,
            'componentes': [
                {'cod_componente': c.cod_componente, 'valor': float(c.valor)}
                for c in componentes
            ],
        }

    # =====================================================
    # CALENDARIO ANUAL
    # =====================================================

    def obtener_calendario(
        self,
        id_zona: int,
        cod_mercado: str,
        estrato: int,
        anio: int,
        consumo_mensual_kwh: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        ciudad = self._get_ciudad(id_zona, cod_mercado)
        seleccion, tarifa = self._seleccionar_tarifa(ciudad, estrato, consumo_mensual_kwh)
        if tarifa is None:
            return None

        periodos = (
            self.db.query(PeriodoTarifario)
            .filter(
                PeriodoTarifario.id_tarifa == tarifa.id_tarifa,
                PeriodoTarifario.anio == anio,
            )
            .all()
        )

        meses = []
        for mes in range(1, 13):
            del_mes = [p for p in periodos if p.mes == mes]
            publicado = next((p for p in del_mes if p.estado == 'PUBLICADA'), None)
            if publicado is None:
                meses.append({'mes': mes, 'publicado': False, 'versiones': len(del_mes)})
                continue

            precios, monomia = self._precios_24(publicado.id_periodo_tarifario)
            valores = [p['precio'] for p in precios if p['precio'] is not None]
            meses.append({
                'mes': mes,
                'publicado': True,
                'numero_version': publicado.numero_version,
                'versiones': len(del_mes),
                'fecha_publicacion': publicado.fecha_publicacion,
                'precio_min': min(valores) if valores else None,
                'precio_max': max(valores) if valores else None,
                'precio_promedio': round(sum(valores) / len(valores), 2) if valores else None,
                'monomia': monomia['valor'] if monomia else None,
            })

        return {
            'anio': anio,
            'ciudad': ciudad,
            'seleccion': seleccion,
            'codigo_tarifa': tarifa.codigo_tarifa,
            'meses': meses,
        }

    # =====================================================
    # INTERNOS
    # =====================================================

    def _query_ciudades(self):
        return (
            self.db.query(ZonaGeografica, MercadoRed, OperadorRed)
            .join(MercadoZona, MercadoZona.id_zona == ZonaGeografica.id_zona)
            .join(MercadoRed, MercadoRed.cod_mercado == MercadoZona.cod_mercado)
            .outerjoin(OperadorRed, OperadorRed.cod_or == MercadoRed.cod_or)
        )

    @staticmethod
    def _ciudad_dict(zona: ZonaGeografica, mercado: MercadoRed, operador: Optional[OperadorRed]) -> Dict[str, Any]:
        return {
            'id_zona': zona.id_zona,
            'cod_mercado': mercado.cod_mercado,
            'municipio': zona.municipio or zona.nombre_zona,
            'departamento': zona.departamento,
            'altura': zona.altura,
            'nombre_mercado': mercado.nombre_mercado,
            'operador_red': operador.nombre_operador if operador else None,
        }

    def _get_ciudad(self, id_zona: int, cod_mercado: str) -> Dict[str, Any]:
        fila = (
            self._query_ciudades()
            .filter(ZonaGeografica.id_zona == id_zona, MercadoRed.cod_mercado == cod_mercado)
            .first()
        )
        if fila is None:
            raise UbicacionNoEncontrada(f"Ubicación no válida: zona {id_zona}, mercado {cod_mercado}")
        return self._ciudad_dict(*fila)

    def _seleccionar_tarifa(
        self,
        ciudad: Dict[str, Any],
        estrato: int,
        consumo_mensual_kwh: Optional[float],
    ) -> Tuple[Dict[str, Any], Optional[Tarifa]]:
        altura = ciudad['altura'] or 0
        cs_kwh = 130 if altura >= self.ALTURA_CS else 173
        vivienda = SimpleNamespace(cod_tipo_cliente='R', estrato=estrato, cs_kwh_mes=cs_kwh)
        tipo_solicitado = self.selector.seleccionar_tipo_tarifa(
            vivienda, consumo_mensual_kwh=consumo_mensual_kwh
        )

        tipos = [tipo_solicitado] + (['A'] if tipo_solicitado != 'A' else [])
        for tipo in tipos:
            for nivel in self.NIVELES_RESIDENCIALES:
                tarifa = self.repo.get_tarifa_por_clasificacion(
                    cod_comercializadora=self.COMERCIALIZADORA,
                    cod_mercado=ciudad['cod_mercado'],
                    cod_nivel=nivel,
                    cod_tipo_tarifa=tipo,
                )
                if tarifa is None:
                    continue
                notas = []
                if tipo != tipo_solicitado:
                    notas.append(
                        f"No hay tarifa tipo {tipo_solicitado} publicada para el mercado "
                        f"{ciudad['nombre_mercado']}; se muestra la tipo {tipo}."
                    )
                if nivel != self.NIVELES_RESIDENCIALES[0]:
                    notas.append(f"Se usa el nivel de tensión {nivel} (no hay N1_1 publicado).")
                return {
                    'estrato': estrato,
                    'cs_kwh_mes': cs_kwh,
                    'cod_tipo_tarifa_solicitado': tipo_solicitado,
                    'cod_tipo_tarifa_aplicado': tipo,
                    'cod_nivel': nivel,
                    'nota': ' '.join(notas) or None,
                }, tarifa

        logger.warning(f"Sin tarifa residencial para el mercado {ciudad['cod_mercado']}")
        return {
            'estrato': estrato,
            'cs_kwh_mes': cs_kwh,
            'cod_tipo_tarifa_solicitado': tipo_solicitado,
            'cod_tipo_tarifa_aplicado': tipo_solicitado,
            'cod_nivel': self.NIVELES_RESIDENCIALES[0],
            'nota': None,
        }, None

    def _precios_24(self, id_periodo_tarifario: int) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """24 precios (hora 1..24) desde v_tarifa_hora; la monomia cubre las horas sin franja."""
        filas = self.repo.get_precios_por_hora_desde_vista(id_periodo_tarifario)
        por_hora = {f.hora: f for f in filas if f.hora is not None}
        sin_hora = [f for f in filas if f.hora is None]
        monomia = (
            {'valor': float(sin_hora[0].valor), 'unidad': sin_hora[0].unidad or 'COP/kWh', 'tipo': 'CU'}
            if sin_hora else None
        )

        precios = []
        for hora in range(1, 25):
            f = por_hora.get(hora)
            if f is not None:
                precios.append({
                    'hora': hora,
                    'codigo_franja': f.franja,
                    'tipo_hora': f.tipo_hora,
                    'precio': float(f.valor),
                    'unidad': f.unidad or 'COP/kWh',
                })
            else:
                precios.append({
                    'hora': hora,
                    'codigo_franja': None,
                    'tipo_hora': None,
                    'precio': monomia['valor'] if monomia else None,
                    'unidad': monomia['unidad'] if monomia else None,
                })
        return precios, monomia
