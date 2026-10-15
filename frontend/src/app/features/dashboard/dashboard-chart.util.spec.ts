import { smoothPathLine } from './dashboard-chart.util';

describe('smoothPathLine', () => {
  it('devuelve cadena vacía sin puntos', () => {
    expect(smoothPathLine([])).toBe('');
  });

  it('con un punto solo hace move-to', () => {
    expect(smoothPathLine([{ x: 3, y: 4 }])).toBe('M 3 4');
  });

  it('genera una cúbica por cada tramo entre puntos', () => {
    const d = smoothPathLine([
      { x: 0, y: 0 },
      { x: 10, y: 10 },
      { x: 20, y: 0 },
    ]);
    expect(d.startsWith('M 0 0')).toBe(true);
    expect(d.match(/ C /g)?.length).toBe(2);
    expect(d.endsWith('20 0')).toBe(true);
  });
});
