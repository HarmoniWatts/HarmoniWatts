/**
 * Recalcula contexto_temporal desde el timestamp de cada documento (sin mover fechas).
 * Útil cuando la colección ya existía y solo faltaba alinear mes/año/hora/día/estación.
 * mongosh "mongodb://host:27017/harmoniwatts" reconcile-contexto.js
 */
const coll = db.getCollection('consumos_enriquecidos');
if (coll.countDocuments({}) === 0) {
  print('[reconcile-contexto] Colección vacía.');
  quit(0);
}

const pipeline = [
  { $set: { _tsNew: '$timestamp' } },
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
];

const r = coll.updateMany({}, pipeline);
print('[reconcile-contexto] Documentos modificados: ' + r.modifiedCount);
