import type { PrecioHora, TipoHora } from '../../tarifas/tarifas.models';
import type { FuenteEstimacion, HorarioUso } from '../electrodomesticos.service';

export const DIAS_CORTOS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
export const DIAS_LARGOS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
export const DIAS_POR_MES = 30.4375;

/** Paleta categórica (tonos medios legibles en tema claro y oscuro). */
export const PALETA = [
  '#06b6d4', '#10b981', '#f59e0b', '#8b5cf6', '#f43f5e',
  '#3b82f6', '#84cc16', '#f97316', '#14b8a6', '#d946ef',
];
export const COLOR_OTROS = '#64748b';

/** Potencia típica (W) para prellenar el editor cuando el usuario no la conoce. */
export const POTENCIA_TIPICA_W: Record<string, number> = {
  LAVADORA: 500,
  LAVAVAJILLAS: 1800,
  TERMO_ELECTRICO: 1500,
  VEHICULO_ELECTRICO: 7000,
  AIRE_ACONDICIONADO: 1200,
  NEVERA: 150,
  CONGELADOR: 200,
  HORNO: 2000,
  MICROONDAS: 1100,
  SECADORA: 2500,
  VITROCERAMICA: 1800,
  TELEVISOR: 100,
};

export const FUENTE_LABEL: Record<FuenteEstimacion, string> = {
  HORARIO_POTENCIA: 'Horario × potencia',
  HORARIO_CONSUMO: 'Horario × promedio diario',
  PROMEDIO_DIARIO: 'Promedio diario registrado',
  AJUSTE_USUARIO: 'Ajustado por ti',
};

export function colorFor(index: number): string {
  return PALETA[index % PALETA.length]!;
}

export function sum(xs: number[]): number {
  return xs.reduce((a, b) => a + b, 0);
}

export function totalPorDia(perfil: number[][]): number[] {
  return perfil.map((d) => sum(d));
}

/** Precio (COP/kWh) por hora 0–23; `null` donde no hay dato. */
export function preciosPorHora(precios: PrecioHora[], monomia: number | null): (number | null)[] {
  const out: (number | null)[] = Array(24).fill(monomia);
  for (const p of precios) {
    if (p.hora >= 1 && p.hora <= 24 && p.precio != null) out[p.hora - 1] = p.precio;
  }
  return out;
}

export function tiposPorHora(precios: PrecioHora[]): (TipoHora | null)[] {
  const out: (TipoHora | null)[] = Array(24).fill(null);
  for (const p of precios) {
    if (p.hora >= 1 && p.hora <= 24) out[p.hora - 1] = p.tipo_hora;
  }
  return out;
}

/** Costo mensual (COP) de un perfil semanal con precio horario. */
export function costoMensual(perfil: number[][], precioHora: (number | null)[]): number | null {
  if (precioHora.every((p) => p == null)) return null;
  let semana = 0;
  for (const dia of perfil) {
    dia.forEach((kwh, h) => (semana += kwh * (precioHora[h] ?? 0)));
  }
  return (semana * DIAS_POR_MES) / 7;
}

/** Proporción (0–1) del consumo semanal que cae en horas de un tipo (p. ej. PICO). */
export function fraccionEnTipo(perfil: number[][], tipos: (TipoHora | null)[], tipo: TipoHora): number {
  let total = 0;
  let enTipo = 0;
  for (const dia of perfil) {
    dia.forEach((kwh, h) => {
      total += kwh;
      if (tipos[h] === tipo) enTipo += kwh;
    });
  }
  return total > 0 ? enTipo / total : 0;
}

/** kWh de cada uno de los últimos `dias` días (hoy incluido) según el patrón semanal. */
export function tendenciaDiaria(perfil: number[][], dias: number, hoy = new Date()): { fecha: Date; kwh: number }[] {
  const porDia = totalPorDia(perfil);
  const out: { fecha: Date; kwh: number }[] = [];
  for (let i = dias - 1; i >= 0; i--) {
    const f = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate() - i);
    const iso = (f.getDay() + 6) % 7; // 0 = lunes
    out.push({ fecha: f, kwh: porDia[iso] ?? 0 });
  }
  return out;
}

export interface DonutSlice {
  id: number | null;
  label: string;
  value: number;
  pct: number;
  color: string;
  path: string;
}

/**
 * Arcos de un gráfico de dona. Agrupa en «Otros» lo que pase de `maxSlices`.
 * Coordenadas en un viewBox centrado en (0,0).
 */
export function donutSlices(
  items: { id: number; label: string; value: number; color: string }[],
  rOuter: number,
  rInner: number,
  maxSlices = 7,
): DonutSlice[] {
  const positivos = items.filter((i) => i.value > 0);
  const total = sum(positivos.map((i) => i.value));
  if (total <= 0) return [];
  let rows: { id: number | null; label: string; value: number; color: string }[] = positivos;
  if (positivos.length > maxSlices) {
    const top = positivos.slice(0, maxSlices - 1);
    const resto = positivos.slice(maxSlices - 1);
    rows = [...top, { id: null, label: `Otros (${resto.length})`, value: sum(resto.map((r) => r.value)), color: COLOR_OTROS }];
  }
  let a0 = -Math.PI / 2;
  return rows.map((r) => {
    const frac = r.value / total;
    const a1 = a0 + frac * Math.PI * 2;
    const path = arcPath(a0, a1, rOuter, rInner);
    a0 = a1;
    return { ...r, pct: frac * 100, path };
  });
}

function arcPath(a0: number, a1: number, ro: number, ri: number): string {
  // Un arco de 360° no se puede dibujar con un solo comando A: se parte en dos
  if (a1 - a0 >= Math.PI * 2 - 1e-6) {
    const mid = a0 + Math.PI;
    return arcPath(a0, mid, ro, ri) + ' ' + arcPath(mid, a1 - 1e-6, ro, ri);
  }
  const large = a1 - a0 > Math.PI ? 1 : 0;
  const p = (r: number, a: number) => `${(r * Math.cos(a)).toFixed(3)} ${(r * Math.sin(a)).toFixed(3)}`;
  return [
    `M ${p(ro, a0)}`,
    `A ${ro} ${ro} 0 ${large} 1 ${p(ro, a1)}`,
    `L ${p(ri, a1)}`,
    `A ${ri} ${ri} 0 ${large} 0 ${p(ri, a0)}`,
    'Z',
  ].join(' ');
}

/** Duración en horas de una franja (fin <= inicio → cruza medianoche; igual → 24 h). */
export function duracionHoras(h: HorarioUso): number {
  const ini = toMin(h.horaInicio);
  const fin = toMin(h.horaFin);
  if (ini == null || fin == null) return 0;
  return (fin > ini ? fin - ini : fin - ini + 1440) / 60;
}

export function toMin(hhmm: string): number | null {
  const m = /^(\d{1,2}):(\d{2})/.exec(hhmm ?? '');
  if (!m) return null;
  return Number(m[1]) * 60 + Number(m[2]);
}

/** Escala "bonita" para el eje Y. */
export function niceMax(v: number): number {
  if (v <= 0) return 1;
  const exp = Math.pow(10, Math.floor(Math.log10(v)));
  const n = v / exp;
  const step = n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10;
  return step * exp;
}
