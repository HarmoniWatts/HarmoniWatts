-- =============================================================================
-- Migración: ciudad (zona + mercado) y número de contrato en vivienda
-- Requiere el modelo TAP de tarifas (BD/Scripts/Script de Migracion SQL Completo
-- Modelo TAP Tarifas.sql): zona_geografica, mercado_red y mercado_zona.
--
-- * Amplía el catálogo de municipios (zona_geografica) con las principales
--   ciudades y las asocia a su mercado de comercialización (mercado_zona).
-- * vivienda.id_zona + vivienda.cod_mercado: ciudad y mercado de la vivienda;
--   la tarifa se resuelve con ese mercado y el estrato de la vivienda.
-- * vivienda.numero_contrato: número de contrato / cuenta con la comercializadora.
--
-- Idempotente: se puede ejecutar varias veces.
-- =============================================================================

BEGIN;

-- 1. Municipios (altura en m.s.n.m.: define el consumo de subsistencia 130/173 kWh)
INSERT INTO zona_geografica (nombre_zona, municipio, departamento, region, altura)
SELECT v.nombre_zona, v.municipio, v.departamento, v.region, v.altura
FROM (VALUES
    ('Bogotá',        'Bogotá D.C.',   'Cundinamarca',       'Andina',    2640),
    ('Soacha',        'Soacha',        'Cundinamarca',       'Andina',    2565),
    ('Medellín',      'Medellín',      'Antioquia',          'Andina',    1495),
    ('Bello',         'Bello',         'Antioquia',          'Andina',    1450),
    ('Barranquilla',  'Barranquilla',  'Atlántico',          'Caribe',      18),
    ('Santa Marta',   'Santa Marta',   'Magdalena',          'Caribe',       6),
    ('Cartagena',     'Cartagena',     'Bolívar',            'Caribe',       2),
    ('Sincelejo',     'Sincelejo',     'Sucre',              'Caribe',     213),
    ('Valledupar',    'Valledupar',    'Cesar',              'Caribe',     168),
    ('Bucaramanga',   'Bucaramanga',   'Santander',          'Andina',     959),
    ('Cúcuta',        'Cúcuta',        'Norte de Santander', 'Andina',     320),
    ('Tunja',         'Tunja',         'Boyacá',             'Andina',    2782),
    ('Manizales',     'Manizales',     'Caldas',             'Andina',    2150),
    ('Pereira',       'Pereira',       'Risaralda',          'Andina',    1411),
    ('Armenia',       'Armenia',       'Quindío',            'Andina',    1483),
    ('Ibagué',        'Ibagué',        'Tolima',             'Andina',    1285),
    ('Neiva',         'Neiva',         'Huila',              'Andina',     442),
    ('Villavicencio', 'Villavicencio', 'Meta',               'Orinoquía',  467),
    ('Pasto',         'Pasto',         'Nariño',             'Andina',    2527),
    ('Palmira',       'Palmira',       'Valle del Cauca',    'Andina',    1001),
    ('Tuluá',         'Tuluá',         'Valle del Cauca',    'Andina',     973),
    ('Cartago',       'Cartago',       'Valle del Cauca',    'Andina',     917)
) AS v(nombre_zona, municipio, departamento, region, altura)
WHERE NOT EXISTS (
    SELECT 1 FROM zona_geografica z
    WHERE z.municipio = v.municipio AND z.departamento = v.departamento
);

-- 2. Municipio -> mercado de comercialización
INSERT INTO mercado_zona (cod_mercado, id_zona)
SELECT v.cod_mercado, z.id_zona
FROM (VALUES
    ('BOGOTA',         'Bogotá D.C.',   'Cundinamarca'),
    ('BOGOTA',         'Soacha',        'Cundinamarca'),
    ('ANTIOQUIA_UNIF', 'Medellín',      'Antioquia'),
    ('ANTIOQUIA_UNIF', 'Bello',         'Antioquia'),
    ('CARIBE_SOL',     'Barranquilla',  'Atlántico'),
    ('CARIBE_SOL',     'Santa Marta',   'Magdalena'),
    ('CARIBE_MAR',     'Cartagena',     'Bolívar'),
    ('CARIBE_MAR',     'Sincelejo',     'Sucre'),
    ('CARIBE_MAR',     'Valledupar',    'Cesar'),
    ('SANTANDER',      'Bucaramanga',   'Santander'),
    ('CENS',           'Cúcuta',        'Norte de Santander'),
    ('BOYACA',         'Tunja',         'Boyacá'),
    ('CALDAS',         'Manizales',     'Caldas'),
    ('PEREIRA',        'Pereira',       'Risaralda'),
    ('QUINDIO',        'Armenia',       'Quindío'),
    ('TOLIMA',         'Ibagué',        'Tolima'),
    ('HUILA',          'Neiva',         'Huila'),
    ('META',           'Villavicencio', 'Meta'),
    ('NARINO',         'Pasto',         'Nariño'),
    ('VALLE',          'Palmira',       'Valle del Cauca'),
    ('CETSA',          'Tuluá',         'Valle del Cauca'),
    ('CARTAGO',        'Cartago',       'Valle del Cauca')
) AS v(cod_mercado, municipio, departamento)
JOIN zona_geografica z ON z.municipio = v.municipio AND z.departamento = v.departamento
ON CONFLICT (cod_mercado, id_zona) DO NOTHING;

-- 3. Columnas nuevas en vivienda (nulas: las viviendas existentes las completan en "Mi vivienda")
ALTER TABLE vivienda ADD COLUMN IF NOT EXISTS id_zona SMALLINT;
ALTER TABLE vivienda ADD COLUMN IF NOT EXISTS cod_mercado VARCHAR(30);
ALTER TABLE vivienda ADD COLUMN IF NOT EXISTS numero_contrato VARCHAR(30);

-- Ciudad y mercado van juntos y deben existir en mercado_zona
ALTER TABLE vivienda DROP CONSTRAINT IF EXISTS fk_vivienda_mercado_zona;
ALTER TABLE vivienda
    ADD CONSTRAINT fk_vivienda_mercado_zona
    FOREIGN KEY (cod_mercado, id_zona) REFERENCES mercado_zona (cod_mercado, id_zona);

ALTER TABLE vivienda DROP CONSTRAINT IF EXISTS ck_vivienda_ubicacion_completa;
ALTER TABLE vivienda
    ADD CONSTRAINT ck_vivienda_ubicacion_completa
    CHECK ((id_zona IS NULL) = (cod_mercado IS NULL));

COMMENT ON COLUMN vivienda.id_zona IS 'Municipio de la vivienda (zona_geografica)';
COMMENT ON COLUMN vivienda.cod_mercado IS 'Mercado de comercialización del municipio; con el estrato define la tarifa';
COMMENT ON COLUMN vivienda.numero_contrato IS 'Número de contrato / cuenta con la comercializadora';

COMMIT;
