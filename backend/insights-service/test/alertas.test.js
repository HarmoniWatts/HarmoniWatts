import { test } from 'node:test';
import assert from 'node:assert/strict';
import { alertasConsumo, alertasFranja, ordenarAlertas, severidadExceso } from '../src/utils/alertas.js';

// Tarifa: valle 0–5, media 6–17, punta 18–20, valle 21–23 (hora 0–23)
const precios = Array.from({ length: 24 }, (_, i) => ({
  hora: i + 1,
  tipo_hora: i < 6 || i > 20 ? 'VALLE' : i >= 18 ? 'PICO' : 'MEDIA',
  precio: i < 6 || i > 20 ? 500 : i >= 18 ? 1000 : 700,
}));

test('en punta: alerta ALTA con el fin de la franja y el sobrecosto vs valle', () => {
  const [a] = alertasFranja(precios, { fecha: '2026-11-22', hora: 19, minuto: 10 });
  assert.equal(a.type, 'TARIFF_PEAK');
  assert.equal(a.severity, 'HIGH');
  assert.equal(a.id, 'franja-punta-2026-11-22-18');
  assert.match(a.message, /hasta las 21:00/);
  assert.match(a.message, /100 % más que en valle/);
});

test('punta cerca: MEDIA a ≤ 60 min, BAJA a ≤ 3 h, nada si falta más', () => {
  assert.equal(alertasFranja(precios, { fecha: '2026-11-22', hora: 17, minuto: 15 })[0].severity, 'MEDIUM');
  const [baja] = alertasFranja(precios, { fecha: '2026-11-22', hora: 15, minuto: 30 });
  assert.equal(baja.severity, 'LOW');
  assert.equal(baja.data.minutesToStart, 150);
  assert.deepEqual(alertasFranja(precios, { fecha: '2026-11-22', hora: 10, minuto: 0 }), []);
  assert.deepEqual(alertasFranja(precios, { fecha: '2026-11-22', hora: 22, minuto: 0 }), []);
  assert.deepEqual(alertasFranja([], { fecha: '2026-11-22', hora: 17, minuto: 0 }), []);
});

/** 7 días previos con 0,2 kWh por hora; hoy hasta las 13:00 con `hoyKwh` por hora. */
function lecturas(hoyKwh, ultimaKwh = hoyKwh) {
  const out = [];
  for (let d = 15; d <= 21; d++) {
    for (let h = 0; h < 24; h++) out.push({ ts: `2026-11-${d}T${String(h).padStart(2, '0')}:00:00`, kwh: 0.2 });
  }
  for (let h = 0; h <= 13; h++) {
    out.push({ ts: `2026-11-22T${String(h).padStart(2, '0')}:00:00`, kwh: h === 13 ? ultimaKwh : hoyKwh });
  }
  return out;
}

test('consumo normal: sin alertas', () => {
  assert.deepEqual(alertasConsumo(lecturas(0.21)), []);
});

test('última hora muy por encima del promedio: alerta por hora con su severidad', () => {
  const alertas = alertasConsumo(lecturas(0.2, 0.45)); // +125 %
  assert.equal(alertas.length, 1);
  assert.equal(alertas[0].type, 'CONSUMPTION_HOUR');
  assert.equal(alertas[0].severity, 'HIGH');
  assert.equal(alertas[0].data.excessPct, 125);
});

test('día completo por encima: alerta del acumulado', () => {
  const dia = alertasConsumo(lecturas(0.28)).find((a) => a.type === 'CONSUMPTION_DAY'); // +40 %
  assert.equal(dia.severity, 'LOW');
  assert.equal(dia.data.untilHour, 14);
  assert.equal(dia.id, 'consumo-dia-2026-11-22-LOW');
});

test('sin historia suficiente no alerta', () => {
  const pocas = lecturas(0.6).filter((l) => l.ts >= '2026-11-20');
  assert.deepEqual(alertasConsumo(pocas), []);
});

test('umbrales y orden', () => {
  assert.equal(severidadExceso(0.29), null);
  assert.equal(severidadExceso(0.3), 'LOW');
  assert.equal(severidadExceso(0.6), 'MEDIUM');
  assert.equal(severidadExceso(1), 'HIGH');
  const orden = ordenarAlertas([
    { severity: 'LOW', timestamp: '2026-11-22T10:00' },
    { severity: 'HIGH', timestamp: '2026-11-22T09:00' },
    { severity: 'LOW', timestamp: '2026-11-22T11:00' },
  ]);
  assert.deepEqual(orden.map((a) => a.timestamp), ['2026-11-22T09:00', '2026-11-22T11:00', '2026-11-22T10:00']);
});
