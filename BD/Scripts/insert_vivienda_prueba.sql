-- 1. TRUNCATE a cliente
TRUNCATE TABLE vivienda RESTART IDENTITY CASCADE;

COMMIT;

-- =====================================================
-- Reseteo explícito de la secuencia (por si acaso)
-- =====================================================
-- Aunque TRUNCATE ... RESTART IDENTITY ya resetea,
-- ejecutamos esto por seguridad.
ALTER SEQUENCE vivienda_id_vivienda_seq RESTART WITH 1;


INSERT INTO vivienda (
    id_cliente,
    tipo,
    superficie,
    habitantes,
    direccion,
    zona_climatica
)
SELECT
    c.id_cliente,
    v.tipo_vivienda,
    v.superficie,
    v.habitantes,
    v.direccion,
    v.zona_climatica
FROM cliente c
JOIN (
    VALUES
    -- nombre           tipo_vivienda  superficie habitantes dirección                               zona
    ('MN1860D3B3B7',    'CASA',         180.00,    5,         'Girardot, Cundinamarca',            'TEMPLADA'),
    ('MN9E60ABC91C',    'APARTAMENTO',   95.00,    4,         'Santiago de Cali, Valle del Cauca', 'CALIDA'),
    ('MNC391C85C85',    'EDIFICIO',     600.00,    8,         'Girardot, Cundinamarca',            'CALIDA'),
    ('MNE5D6840091',    'LOCAL',        120.00,    3,         'Cereté, Córdoba',                   'CALIDA'),
    ('MN809B65A6F1',    'CASA',         110.00,    4,         'Montería, Córdoba',                 'CALIDA'),
    ('MND9A83DC2D2',    'CASA',         130.00,    5,         'Montería, Córdoba',                 'CALIDA'),
    ('MN157A243DFE',    'CASA',          90.00,    4,         'Caucasia, Antioquia',               'CALIDA'),
    ('MN233D2ED722',    'LOCAL',        150.00,    3,         'Santiago de Cali, Valle del Cauca', 'CALIDA'),
    ('MNDD305C0D60',    'EDIFICIO',     450.00,    6,      'Santiago de Cali, Valle del Cauca', 'CALIDA')
) AS v(
    nombre,
    tipo_vivienda,
    superficie,
    habitantes,
    direccion,
    zona_climatica
)
ON c.nombre = v.nombre;