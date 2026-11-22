import { describe, expect, it } from 'vitest';
import { kwhMesDesdeWatts, potenciaDesdeEtiqueta, wattsDesdeKwhMes } from './potencia-input.component';

describe('conversión kWh/mes ↔ W', () => {
  it('nevera siempre encendida: 35 kWh/mes ≈ 48 W promedio', () => {
    expect(wattsDesdeKwhMes(35, 168)).toBe(48);
  });

  it('ida y vuelta conserva el kWh/mes con el mismo horario', () => {
    const w = wattsDesdeKwhMes(20, 10)!;
    expect(kwhMesDesdeWatts(w, 10)).toBeCloseTo(20, 0);
  });

  it('sin horario o sin consumo no hay resultado', () => {
    expect(wattsDesdeKwhMes(20, 0)).toBeNull();
    expect(wattsDesdeKwhMes(0, 10)).toBeNull();
  });
});

describe('potenciaDesdeEtiqueta (foto con IA)', () => {
  it('usa la placa en aparatos sin compresor', () => {
    expect(potenciaDesdeEtiqueta(1000, 20, 'OTRO', 7)).toEqual({ w: 1000, origen: 'placa' });
  });

  it('en la nevera prefiere el kWh/mes de la etiqueta', () => {
    expect(potenciaDesdeEtiqueta(150, 35, 'NEVERA', 168)).toEqual({ w: 48, origen: 'etiqueta' });
  });

  it('sin placa convierte la etiqueta; sin datos no sugiere', () => {
    expect(potenciaDesdeEtiqueta(null, 35, 'LAVADORA', 168)?.origen).toBe('etiqueta');
    expect(potenciaDesdeEtiqueta(null, null, 'LAVADORA', 7)).toBeNull();
  });
});
