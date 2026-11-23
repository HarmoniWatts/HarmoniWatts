import { test } from 'node:test';
import assert from 'node:assert/strict';
import { seriePrediccionDelDia, toDashboardPrediction } from '../src/utils/prediccion.js';

const pron = {
  meter_no: 'MN1',
  generado_en: '2026-11-22T18:00:00+00:00',
  ultima_lectura: '2026-11-22T12:00:00',
  modelo: { nombre: 'CentralFTForecaster' },
  historico: [
    { timestamp: '2026-11-22T11:00:00', real_kwh: 0.4, estimado_kwh: 0.5 },
    { timestamp: '2026-11-22T12:00:00', real_kwh: 0.6, estimado_kwh: 0.55 },
  ],
  futuro: [
    { timestamp: '2026-11-22T13:00:00', estimado_kwh: 0.7, inferior_kwh: 0.5, superior_kwh: 0.9 },
    { timestamp: '2026-11-23T00:00:00', estimado_kwh: 0.2, inferior_kwh: 0.1, superior_kwh: 0.3 },
  ],
  confianza: { nivel: 'medio', error_diario_pct: 16.3, error_horario_pct: 27.5, dias_evaluados: 7, horas_evaluadas: 168, metodo: 'WAPE' },
};

test('seriePrediccionDelDia junta backtest y pronóstico del día', () => {
  const s = seriePrediccionDelDia(pron, '2026-11-22');
  assert.equal(s.length, 24);
  assert.equal(s[11], 0.5);
  assert.equal(s[12], 0.55);
  assert.equal(s[13], 0.7);
  assert.equal(s[0], null);
  assert.equal(s[23], null);
});

test('seriePrediccionDelDia devuelve null sin datos del día', () => {
  assert.equal(seriePrediccionDelDia(pron, '2026-11-30'), null);
  assert.equal(seriePrediccionDelDia(null, '2026-11-22'), null);
});

test('toDashboardPrediction pasa a camelCase y traduce el nivel', () => {
  const d = toDashboardPrediction(pron);
  assert.equal(d.available, true);
  assert.equal(d.confidence.level, 'MEDIUM');
  assert.equal(d.confidence.dailyErrorPct, 16.3);
  assert.deepEqual(d.history[0], { timestamp: '2026-11-22T11:00:00', actualKwh: 0.4, predictedKwh: 0.5 });
  assert.deepEqual(d.forecast[1], { timestamp: '2026-11-23T00:00:00', predictedKwh: 0.2, lowerKwh: 0.1, upperKwh: 0.3 });
});
