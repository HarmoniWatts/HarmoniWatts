/**
 * Los consumos se consultan por (no_contrato, cod_comercializadora). Los datos demo
 * (BD/datos/harmoniwatts.consumos_enriquecidos.json) solo traen id_vivienda; este
 * script les asigna el contrato demo para que se vean en el dashboard.
 *
 * Para verlos: registra una vivienda con número de contrato 45754113 y
 * comercializadora ENERTOTAL en "Mi vivienda".
 *
 * Idempotente. mongosh "mongodb://host:27017/harmoniwatts" asignar-contrato-demo.js
 */
const coll = db.getCollection('consumos_enriquecidos');
const res = coll.updateMany(
  { id_vivienda: 45754113, no_contrato: { $exists: false } },
  { $set: { no_contrato: '45754113', cod_comercializadora: 'ENERTOTAL' } },
);
print(`[asignar-contrato-demo] ${res.modifiedCount} documentos con contrato demo 45754113/ENERTOTAL.`);

coll.createIndex(
  { cod_comercializadora: 1, no_contrato: 1, timestamp: 1 },
  { name: 'idx_comercializadora_contrato_timestamp' },
);
