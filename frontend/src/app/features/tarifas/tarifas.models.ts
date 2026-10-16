/** Contratos de tariff-service `/api/v1/tariff/ubicacion/*` (ver docs/TARIFF-API.md). */

/** Tipo de hora tal como lo publica la comercializadora. */
export type TipoHora = 'VALLE' | 'MEDIA' | 'PICO';

export interface CiudadTarifaria {
  id_zona: number;
  cod_mercado: string;
  municipio: string;
  departamento: string | null;
  altura: number | null;
  nombre_mercado: string;
  operador_red: string | null;
}

export interface SeleccionTarifa {
  estrato: number;
  cs_kwh_mes: number;
  cod_tipo_tarifa_solicitado: string;
  cod_tipo_tarifa_aplicado: string;
  cod_nivel: string;
  nota: string | null;
}

export interface PrecioHora {
  /** 1 = 00:00–01:00 … 24 = 23:00–24:00 */
  hora: number;
  codigo_franja: string | null;
  tipo_hora: TipoHora | null;
  precio: number | null;
  unidad: string | null;
}

export interface TarifaUbicacionResponse {
  fecha: string;
  ciudad: CiudadTarifaria;
  seleccion: SeleccionTarifa;
  tarifa: {
    id_tarifa: number;
    codigo_tarifa: string;
    nombre_tarifa: string | null;
    cod_comercializadora: string;
    cod_mercado: string;
    cod_nivel: string;
    cod_tipo_tarifa: string | null;
    resolucion_regulatoria: string | null;
  };
  periodo: {
    id_periodo_tarifario: number;
    anio: number;
    mes: number;
    fecha_inicio: string;
    fecha_fin: string;
    numero_version: number;
    estado: string;
    fecha_publicacion: string | null;
  };
  monomia: { valor: number; unidad: string; tipo: string } | null;
  precios: PrecioHora[];
  componentes: { cod_componente: string; valor: number }[];
}

export interface MesCalendario {
  mes: number;
  publicado: boolean;
  numero_version: number | null;
  versiones: number;
  fecha_publicacion: string | null;
  precio_min: number | null;
  precio_max: number | null;
  precio_promedio: number | null;
  monomia: number | null;
  unidad: string;
}

export interface CalendarioTarifasResponse {
  anio: number;
  ciudad: CiudadTarifaria;
  seleccion: SeleccionTarifa;
  codigo_tarifa: string;
  meses: MesCalendario[];
}

/** Datos de la vivienda que determinan su tarifa. */
export interface UbicacionTarifaria {
  idZona: number;
  codMercado: string;
  estrato: number;
}
