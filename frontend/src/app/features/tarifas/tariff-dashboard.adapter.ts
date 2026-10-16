/**
 * Adaptador tariff-service → contratos del dashboard (DASHBOARD-API.md).
 *
 * El dashboard trabaja con horas de reloj 0–23 y franjas `[startHour, endHour)`;
 * tariff-service publica horas 1–24 (hora 1 = 00:00–01:00) y tipos VALLE/MEDIA/PICO.
 * El dashboard nombra PUNTA a la franja cara, así que PICO se traduce a PUNTA.
 */
import type {
  DashboardSummaryResponse,
  TariffBand,
  TariffType,
} from '../dashboard/dashboard.models';
import type { PrecioHora, TipoHora } from './tarifas.models';

type CurrentTariffSlot = DashboardSummaryResponse['currentTariffSlot'];
type NextHighTariffWindow = DashboardSummaryResponse['nextHighTariffWindow'];

const LABELS: Record<string, string> = { VALLE: 'Valle', MEDIA: 'Media', PUNTA: 'Punta' };

export function toDashboardTariffType(tipo: TipoHora | null | undefined): TariffType {
  if (tipo === 'PICO') {
    return 'PUNTA';
  }
  return tipo ?? 'MEDIA';
}

export function tariffTypeLabel(type: TariffType): string {
  return LABELS[String(type).toUpperCase()] ?? String(type);
}

/** Precio de una hora de reloj (0–23). */
export function priceAtClockHour(precios: PrecioHora[], clockHour: number): PrecioHora | undefined {
  return precios.find((p) => p.hora === clockHour + 1);
}

/** Agrupa horas contiguas con la misma franja y tipo en bandas `[startHour, endHour)`. */
export function toTariffBands(precios: PrecioHora[]): TariffBand[] {
  const ordered = precios.filter((p) => p.precio != null).sort((a, b) => a.hora - b.hora);
  const bands: (TariffBand & { franja: string | null })[] = [];
  for (const p of ordered) {
    const type = toDashboardTariffType(p.tipo_hora);
    const last = bands[bands.length - 1];
    if (last && last.endHour === p.hora - 1 && last.type === type && last.franja === p.codigo_franja) {
      last.endHour = p.hora;
      continue;
    }
    bands.push({
      type,
      startHour: p.hora - 1,
      endHour: p.hora,
      energyPriceCopPerKwh: p.precio!,
      franja: p.codigo_franja,
    });
  }
  return bands.map(({ franja: _franja, ...band }) => band);
}

export function toCurrentTariffSlot(precios: PrecioHora[], clockHour: number): CurrentTariffSlot | null {
  const p = priceAtClockHour(precios, clockHour);
  if (!p || p.precio == null) {
    return null;
  }
  const type = toDashboardTariffType(p.tipo_hora);
  return {
    type,
    label: p.codigo_franja ? `${tariffTypeLabel(type)} (${p.codigo_franja})` : tariffTypeLabel(type),
    energyPriceCopPerKwh: p.precio,
  };
}

/**
 * Próxima ventana PUNTA del día (o la vigente si ya empezó).
 * `date` es el día consultado (YYYY-MM-DD); las horas se expresan en hora local.
 */
export function toNextHighTariffWindow(
  precios: PrecioHora[],
  date: string,
  clockHour: number,
): NextHighTariffWindow | null {
  const band = toTariffBands(precios).find((b) => b.type === 'PUNTA' && b.endHour > clockHour);
  if (!band) {
    return null;
  }
  const hh = (h: number) => String(h).padStart(2, '0');
  const enCurso = band.startHour <= clockHour;
  return {
    type: 'PUNTA',
    label: 'Punta',
    startsAt: localIso(date, band.startHour),
    endsAt: localIso(date, band.endHour),
    displayHint: enCurso ? `Punta ahora · hasta ${hh(band.endHour)}:00` : `Punta ${hh(band.startHour)}:00`,
  };
}

/** Costo del día: Σ kWh de cada hora de reloj × precio de esa hora. */
export function estimateDailyCostCop(precios: PrecioHora[], hourlyKwh: number[], hours?: number[]): number {
  return hourlyKwh.reduce((total, kwh, idx) => {
    const clockHour = hours?.[idx] ?? idx;
    const precio = priceAtClockHour(precios, clockHour)?.precio;
    return precio != null && Number.isFinite(kwh) ? total + kwh * precio : total;
  }, 0);
}

function localIso(date: string, clockHour: number): string {
  const [y, m, d] = date.split('-').map(Number);
  // hour 24 → 00:00 del día siguiente (Date normaliza el desbordamiento)
  return new Date(y, m - 1, d, clockHour, 0, 0).toISOString();
}
