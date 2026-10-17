import { test } from 'node:test';
import assert from 'node:assert/strict';
import TariffUtils from '../src/utils/tariffUtils.js';
import { tariffBands } from '../src/config/index.js';

test('getTariffByHour devuelve la franja correcta', () => {
  assert.equal(TariffUtils.getTariffByHour(3).type, 'VALLE');
  assert.equal(TariffUtils.getTariffByHour(8).type, 'MEDIA');
  assert.equal(TariffUtils.getTariffByHour(19).type, 'PUNTA');
  assert.equal(TariffUtils.getTariffByHour(23).type, 'VALLE');
});

test('getNextHighTariffWindow busca la próxima punta', () => {
  assert.equal(TariffUtils.getNextHighTariffWindow(9).startsAtHour, 10);
  assert.equal(TariffUtils.getNextHighTariffWindow(14).startsAtHour, 18);
  const tomorrow = TariffUtils.getNextHighTariffWindow(22);
  assert.equal(tomorrow.startsAtHour, 10);
  assert.equal(tomorrow.isTomorrow, true);
});

test('calculateEstimatedCost suma consumo × precio por hora', () => {
  const series = Array(24).fill(0);
  series[2] = 1; // valle 280
  series[11] = 2; // punta 980
  assert.equal(TariffUtils.calculateEstimatedCost(null, tariffBands, series), 280 + 1960);
});

test('calculateSavings nunca es negativo', () => {
  const soloPunta = Array(24).fill(0);
  soloPunta[19] = 1;
  assert.equal(TariffUtils.calculateSavings(soloPunta, tariffBands), 0);
  const soloValle = Array(24).fill(0);
  soloValle[1] = 1;
  assert.equal(TariffUtils.calculateSavings(soloValle, tariffBands), 520 - 280);
});
