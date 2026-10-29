-- =====================================================================
-- Vistas e índices para los endpoints históricos (/tariff/historical)
-- Ejecutar después de crear las tablas del modelo TAP. Es re-ejecutable.
--
--   v_periodo_publicado       1 fila por período PUBLICADA (tarifa + período + configuración).
--                             Centraliza la regla "solo PUBLICADA" para que el código no la repita.
--   v_tarifa_publicada_hora   1 fila por hora (1..24) de cada período PUBLICADA. Excluye la monomia
--                             (no tiene hora). Un AVG sobre esta vista es un promedio ponderado por horas.
--
-- Son vistas propias de este módulo: no dependen de v_tarifa_hora, así que los
-- cambios en esa vista no afectan a los endpoints históricos.
-- =====================================================================

BEGIN;

CREATE OR REPLACE VIEW v_periodo_publicado AS
SELECT
    p.id_periodo_tarifario,
    t.id_tarifa,
    t.codigo_tarifa,
    t.nombre_tarifa,
    t.cod_comercializadora,
    t.cod_mercado,
    t.cod_nivel,
    t.cod_tipo_tarifa,
    t.resolucion_regulatoria,
    p.anio,
    p.mes,
    p.fecha_inicio,
    p.fecha_fin,
    p.numero_version,
    p.fecha_publicacion,
    p.id_configuracion_horaria,
    ch.codigo AS configuracion
FROM periodo_tarifario p
JOIN tarifa t                      ON t.id_tarifa = p.id_tarifa
LEFT JOIN configuracion_horaria ch ON ch.id_configuracion_horaria = p.id_configuracion_horaria
WHERE p.estado = 'PUBLICADA';

CREATE OR REPLACE VIEW v_tarifa_publicada_hora AS
SELECT
    pp.id_periodo_tarifario,
    pp.id_tarifa,
    pp.codigo_tarifa,
    pp.cod_comercializadora,
    pp.cod_mercado,
    pp.cod_nivel,
    pp.cod_tipo_tarifa,
    pp.anio,
    pp.mes,
    pp.id_configuracion_horaria,
    pp.configuracion,
    h.hora,
    f.codigo  AS codigo_franja,
    cf.tipo_hora,
    tv.valor,
    tv.unidad
FROM v_periodo_publicado pp
JOIN tarifa_valor tv          ON tv.id_periodo_tarifario     = pp.id_periodo_tarifario
JOIN configuracion_hora h     ON h.id_configuracion_horaria  = tv.id_configuracion_horaria
                             AND h.id_franja_horaria         = tv.id_franja_horaria
JOIN franja_horaria f         ON f.id_franja_horaria         = tv.id_franja_horaria
JOIN configuracion_franja cf  ON cf.id_configuracion_horaria = tv.id_configuracion_horaria
                             AND cf.id_franja_horaria        = tv.id_franja_horaria;

COMMENT ON VIEW v_periodo_publicado IS
    'Períodos tarifarios PUBLICADA con los datos de su tarifa y su configuración horaria';
COMMENT ON VIEW v_tarifa_publicada_hora IS
    'Precio de cada hora (1..24) de los períodos PUBLICADA; excluye monomia';

-- Índices para las búsquedas por mes y por combinación de tarifa
CREATE INDEX IF NOT EXISTS idx_periodo_publicado_anio_mes
    ON periodo_tarifario (anio, mes) WHERE estado = 'PUBLICADA';

CREATE INDEX IF NOT EXISTS idx_tarifa_combinacion
    ON tarifa (cod_comercializadora, cod_mercado, cod_nivel, cod_tipo_tarifa);
	
	
CREATE OR REPLACE VIEW v_tarifa_hora AS
SELECT
    tv.id_tarifa_valor,        -- PK natural
    t.id_tarifa,
    t.codigo_tarifa,
    t.cod_comercializadora,
    t.cod_mercado,
    t.cod_nivel,
    t.cod_tipo_tarifa,
    p.id_periodo_tarifario,
    p.anio,
    p.mes,
    p.fecha_inicio,
    p.fecha_fin,
    p.numero_version,
    p.estado,
    COALESCE(tv.id_configuracion_horaria, p.id_configuracion_horaria) AS id_configuracion_horaria,
    ch.codigo   AS configuracion,
    h.hora,                    -- NULL si es monomia
    tv.id_franja_horaria,      -- NULL si es monomia
    f.codigo    AS franja,     -- NULL si es monomia
    f.tipo_dia,
    cf.tipo_hora,              -- NULL si es monomia
    tv.valor,
    tv.unidad
FROM tarifa_valor tv
JOIN periodo_tarifario p ON p.id_periodo_tarifario = tv.id_periodo_tarifario
JOIN tarifa t ON t.id_tarifa = p.id_tarifa
LEFT JOIN configuracion_horaria ch ON ch.id_configuracion_horaria = tv.id_configuracion_horaria
LEFT JOIN configuracion_hora h ON h.id_configuracion_horaria = tv.id_configuracion_horaria
                              AND h.id_franja_horaria = tv.id_franja_horaria
LEFT JOIN franja_horaria f ON f.id_franja_horaria = tv.id_franja_horaria
LEFT JOIN configuracion_franja cf ON cf.id_configuracion_horaria = tv.id_configuracion_horaria
                                  AND cf.id_franja_horaria = tv.id_franja_horaria;

COMMIT;

-- Prueba rápida:
--   SELECT anio, mes, round(avg(valor), 2) AS promedio
--   FROM v_tarifa_publicada_hora
--   WHERE cod_comercializadora = 'ENERTOTAL' AND cod_mercado = 'CALI'
--     AND cod_nivel = 'N1_1' AND cod_tipo_tarifa = 'A'
--   GROUP BY anio, mes ORDER BY anio, mes;
