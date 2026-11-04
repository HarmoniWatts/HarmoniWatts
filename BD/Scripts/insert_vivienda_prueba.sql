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
    ('MN57A84E9C8C',    'CASA',         180.00,    5,         'Popayán, Cauca',                     'TEMPLADA'),
    ('MN3053A27FAA',    'APARTAMENTO',   95.00,    4,         'Santiago de Cali, Valle del Cauca', 'CALIDA'),
    ('MNB22B64A8E3',    'EDIFICIO',     600.00,    8,         'Girardot, Cundinamarca',            'CALIDA'),
    ('MN53EF93833D',    'LOCAL',        120.00,    3,         'Cereté, Córdoba',                   'CALIDA'),
    ('MN4B45F58D3C',    'CASA',         110.00,    4,         'Montería, Córdoba',                 'CALIDA'),
    ('MN4A59921A8B',    'CASA',         130.00,    5,         'Montería, Córdoba',                 'CALIDA'),
    ('MNE067834B30',    'CASA',          90.00,    4,         'Caucasia, Antioquia',               'CALIDA'),
    ('MN4ABA1F08F8',    'LOCAL',        150.00,    3,         'Santiago de Cali, Valle del Cauca', 'CALIDA'),
    ('MN5EE61A9F74',    'EDIFICIO',     450.00,    6,      'Santiago de Cali, Valle del Cauca', 'CALIDA')
) AS v(
    nombre,
    tipo_vivienda,
    superficie,
    habitantes,
    direccion,
    zona_climatica
)
ON c.nombre = v.nombre;