import { describe, expect, it } from 'vitest';
import type { EstimacionElectrodomestico, EstimacionViviendaResponse } from '../electrodomesticos/electrodomesticos.service';
import { toAppliancesTop } from './dashboard.component';

function electro(id: number, kwhMes: number, activo = true): EstimacionElectrodomestico {
  return {
    id,
    nombre: `E${id}`,
    tipoCodigo: 'NEVERA',
    tipoNombre: 'Nevera',
    activo,
    optimizable: false,
    fuente: 'HORARIO_POTENCIA',
    potenciaW: 100,
    horasSemana: 168,
    kwhDia: kwhMes / 30,
    kwhSemana: 0,
    kwhMes,
    kwhMesCalculado: kwhMes,
    porcentaje: kwhMes,
    ranking: id,
    perfilSemanal: [],
  };
}

describe('toAppliancesTop (dashboard)', () => {
  it('toma los activos con consumo, en el orden del ranking y hasta el límite', () => {
    const est = {
      electrodomesticos: [electro(1, 50), electro(2, 30), electro(3, 0), electro(4, 20, false), electro(5, 10)],
    } as EstimacionViviendaResponse;
    const top = toAppliancesTop(est, 2);
    expect(top.items.map((i) => i.id)).toEqual(['1', '2']);
    expect(top.items[0]).toMatchObject({ name: 'E1', category: 'NEVERA', sharePercent: 50, consumptionKwh: 50 });
    expect(toAppliancesTop(est, 5).items.map((i) => i.id)).toEqual(['1', '2', '5']);
  });
});
