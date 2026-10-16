import {
  estimateDailyCostCop,
  toCurrentTariffSlot,
  toNextHighTariffWindow,
  toTariffBands,
} from './tariff-dashboard.adapter';
import type { PrecioHora, TipoHora } from './tarifas.models';

/** Curva CH00 de Enertotal: F1 valle, F2/F3 media, F4/F5 pico. */
function curva(): PrecioHora[] {
  const franja = (h: number): [string, TipoHora, number] => {
    if (h <= 4 || h === 24) return ['F1', 'VALLE', 769.3];
    if (h >= 10 && h <= 12) return ['F3', 'MEDIA', 781];
    if (h >= 19 && h <= 21) return ['F4', 'PICO', 785.8];
    if (h === 22) return ['F5', 'PICO', 782.96];
    return ['F2', 'MEDIA', 778.16];
  };
  return Array.from({ length: 24 }, (_, i) => {
    const [codigo_franja, tipo_hora, precio] = franja(i + 1);
    return { hora: i + 1, codigo_franja, tipo_hora, precio, unidad: 'COP/kWh' };
  });
}

describe('tariff-dashboard.adapter', () => {
  it('agrupa horas contiguas en bandas de reloj y traduce PICO a PUNTA', () => {
    const bands = toTariffBands(curva());

    expect(bands[0]).toEqual({ type: 'VALLE', startHour: 0, endHour: 4, energyPriceCopPerKwh: 769.3 });
    expect(bands.find((b) => b.startHour === 18)).toEqual({
      type: 'PUNTA',
      startHour: 18,
      endHour: 21,
      energyPriceCopPerKwh: 785.8,
    });
    // F4 y F5 son PICO pero con distinto precio: bandas separadas
    expect(bands.find((b) => b.startHour === 21)?.energyPriceCopPerKwh).toBe(782.96);
    expect(bands[bands.length - 1]).toMatchObject({ type: 'VALLE', startHour: 23, endHour: 24 });
  });

  it('resuelve la franja vigente de una hora de reloj', () => {
    expect(toCurrentTariffSlot(curva(), 19)).toEqual({
      type: 'PUNTA',
      label: 'Punta (F4)',
      energyPriceCopPerKwh: 785.8,
    });
    expect(toCurrentTariffSlot([], 10)).toBeNull();
  });

  it('indica la próxima punta o la que está en curso', () => {
    const proxima = toNextHighTariffWindow(curva(), '2026-09-15', 14);
    expect(proxima?.displayHint).toBe('Punta 18:00');
    expect(new Date(proxima!.startsAt).getHours()).toBe(18);

    expect(toNextHighTariffWindow(curva(), '2026-09-15', 19)?.displayHint).toBe('Punta ahora · hasta 21:00');
    expect(toNextHighTariffWindow(curva(), '2026-09-15', 23)).toBeNull();
  });

  it('estima el costo del día con el precio de cada hora', () => {
    const kwh = Array.from({ length: 24 }, () => 0);
    kwh[0] = 2; // 00:00 valle
    kwh[19] = 1; // 19:00 punta
    expect(estimateDailyCostCop(curva(), kwh)).toBeCloseTo(2 * 769.3 + 785.8, 2);
  });
});
