import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  peakKwhFromSeries,
  niceCeilKwh,
  maxKwhScaleFromHourlySeries,
} from '../src/utils/chartScale.js';

test('peakKwhFromSeries ignora valores no numéricos', () => {
  assert.equal(peakKwhFromSeries([[1, 2.5, NaN], [null, 'x', 0.3], 'no-array']), 2.5);
  assert.equal(peakKwhFromSeries([]), 0);
  assert.equal(peakKwhFromSeries([[-1, -3]]), 0);
});

test('niceCeilKwh redondea a 1, 2, 5 o 10 × 10^n', () => {
  assert.equal(niceCeilKwh(0.7), 1);
  assert.equal(niceCeilKwh(1.3), 2);
  assert.equal(niceCeilKwh(3), 5);
  assert.equal(niceCeilKwh(7.2), 10);
  assert.equal(niceCeilKwh(42), 50);
  assert.equal(niceCeilKwh(0), 0);
  assert.equal(niceCeilKwh(Infinity), 0);
});

test('maxKwhScaleFromHourlySeries aplica margen y usa la predicción', () => {
  assert.equal(maxKwhScaleFromHourlySeries([1, 1.9], null), 5); // 1.9 * 1.08 = 2.05 → 5
  assert.equal(maxKwhScaleFromHourlySeries([0.5], [0.8]), 1);
  assert.equal(maxKwhScaleFromHourlySeries([], []), null);
});
