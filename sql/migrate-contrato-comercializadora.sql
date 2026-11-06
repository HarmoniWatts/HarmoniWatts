-- =============================================================================
-- Migración: consumos por número de contrato + comercializadora (HAR-107)
--
-- Los consumos (MongoDB, consumption-service) se identifican por la pareja
-- (no_contrato, cod_comercializadora): el contrato solo es único dentro de su
-- comercializadora.
--
-- * vivienda.cod_comercializadora: comercializadora con la que la vivienda tiene
--   el contrato (vivienda.numero_contrato ya existe, ver
--   migrate-vivienda-ciudad-contrato.sql). El dashboard consulta los consumos
--   de la vivienda seleccionada con esa pareja.
-- * cliente.no_contrato: contrato del cliente (lo usa la sincronización con la
--   comercializadora para resolver la tarifa del cliente).
--
-- Idempotente: se puede ejecutar varias veces.
-- =============================================================================

BEGIN;

-- 1. Vivienda: comercializadora del contrato
ALTER TABLE vivienda ADD COLUMN IF NOT EXISTS numero_contrato VARCHAR(30);
ALTER TABLE vivienda ADD COLUMN IF NOT EXISTS cod_comercializadora VARCHAR(20);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_vivienda_comercializadora') THEN
        ALTER TABLE vivienda
            ADD CONSTRAINT fk_vivienda_comercializadora
            FOREIGN KEY (cod_comercializadora) REFERENCES comercializadora (cod_comercializadora);
    END IF;
END $$;

-- Un mismo contrato de una comercializadora no puede quedar en dos viviendas
CREATE UNIQUE INDEX IF NOT EXISTS uq_vivienda_contrato_comercializadora
    ON vivienda (cod_comercializadora, numero_contrato)
    WHERE cod_comercializadora IS NOT NULL AND numero_contrato IS NOT NULL;

COMMENT ON COLUMN vivienda.numero_contrato IS 'Número de contrato / cuenta con la comercializadora';
COMMENT ON COLUMN vivienda.cod_comercializadora IS 'Comercializadora del contrato (con numero_contrato identifica los consumos)';

-- Las viviendas que ya tenían contrato quedan con la única comercializadora activa
UPDATE vivienda
SET cod_comercializadora = (SELECT cod_comercializadora FROM comercializadora
                            WHERE activo ORDER BY cod_comercializadora LIMIT 1)
WHERE numero_contrato IS NOT NULL AND btrim(numero_contrato) <> ''
  AND cod_comercializadora IS NULL
  AND (SELECT count(*) FROM comercializadora WHERE activo) = 1;

-- 2. Cliente: número de contrato
ALTER TABLE cliente ADD COLUMN IF NOT EXISTS no_contrato VARCHAR(50);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_cliente_cuenta_comercializadora') THEN
        ALTER TABLE cliente
            ADD CONSTRAINT uq_cliente_cuenta_comercializadora UNIQUE (no_contrato, cod_comercializadora);
    END IF;
END $$;

COMMENT ON COLUMN cliente.no_contrato IS 'Número de contrato / cuenta con la comercializadora';

COMMIT;
