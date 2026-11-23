import type { DashboardPredictionResponse } from '../dashboard.models';

/** Franjas tarifarias (mismos nombres que el resto del dashboard). */
export type Franja = 'VALLE' | 'MEDIA' | 'PUNTA';
export const FRANJAS: Franja[] = ['VALLE', 'MEDIA', 'PUNTA'];

/** Una hora de la ventana: real solo en el pasado; rango solo en el futuro. */
export interface HoraPred {
  ts: string; // 'YYYY-MM-DDTHH:00:00' (hora local)
  dia: string; // 'YYYY-MM-DD'
  hora: number;
  real: number | null;
  pred: number;
  inf: number | null;
  sup: number | null;
  futuro: boolean;
}

export interface DiaPred {
  dia: string;
  real: number | null;
  /** Horas con consumo real (24 = día completo). */
  horasReales: number;
  pred: number;
  inf: number | null;
  sup: number | null;
  /** Día con alguna hora futura (hoy o después). */
  futuro: boolean;
  /** kWh predichos por franja tarifaria. */
  franjas: Record<Franja, number>;
}

/** Une historia (predicción vs real) y pronóstico en una sola serie horaria ordenada. */
export function horasDePrediccion(p: DashboardPredictionResponse | null): HoraPred[] {
  if (!p?.available) return [];
  const out: HoraPred[] = [];
  for (const h of p.history ?? []) {
    out.push({ ...base(h.timestamp), real: h.actualKwh, pred: h.predictedKwh, inf: null, sup: null, futuro: false });
  }
  for (const f of p.forecast ?? []) {
    out.push({ ...base(f.timestamp), real: null, pred: f.predictedKwh, inf: f.lowerKwh, sup: f.upperKwh, futuro: true });
  }
  return out.sort((a, b) => a.ts.localeCompare(b.ts));
}

function base(ts: string): Pick<HoraPred, 'ts' | 'dia' | 'hora'> {
  return { ts, dia: ts.slice(0, 10), hora: Number(ts.slice(11, 13)) };
}

/**
 * Agrega por día. Se descartan los días de los extremos con menos de 24 h (la ventana empieza y
 * termina a cualquier hora). El rango diario se estima con el error diario medido (WAPE):
 * sumar los rangos horarios lo exageraría, porque los errores de cada hora se compensan.
 */
export function diasDePrediccion(
  horas: HoraPred[],
  tipos: (Franja | null)[] | null,
  errorDiarioPct: number | null,
): DiaPred[] {
  const porDia = new Map<string, HoraPred[]>();
  for (const h of horas) {
    const l = porDia.get(h.dia) ?? [];
    l.push(h);
    porDia.set(h.dia, l);
  }
  const rel = errorDiarioPct != null ? errorDiarioPct / 100 : 0.3;
  const dias: DiaPred[] = [];
  for (const [dia, hs] of porDia) {
    if (hs.length < 24) continue;
    const reales = hs.filter((h) => h.real != null);
    const pred = suma(hs.map((h) => h.pred));
    const futuro = hs.some((h) => h.futuro);
    const franjas: Record<Franja, number> = { VALLE: 0, MEDIA: 0, PUNTA: 0 };
    for (const h of hs) franjas[tipos?.[h.hora] ?? 'MEDIA'] += h.pred;
    dias.push({
      dia,
      real: reales.length ? suma(reales.map((h) => h.real!)) : null,
      horasReales: reales.length,
      pred,
      inf: futuro ? Math.max(0, pred * (1 - rel)) : null,
      sup: futuro ? pred * (1 + rel) : null,
      futuro,
      franjas,
    });
  }
  return dias.sort((a, b) => a.dia.localeCompare(b.dia));
}

export interface ResumenPred {
  pasadoReal: number;
  pasadoPred: number;
  dias: number;
  futuroPred: number;
  futuroInf: number;
  futuroSup: number;
  diasFuturos: number;
}

/** Totales de los días completos: pasado (real vs predicho) y próximos (predicho y rango). */
export function resumen(dias: DiaPred[]): ResumenPred {
  const pasados = dias.filter((d) => !d.futuro && d.real != null);
  const futuros = dias.filter((d) => d.futuro && d.horasReales === 0);
  return {
    pasadoReal: suma(pasados.map((d) => d.real!)),
    pasadoPred: suma(pasados.map((d) => d.pred)),
    dias: pasados.length,
    futuroPred: suma(futuros.map((d) => d.pred)),
    futuroInf: suma(futuros.map((d) => d.inf ?? d.pred)),
    futuroSup: suma(futuros.map((d) => d.sup ?? d.pred)),
    diasFuturos: futuros.length,
  };
}

/** Franja (VALLE/MEDIA/PUNTA) por hora 0–23 desde los precios de la tarifa. */
export function tiposPorHora(precios: { hora: number; tipo_hora: string | null }[]): (Franja | null)[] {
  const out: (Franja | null)[] = Array(24).fill(null);
  for (const p of precios) {
    if (p.hora < 1 || p.hora > 24) continue;
    out[p.hora - 1] = p.tipo_hora === 'VALLE' ? 'VALLE' : p.tipo_hora === 'PICO' ? 'PUNTA' : p.tipo_hora ? 'MEDIA' : null;
  }
  return out;
}

export function suma(xs: number[]): number {
  return xs.reduce((a, b) => a + b, 0);
}

export function niceMax(v: number): number {
  if (v <= 0) return 1;
  const exp = Math.pow(10, Math.floor(Math.log10(v)));
  const n = v / exp;
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * exp;
}
