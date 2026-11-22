INSERT INTO configuracion_franja (id_configuracion_horaria, id_franja_horaria, tipo_hora)
SELECT v.a, v.b, v.c
FROM (VALUES
    (1,6,'PICO'),(5,6,'PICO'),(5,8,'PICO'),(8,7,'PICO'),
    (8,8,'PICO'),(9,7,'PICO'),(10,7,'PICO')
) AS v(a,b,c)
WHERE NOT EXISTS (
    SELECT 1 FROM configuracion_franja cf
    WHERE cf.id_configuracion_horaria = v.a
      AND cf.id_franja_horaria      = v.b
);
