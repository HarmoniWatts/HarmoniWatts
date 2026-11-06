import { toContrato } from './vivienda-context.service';
import type { ViviendaDto } from './vivienda.service';

const base: ViviendaDto = { id: 1, tipo: 'Casa', habitantes: 3, estrato: 3, ubicacion: 'Calle 1' };

describe('toContrato (consumos por contrato + comercializadora)', () => {
  it('es null sin vivienda o sin alguno de los dos datos', () => {
    expect(toContrato(null)).toBeNull();
    expect(toContrato(base)).toBeNull();
    expect(toContrato({ ...base, numeroContrato: '753691' })).toBeNull();
    expect(toContrato({ ...base, codComercializadora: 'ENERTOTAL' })).toBeNull();
    expect(toContrato({ ...base, numeroContrato: '  ', codComercializadora: 'ENERTOTAL' })).toBeNull();
  });

  it('devuelve la pareja sin espacios', () => {
    expect(toContrato({ ...base, numeroContrato: ' 753691 ', codComercializadora: 'ENERTOTAL' })).toEqual({
      noContrato: '753691',
      codComercializadora: 'ENERTOTAL',
    });
  });
});
