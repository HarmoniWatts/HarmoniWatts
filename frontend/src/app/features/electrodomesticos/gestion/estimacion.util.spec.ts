import { describe, expect, it } from 'vitest';
import { costoMensual, DIAS_POR_MES, donutSlices, duracionHoras, fraccionEnTipo, tendenciaDiaria } from './estimacion.util';

function perfilVacio(): number[][] {
  return Array.from({ length: 7 }, () => Array(24).fill(0));
}

describe('estimacion.util', () => {
  it('duracionHoras maneja franjas que cruzan medianoche', () => {
    expect(duracionHoras({ diaSemana: 1, horaInicio: '18:00', horaFin: '19:30' })).toBe(1.5);
    expect(duracionHoras({ diaSemana: 1, horaInicio: '22:00', horaFin: '06:00' })).toBe(8);
  });

  it('costoMensual multiplica kWh por el precio de cada hora', () => {
    const p = perfilVacio();
    p[0]![18] = 1; // 1 kWh el lunes a las 18
    const precios = Array(24).fill(100);
    precios[18] = 1000;
    expect(costoMensual(p, precios)).toBeCloseTo((1000 * DIAS_POR_MES) / 7);
    expect(costoMensual(p, Array(24).fill(null))).toBeNull();
  });

  it('fraccionEnTipo calcula la parte en hora pico', () => {
    const p = perfilVacio();
    p[0]![10] = 1;
    p[0]![19] = 3;
    const tipos = Array(24).fill('VALLE');
    tipos[19] = 'PICO';
    expect(fraccionEnTipo(p, tipos, 'PICO')).toBeCloseTo(0.75);
  });

  it('tendenciaDiaria sigue el patrón semanal', () => {
    const p = perfilVacio();
    p[0]![8] = 2; // lunes
    const serie = tendenciaDiaria(p, 7, new Date(2026, 10, 22)); // domingo
    expect(serie).toHaveLength(7);
    expect(serie.find((s) => s.fecha.getDay() === 1)?.kwh).toBe(2);
    expect(serie.filter((s) => s.kwh === 0)).toHaveLength(6);
  });

  it('donutSlices agrupa el resto en «Otros»', () => {
    const items = Array.from({ length: 9 }, (_, i) => ({ id: i, label: `E${i}`, value: 9 - i, color: '#000' }));
    const s = donutSlices(items, 100, 60, 5);
    expect(s).toHaveLength(5);
    expect(s[4]!.label).toBe('Otros (5)');
    expect(s.reduce((a, x) => a + x.pct, 0)).toBeCloseTo(100);
  });
});
