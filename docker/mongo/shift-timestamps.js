/**
 * Ejecutar tras import inicial: desplaza timestamps al día UTC actual y alinea contexto_temporal.
 * mongosh "mongodb://host:27017/harmoniwatts" shift-timestamps.js
 */
const coll = db.getCollection('consumos_enriquecidos');
const minDoc = coll.find().sort({ timestamp: 1 }).limit(1).toArray()[0];
if (!minDoc) {
  print('[shift] Sin documentos, nada que hacer.');
  quit(0);
}
const now = new Date();
const todayUtc = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
const minOld = new Date(
  Date.UTC(
    minDoc.timestamp.getUTCFullYear(),
    minDoc.timestamp.getUTCMonth(),
    minDoc.timestamp.getUTCDate(),
  ),
);
const deltaMs = todayUtc - minOld;
if (deltaMs === 0) {
  print('[shift] delta 0, sin desplazamiento (usar reconcile-contexto.js si falta contexto_temporal).');
  quit(0);
}

const r = coll.updateMany(
  {},
  [
    {
      $set: {
        timestamp: { $add: ['$timestamp', deltaMs] },
        _tsNew: { $add: ['$timestamp', deltaMs] },
      },
    },
    {
      $set: {
        'contexto_temporal.dia_semana': { $isoDayOfWeek: '$_tsNew' },
        'contexto_temporal.es_festivo': { $ifNull: ['$contexto_temporal.es_festivo', false] },
        'contexto_temporal.hora_del_dia': { $hour: '$_tsNew' },
        'contexto_temporal.mes': { $month: '$_tsNew' },
        'contexto_temporal.anio': { $year: '$_tsNew' },
        'contexto_temporal.estacion': {
          $let: {
            vars: { m: { $month: '$_tsNew' } },
            in: {
              $switch: {
                branches: [
                  { case: { $in: ['$$m', [12, 1, 2]] }, then: 'invierno' },
                  { case: { $in: ['$$m', [3, 4, 5]] }, then: 'primavera' },
                  { case: { $in: ['$$m', [6, 7, 8]] }, then: 'verano' },
                  { case: { $in: ['$$m', [9, 10, 11]] }, then: 'otoño' },
                ],
                default: 'primavera',
              },
            },
          },
        },
      },
    },
    { $unset: '_tsNew' },
  ],
);

print('[shift] Documentos modificados: ' + r.modifiedCount);
