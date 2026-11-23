import { describe, expect, it } from 'vitest';
import type { DashboardPredictionResponse } from '../dashboard.models';
import { diasDePrediccion, horasDePrediccion, resumen, tiposPorHora } from './prediccion.util';

/** Ventana como la del servicio: 36 h pasadas (desde las 12:00) + 36 h futuras. */
function respuesta(): DashboardPredictionResponse {
  const ts = (d: number, h: number) => `2026-11-${String(d).padStart(2, '0')}T${String(h).padStart(2, '0')}:00:00`;
  const history = [];
  const forecast = [];
  for (let i = 0; i < 36; i++) {
    const d = 20 + Math.floor((12 + i) / 24);
    history.push({ timestamp: ts(d, (12 + i) % 24), actualKwh: 1, predictedKwh: 0.9 });
  }
  for (let i = 0; i < 36; i++) {
    const d = 22 + Math.floor(i / 24);
    forecast.push({ timestamp: ts(d, i % 24), predictedKwh: 0.5, lowerKwh: 0.4, upperKwh: 0.6 });
  }
  return {
    available: true,
    confidence: { level: 'MEDIUM', dailyErrorPct: 20, hourlyErrorPct: 30, daysEvaluated: 1, hoursEvaluated: 36, method: null },
    history,
    forecast,
  };
}

describe('prediccion.util', () => {
  it('une historia y pronóstico en orden', () => {
    const h = horasDePrediccion(respuesta());
    expect(h).toHaveLength(72);
    expect(h[0]).toMatchObject({ dia: '2026-11-20', hora: 12, real: 1, pred: 0.9, futuro: false });
    expect(h[71]).toMatchObject({ dia: '2026-11-23', hora: 11, real: null, futuro: true, inf: 0.4, sup: 0.6 });
    expect(horasDePrediccion({ available: false })).toEqual([]);
  });

  it('agrega por día y descarta los días incompletos de los extremos', () => {
    const dias = diasDePrediccion(horasDePrediccion(respuesta()), null, 20);
    expect(dias.map((d) => d.dia)).toEqual(['2026-11-21', '2026-11-22']);
    const [ayer, hoy] = dias;
    expect(ayer).toMatchObject({ real: 24, horasReales: 24, futuro: false, inf: null });
    expect(ayer.pred).toBeCloseTo(21.6);
    // Hoy solo tiene horas futuras: rango = ± error diario medido (20 %)
    expect(hoy).toMatchObject({ real: null, futuro: true });
    expect(hoy.pred).toBeCloseTo(12);
    expect(hoy.inf).toBeCloseTo(9.6);
    expect(hoy.sup).toBeCloseTo(14.4);
  });

  it('reparte el predicho por franja según la tarifa', () => {
    const tipos = tiposPorHora(
      Array.from({ length: 24 }, (_, i) => ({ hora: i + 1, tipo_hora: i < 6 ? 'VALLE' : i >= 18 ? 'PICO' : 'MEDIA' })),
    );
    const [ayer] = diasDePrediccion(horasDePrediccion(respuesta()), tipos, 20);
    expect(ayer.franjas.VALLE).toBeCloseTo(6 * 0.9);
    expect(ayer.franjas.PUNTA).toBeCloseTo(6 * 0.9);
    expect(ayer.franjas.MEDIA).toBeCloseTo(12 * 0.9);
  });

  it('resume pasado y próximos días', () => {
    const r = resumen(diasDePrediccion(horasDePrediccion(respuesta()), null, 20));
    expect(r).toMatchObject({ dias: 1, pasadoReal: 24, diasFuturos: 1 });
    expect(r.futuroPred).toBeCloseTo(12);
  });
});
