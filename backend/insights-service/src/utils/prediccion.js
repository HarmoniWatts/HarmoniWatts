/**
 * Utilidades del pronóstico de prediction-service (HAR-25). Funciones puras.
 *
 * prediction-service responde (snake_case, timestamps locales sin zona):
 *   historico: [{ timestamp, real_kwh, estimado_kwh }]   predicción del modelo vs real (backtest)
 *   futuro:    [{ timestamp, estimado_kwh, inferior_kwh, superior_kwh }]
 *   confianza: { nivel, error_diario_pct, error_horario_pct, dias_evaluados, horas_evaluadas, metodo }
 */

const NIVELES = { alto: 'HIGH', medio: 'MEDIUM', bajo: 'LOW' };

/** Respuesta del dashboard (camelCase, como el resto de insights-service). */
export function toDashboardPrediction(p) {
  const c = p.confianza ?? {};
  return {
    available: true,
    meterNo: p.meter_no,
    generatedAt: p.generado_en,
    lastReading: p.ultima_lectura,
    model: p.modelo?.nombre ?? null,
    confidence: {
      level: NIVELES[c.nivel] ?? 'LOW',
      dailyErrorPct: c.error_diario_pct ?? null,
      hourlyErrorPct: c.error_horario_pct ?? null,
      daysEvaluated: c.dias_evaluados ?? 0,
      hoursEvaluated: c.horas_evaluadas ?? 0,
      method: c.metodo ?? null,
    },
    history: (p.historico ?? []).map((h) => ({
      timestamp: h.timestamp,
      actualKwh: h.real_kwh,
      predictedKwh: h.estimado_kwh,
    })),
    forecast: (p.futuro ?? []).map((f) => ({
      timestamp: f.timestamp,
      predictedKwh: f.estimado_kwh,
      lowerKwh: f.inferior_kwh,
      upperKwh: f.superior_kwh,
    })),
  };
}

/**
 * Serie de 24 valores (hora 0–23) del día `fecha` (YYYY-MM-DD) con la predicción del modelo:
 * horas pasadas desde el backtest y horas siguientes desde el pronóstico.
 * Las horas sin predicción quedan en null. Devuelve null si el día no tiene ninguna.
 */
export function seriePrediccionDelDia(p, fecha) {
  if (!p || !fecha) return null;
  const serie = new Array(24).fill(null);
  const poner = (timestamp, valor) => {
    if (typeof timestamp !== 'string' || !timestamp.startsWith(fecha) || valor == null) return;
    const hora = Number(timestamp.slice(11, 13));
    if (hora >= 0 && hora < 24) serie[hora] = Math.round(valor * 1000) / 1000;
  };
  for (const h of p.historico ?? []) poner(h.timestamp, h.estimado_kwh);
  for (const f of p.futuro ?? []) poner(f.timestamp, f.estimado_kwh);
  return serie.some((v) => v !== null) ? serie : null;
}
