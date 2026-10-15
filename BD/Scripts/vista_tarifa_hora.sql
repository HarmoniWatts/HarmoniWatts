-- =====================================================================
-- VISTA v_tarifa_hora: precio de cada hora (1..24) por tarifa y período
--
-- Une: tarifa_valor -> configuracion_hora (hora de cada franja) ->
--      configuracion_horaria (código de la configuración) ->
--      franja_horaria (código de la franja)
-- y, para que la vista sea útil, también: periodo_tarifario y tarifa
-- (identifican de qué tarifa y mes es el precio) y configuracion_franja
-- (tipo_hora: VALLE / MEDIA / PICO).
--
-- Una fila = una hora de un período de una tarifa. Cada franja se expande a
-- sus horas, por lo que un período con franjas F1..F5 genera 24 filas.
-- Las filas de monomia (sin franja) no aparecen: no tienen hora asociada.
-- La vista incluye todos los estados; filtrar con estado = 'PUBLICADA'.
-- =====================================================================

CREATE OR REPLACE VIEW v_tarifa_hora AS
SELECT
    -- Tarifa
    t.id_tarifa,
    t.codigo_tarifa,
    t.cod_comercializadora,
    t.cod_mercado,
    t.cod_nivel,
    t.cod_tipo_tarifa,
    -- Período
    p.id_periodo_tarifario,
    p.anio,
    p.mes,
    p.fecha_inicio,
    p.fecha_fin,
    p.numero_version,
    p.estado,
    -- Configuración horaria (NULL en monomias sencillas)
    COALESCE(tv.id_configuracion_horaria, p.id_configuracion_horaria) AS id_configuracion_horaria,
    ch.codigo AS configuracion,
    -- Hora (NULL en monomias sencillas)
    h.hora,
    -- Franja (NULL en monomias sencillas)
    tv.id_franja_horaria,
    f.codigo AS franja,
    f.tipo_dia,
    cf.tipo_hora,
    -- Valor (siempre presente)
    tv.valor,
    tv.unidad
FROM tarifa_valor tv
JOIN periodo_tarifario p     ON p.id_periodo_tarifario     = tv.id_periodo_tarifario
JOIN tarifa t                ON t.id_tarifa                = p.id_tarifa
-- LEFT JOINs para permitir NULL en franja y configuración
LEFT JOIN configuracion_horaria ch 
    ON ch.id_configuracion_horaria = tv.id_configuracion_horaria
LEFT JOIN configuracion_hora h 
    ON h.id_configuracion_horaria = tv.id_configuracion_horaria
   AND h.id_franja_horaria        = tv.id_franja_horaria
LEFT JOIN franja_horaria f 
    ON f.id_franja_horaria = tv.id_franja_horaria
LEFT JOIN configuracion_franja cf 
    ON cf.id_configuracion_horaria = tv.id_configuracion_horaria
   AND cf.id_franja_horaria        = tv.id_franja_horaria;

COMMENT ON VIEW v_tarifa_hora IS
    'Precio por hora (1..24) de cada tarifa y período: tarifa_valor + configuración + hora + franja. '
    'Soporta monomias sencillas (id_franja_horaria NULL e id_configuracion_horaria NULL).';
	
-- Ejemplo: precio de las 24 horas de CALI N1_1 tipo A el 15 de octubre de 2025
--   SELECT hora, franja, tipo_hora, valor
--   FROM v_tarifa_hora
--   WHERE codigo_tarifa = 'CALI-N1_1-A'
--     AND estado = 'PUBLICADA'
--     AND DATE '2025-10-15' BETWEEN fecha_inicio AND fecha_fin
--   ORDER BY hora;
