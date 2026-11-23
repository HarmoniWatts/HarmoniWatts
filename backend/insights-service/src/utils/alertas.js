/**
 * Alertas visuales (HAR-21). Funciones puras: reciben precios / lecturas ya en hora local.
 *
 * - Franja de alto precio: en punta ahora (ALTA), empieza en ≤ 60 min (MEDIA) o en ≤ 3 h (BAJA).
 * - Consumo sobre lo habitual: última hora leída y acumulado del día frente al promedio de las
 *   mismas horas en las 4 semanas anteriores. +30 % BAJA, +60 % MEDIA, +100 % ALTA.
 */

export const SEVERIDAD = { LOW: 'LOW', MEDIUM: 'MEDIUM', HIGH: 'HIGH' };
const ORDEN = { HIGH: 0, MEDIUM: 1, LOW: 2 };

/** Umbrales del exceso de consumo (fracción sobre el promedio). */
export const UMBRALES_CONSUMO = [
  { min: 1.0, severidad: SEVERIDAD.HIGH },
  { min: 0.6, severidad: SEVERIDAD.MEDIUM },
  { min: 0.3, severidad: SEVERIDAD.LOW },
];
export const MINUTOS_PUNTA_PRONTO = { MEDIUM: 60, LOW: 180 };
/** Días previos mínimos para que el promedio sea representativo. */
export const MIN_DIAS_HISTORIA = 5;
/** Diferencias mínimas en kWh para no alertar por variaciones mínimas. */
const MIN_DIFF_HORA = 0.05;
const MIN_DIFF_DIA = 0.3;

const hh = (h) => `${String(h % 24).padStart(2, '0')}:00`;
const pct = (v) => Math.round(v * 100);
const r2 = (v) => Math.round(v * 100) / 100;

export function severidadExceso(exceso) {
  return UMBRALES_CONSUMO.find((u) => exceso >= u.min)?.severidad ?? null;
}

/** Tipo de hora 0–23 ('VALLE' | 'MEDIA' | 'PICO') y precio, desde precios[] de tariff-service (hora 1–24). */
function porHora(precios) {
  const tipos = Array(24).fill(null);
  const valor = Array(24).fill(null);
  for (const p of precios ?? []) {
    if (p.hora >= 1 && p.hora <= 24) {
      tipos[p.hora - 1] = p.tipo_hora;
      valor[p.hora - 1] = p.precio;
    }
  }
  return { tipos, valor };
}

/** [inicio, fin) del bloque de punta que contiene la hora h. */
function bloque(tipos, h) {
  let ini = h;
  let fin = h;
  while (ini > 0 && tipos[ini - 1] === 'PICO') ini--;
  while (fin < 24 && tipos[fin] === 'PICO') fin++;
  return [ini, fin];
}

/**
 * @param precios precios[] de la tarifa vigente
 * @param ahora { fecha: 'YYYY-MM-DD', hora: 0–23, minuto: 0–59 } en hora local
 */
export function alertasFranja(precios, ahora) {
  const { tipos, valor } = porHora(precios);
  if (!tipos.some((t) => t === 'PICO')) return [];
  const precioValle = Math.min(...valor.filter((v, i) => v != null && tipos[i] === 'VALLE'));
  const masQueValle = (p) =>
    Number.isFinite(precioValle) && precioValle > 0 && p != null ? ` (${pct(p / precioValle - 1)} % más que en valle)` : '';

  if (tipos[ahora.hora] === 'PICO') {
    const [ini, fin] = bloque(tipos, ahora.hora);
    const precio = valor[ahora.hora];
    return [
      {
        id: `franja-punta-${ahora.fecha}-${ini}`,
        type: 'TARIFF_PEAK',
        severity: SEVERIDAD.HIGH,
        title: 'Estás en franja de punta',
        message:
          `La energía está en su precio más alto hasta las ${hh(fin)}: ` +
          `${Math.round(precio ?? 0).toLocaleString('es-CO')} COP/kWh${masQueValle(precio)}. ` +
          'Aplaza lavadora, secadora o carga del vehículo si puedes.',
        timestamp: `${ahora.fecha}T${hh(ini)}:00`,
        data: { startHour: ini, endHour: fin, priceCopPerKwh: precio },
      },
    ];
  }

  // Próxima hora de punta hoy después de la actual
  const prox = tipos.findIndex((t, i) => i > ahora.hora && t === 'PICO');
  if (prox < 0) return [];
  const minutos = prox * 60 - (ahora.hora * 60 + ahora.minuto);
  const severidad =
    minutos <= MINUTOS_PUNTA_PRONTO.MEDIUM ? SEVERIDAD.MEDIUM : minutos <= MINUTOS_PUNTA_PRONTO.LOW ? SEVERIDAD.LOW : null;
  if (!severidad) return [];
  const [, fin] = bloque(tipos, prox);
  const precio = valor[prox];
  return [
    {
      id: `franja-punta-pronto-${ahora.fecha}-${prox}`,
      type: 'TARIFF_PEAK_SOON',
      severity: severidad,
      title: `La franja de punta empieza a las ${hh(prox)}`,
      message:
        `En ${minutos} min entras a la franja de precio más alto (${hh(prox)}–${hh(fin)}): ` +
        `${Math.round(precio ?? 0).toLocaleString('es-CO')} COP/kWh${masQueValle(precio)}. ` +
        'Es buen momento para adelantar los consumos grandes.',
      timestamp: `${ahora.fecha}T${hh(ahora.hora)}:${String(ahora.minuto).padStart(2, '0')}`,
      data: { startHour: prox, endHour: fin, minutesToStart: minutos, priceCopPerKwh: precio },
    },
  ];
}

/**
 * @param lecturas [{ ts: 'YYYY-MM-DDTHH:mm:ss' (hora local), kwh }] ordenadas o no
 */
export function alertasConsumo(lecturas) {
  const ls = (lecturas ?? []).filter((l) => l?.ts && Number.isFinite(l.kwh)).sort((a, b) => a.ts.localeCompare(b.ts));
  if (!ls.length) return [];
  const ultima = ls[ls.length - 1];
  const fecha = ultima.ts.slice(0, 10);
  const hora = Number(ultima.ts.slice(11, 13));

  // Lecturas de días anteriores agrupadas por día
  const dias = new Map();
  for (const l of ls) {
    const d = l.ts.slice(0, 10);
    if (d >= fecha) continue;
    if (!dias.has(d)) dias.set(d, new Map());
    dias.get(d).set(Number(l.ts.slice(11, 13)), l.kwh);
  }
  const out = [];

  // 1) Última hora vs promedio de esa misma hora
  const mismasHoras = [...dias.values()].map((m) => m.get(hora)).filter((v) => v != null);
  if (mismasHoras.length >= MIN_DIAS_HISTORIA) {
    const prom = mismasHoras.reduce((a, b) => a + b, 0) / mismasHoras.length;
    const exceso = prom > 0 ? ultima.kwh / prom - 1 : 0;
    const sev = severidadExceso(exceso);
    if (sev && ultima.kwh - prom >= MIN_DIFF_HORA) {
      out.push({
        id: `consumo-hora-${ultima.ts.slice(0, 13)}`,
        type: 'CONSUMPTION_HOUR',
        severity: sev,
        title: `Consumo alto a las ${hh(hora)}`,
        message:
          `Entre las ${hh(hora)} y las ${hh(hora + 1)} consumiste ${r2(ultima.kwh).toLocaleString('es-CO')} kWh, ` +
          `${pct(exceso)} % más que tu promedio a esa hora (${r2(prom).toLocaleString('es-CO')} kWh).`,
        timestamp: ultima.ts,
        data: { kwh: r2(ultima.kwh), averageKwh: r2(prom), excessPct: pct(exceso), hour: hora },
      });
    }
  }

  // 2) Acumulado del día (hasta la última hora leída) vs promedio de los mismos tramos
  const hoy = ls.filter((l) => l.ts.startsWith(fecha));
  const completos = [...dias.values()].filter((m) => [...Array(hora + 1).keys()].every((h) => m.has(h)));
  if (hoy.length === hora + 1 && completos.length >= MIN_DIAS_HISTORIA) {
    const acumHoy = hoy.reduce((a, l) => a + l.kwh, 0);
    const prom =
      completos.map((m) => [...Array(hora + 1).keys()].reduce((a, h) => a + m.get(h), 0)).reduce((a, b) => a + b, 0) /
      completos.length;
    const exceso = prom > 0 ? acumHoy / prom - 1 : 0;
    const sev = severidadExceso(exceso);
    if (sev && acumHoy - prom >= MIN_DIFF_DIA) {
      out.push({
        id: `consumo-dia-${fecha}-${sev}`,
        type: 'CONSUMPTION_DAY',
        severity: sev,
        title: 'Hoy vas consumiendo más de lo habitual',
        message:
          `Hasta las ${hh(hora + 1)} llevas ${r2(acumHoy).toLocaleString('es-CO')} kWh, ` +
          `${pct(exceso)} % más que tu promedio a esta hora (${r2(prom).toLocaleString('es-CO')} kWh).`,
        timestamp: ultima.ts,
        data: { kwh: r2(acumHoy), averageKwh: r2(prom), excessPct: pct(exceso), untilHour: hora + 1 },
      });
    }
  }
  return out;
}

/** Más graves primero; a igual severidad, más recientes primero. */
export function ordenarAlertas(alertas) {
  return [...alertas].sort((a, b) => ORDEN[a.severity] - ORDEN[b.severity] || b.timestamp.localeCompare(a.timestamp));
}
