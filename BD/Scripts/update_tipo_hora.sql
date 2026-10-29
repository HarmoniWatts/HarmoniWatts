-- =====================================================================
-- Define configuracion_franja.tipo_hora (VALLE / MEDIA / PICO)
--
-- Regla, según las horas que tiene cada franja en su configuración
-- (hora 1 = 00:00-01:00 ... hora 24 = 23:00-24:00):
--   PICO  : la franja incluye alguna hora entre 19 y 21 (18:00-21:00)
--   VALLE : todas sus horas son 1, 2, 3, 4 o 24 (23:00-04:00)
--   MEDIA : el resto
--
-- Solo actualiza filas con tipo_hora NULL (no pisa cambios manuales).
-- Para recalcular todo, quitar la condición "cf.tipo_hora IS NULL".
-- =====================================================================

BEGIN;

UPDATE configuracion_franja cf
SET tipo_hora = t.tipo
FROM (
    SELECT h.id_configuracion_horaria,
           h.id_franja_horaria,
           CASE
               WHEN bool_or(h.hora BETWEEN 19 AND 21)    THEN 'PICO'
               WHEN bool_and(h.hora IN (1, 2, 3, 4, 24)) THEN 'VALLE'
               ELSE 'MEDIA'
           END AS tipo
    FROM configuracion_hora h
    GROUP BY h.id_configuracion_horaria, h.id_franja_horaria
) t
WHERE cf.id_configuracion_horaria = t.id_configuracion_horaria
  AND cf.id_franja_horaria        = t.id_franja_horaria
  AND cf.tipo_hora IS NULL;

-- Verificación 1: no debe quedar ninguna franja sin tipo (resultado esperado: 0)
SELECT count(*) AS sin_tipo FROM configuracion_franja WHERE tipo_hora IS NULL;

-- Verificación 2: franjas por configuración y tipo
SELECT c.codigo AS configuracion,
       string_agg(f.codigo, ', ' ORDER BY f.codigo) FILTER (WHERE cf.tipo_hora = 'VALLE') AS valle,
       string_agg(f.codigo, ', ' ORDER BY f.codigo) FILTER (WHERE cf.tipo_hora = 'MEDIA') AS media,
       string_agg(f.codigo, ', ' ORDER BY f.codigo) FILTER (WHERE cf.tipo_hora = 'PICO')  AS pico
FROM configuracion_franja cf
JOIN configuracion_horaria c ON c.id_configuracion_horaria = cf.id_configuracion_horaria
JOIN franja_horaria f        ON f.id_franja_horaria        = cf.id_franja_horaria
GROUP BY c.codigo
ORDER BY c.codigo;

COMMIT;
