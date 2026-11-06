import { test } from 'node:test';
import assert from 'node:assert/strict';
import { contratoDesdeQuery } from '../src/controllers/dashboardController.js';
import { cuentaPath } from '../src/services/consumptionService.js';

test('contratoDesdeQuery exige contrato y comercializadora', () => {
  assert.equal(contratoDesdeQuery({}), null);
  assert.equal(contratoDesdeQuery({ noContrato: '123' }), null);
  assert.equal(contratoDesdeQuery({ codComercializadora: 'ENERTOTAL' }), null);
  assert.equal(contratoDesdeQuery({ noContrato: '  ', codComercializadora: 'X' }), null);
});

test('contratoDesdeQuery normaliza los valores', () => {
  assert.deepEqual(contratoDesdeQuery({ noContrato: ' 753691 ', codComercializadora: ' enertotal ' }), {
    noContrato: '753691',
    codComercializadora: 'ENERTOTAL',
  });
});

test('cuentaPath arma la ruta del consumption-service', () => {
  assert.equal(cuentaPath({ noContrato: '75/36 91', codComercializadora: 'ENERTOTAL' }), '75%2F36%2091/ENERTOTAL');
});
