/**
 * Escala del eje Y del gráfico a partir de series horarias (kWh agregados desde valor_kwh en consumo).
 */

/**
 * @param {number[][]} seriesList
 * @returns {number}
 */
export function peakKwhFromSeries(seriesList) {
  const flat = seriesList
    .filter(Array.isArray)
    .flat()
    .filter((n) => typeof n === 'number' && Number.isFinite(n));
  if (!flat.length) {
    return 0;
  }
  return Math.max(0, ...flat);
}

/**
 * Tope del eje Y “amable” (1, 2, 5, 10 × 10^n), a partir del pico de consumo (insumo).
 * @param {number} peak
 * @returns {number}
 */
export function niceCeilKwh(peak) {
  if (!Number.isFinite(peak) || peak <= 0) {
    return 0;
  }
  const x = peak;
  const exp = Math.floor(Math.log10(x));
  const pow = 10 ** exp;
  const f = x / pow;
  let nf;
  if (f <= 1) nf = 1;
  else if (f <= 2) nf = 2;
  else if (f <= 5) nf = 5;
  else nf = 10;
  return nf * pow;
}

/**
 * maxKwhScale para la API: margen ligero sobre el pico real (solo insumo).
 * @param {number[]} actualKwh
 * @param {number[]|null} predictedKwh
 * @param {number} [paddingRatio=1.08]
 * @returns {number|null} null si no hay datos para escalar
 */
export function maxKwhScaleFromHourlySeries(actualKwh, predictedKwh, paddingRatio = 1.08) {
  const pred = Array.isArray(predictedKwh) ? predictedKwh : [];
  const peak = peakKwhFromSeries([actualKwh || [], pred]);
  if (peak <= 0) {
    return null;
  }
  const withPadding = peak * paddingRatio;
  const nice = niceCeilKwh(withPadding);
  return Math.round(nice * 1000) / 1000;
}
