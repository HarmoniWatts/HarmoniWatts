-- =============================================================================
-- Migración: harmoniwatts — catálogos + columnas API electrodomésticos
-- =============================================================================
-- Tabla antigua (9 columnas): id_electro, id_vivienda, nombre, tipo, potencia_w,
--   es_desplazable, uso_semanal, horario_habitual, activo
-- Añade: electrodomestico_tipo_predefinido, marca_predefinida, y en electrodomestico:
--   id_tipo_predefinido, id_marca_predefinida, marca_otro
--
-- Ejecutar (ajusta usuario/clave/BD si difieren), desde la carpeta HarmoniWatts:
--
--   docker exec -i -e PGPASSWORD=TU_CLAVE keycloak-postgres \
--     psql -U keycloak_user -d harmoniwatts -v ON_ERROR_STOP=1 \
--     < sql/migrate-electrodomesticos-catalogos.sql
--
-- En PowerShell:
--   Get-Content sql/migrate-electrodomesticos-catalogos.sql -Raw | docker exec -i -e PGPASSWORD=TU_CLAVE keycloak-postgres psql -U keycloak_user -d harmoniwatts -v ON_ERROR_STOP=1
--
-- Requiere PostgreSQL 11+ (ADD COLUMN IF NOT EXISTS).
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS electrodomestico_tipo_predefinido (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nombre_es VARCHAR(100) NOT NULL,
    orden SMALLINT NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS marca_predefinida (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    orden SMALLINT NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO electrodomestico_tipo_predefinido (codigo, nombre_es, orden) VALUES
    ('LAVADORA', 'Lavadora', 10),
    ('LAVAVAJILLAS', 'Lavavajillas', 20),
    ('TERMO_ELECTRICO', 'Termo eléctrico / calentador', 30),
    ('VEHICULO_ELECTRICO', 'Vehículo eléctrico (EV)', 40),
    ('AIRE_ACONDICIONADO', 'Aire acondicionado', 50),
    ('NEVERA', 'Nevera / refrigerador', 60),
    ('CONGELADOR', 'Congelador', 70),
    ('HORNO', 'Horno', 80),
    ('MICROONDAS', 'Microondas', 90),
    ('SECADORA', 'Secadora', 100),
    ('VITROCERAMICA', 'Vitrocerámica / cocina eléctrica', 110),
    ('TELEVISOR', 'Televisor', 120),
    ('OTRO', 'Otro (personalizado)', 999)
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO marca_predefinida (nombre, orden) VALUES
    ('Samsung', 10),
    ('LG', 20),
    ('Whirlpool', 30),
    ('Bosch', 40),
    ('Mabe', 50),
    ('Electrolux', 60),
    ('Haier', 70),
    ('Panasonic', 80),
    ('Daikin', 90),
    ('Mitsubishi Electric', 100),
    ('Generico / sin marca', 200),
    ('Otro', 999)
ON CONFLICT (nombre) DO NOTHING;

ALTER TABLE electrodomestico ADD COLUMN IF NOT EXISTS id_tipo_predefinido INTEGER REFERENCES electrodomestico_tipo_predefinido(id);
ALTER TABLE electrodomestico ADD COLUMN IF NOT EXISTS id_marca_predefinida INTEGER REFERENCES marca_predefinida(id);
ALTER TABLE electrodomestico ADD COLUMN IF NOT EXISTS marca_otro VARCHAR(100);

ALTER TABLE electrodomestico DROP COLUMN IF EXISTS horario_preferente;

-- Filas existentes sin catálogo: tipo «OTRO»
UPDATE electrodomestico e
SET id_tipo_predefinido = (SELECT id FROM electrodomestico_tipo_predefinido WHERE codigo = 'OTRO' LIMIT 1)
WHERE e.id_tipo_predefinido IS NULL;

UPDATE electrodomestico SET potencia_w = 0 WHERE potencia_w IS NULL;
UPDATE electrodomestico SET es_desplazable = FALSE WHERE es_desplazable IS NULL;

-- Coherencia con JPA (nullable = false en entidad)
ALTER TABLE electrodomestico ALTER COLUMN id_tipo_predefinido SET NOT NULL;
ALTER TABLE electrodomestico ALTER COLUMN potencia_w SET NOT NULL;

COMMIT;
