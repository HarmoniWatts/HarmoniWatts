import { describe, expect, it } from 'vitest';
import { cuando } from './notificacion-item.component';
import { desdeAlerta, desdeRecomendacion, ordenarNotificaciones } from './notificaciones.service';

describe('notificaciones', () => {
  it('alertas primero, por severidad y luego las más recientes; IA al final', () => {
    const ns = ordenarNotificaciones([
      desdeRecomendacion({ id: 'r1', title: 'IA', body: '' }, '2026-11-22T22:00'),
      desdeAlerta({ id: 'a', type: 'CONSUMPTION_HOUR', severity: 'LOW', title: '', message: '', timestamp: '2026-11-22T13:00' }),
      desdeAlerta({ id: 'b', type: 'TARIFF_PEAK', severity: 'HIGH', title: '', message: '', timestamp: '2026-11-22T18:00' }),
      desdeAlerta({ id: 'c', type: 'CONSUMPTION_DAY', severity: 'LOW', title: '', message: '', timestamp: '2026-11-22T14:00' }),
    ]);
    expect(ns.map((n) => n.id)).toEqual(['b', 'c', 'a', 'ia-r1']);
    expect(ns[3]).toMatchObject({ origen: 'IA', severidad: null, tipo: 'RECOMMENDATION' });
  });

  it('cuando() muestra tiempo relativo legible', () => {
    const ahora = new Date(2026, 10, 22, 22, 0);
    expect(cuando('2026-11-22T21:50', ahora)).toBe('hace 10 min');
    expect(cuando('2026-11-22T13:00', ahora)).toBe('hace 9 h');
    expect(cuando('2026-11-21T18:00', ahora)).toBe('ayer 18:00');
    expect(cuando('2026-11-22T23:00', ahora)).toBe('hoy 23:00');
  });
});
