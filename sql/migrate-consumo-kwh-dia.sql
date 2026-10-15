-- Migración: potencia_w (W) → consumo_kwh_dia (kWh/día promedio)
-- Ejecutar contra la BD harmoniwatts si el volumen ya existía.
--
-- Ejemplo:
--   docker exec -i keycloak-postgres psql -U keycloak_user -d harmoniwatts < sql/migrate-consumo-kwh-dia.sql

BEGIN;

ALTER TABLE electrodomestico
  ADD COLUMN IF NOT EXISTS consumo_kwh_dia NUMERIC(10, 4);

-- Valores antiguos típicos de watts (>= 50): no se pueden convertir sin horas → 0.01 placeholder
-- Valores pequeños (< 50) se asumen ya en kWh/día (si alguien ya los había ajustado).
UPDATE electrodomestico
SET consumo_kwh_dia = CASE
  WHEN potencia_w IS NULL THEN 0.01
  WHEN potencia_w >= 50 THEN 0.01
  ELSE potencia_w::numeric
END
WHERE consumo_kwh_dia IS NULL;

ALTER TABLE electrodomestico
  ALTER COLUMN consumo_kwh_dia SET NOT NULL;

ALTER TABLE electrodomestico
  DROP COLUMN IF EXISTS potencia_w;

COMMENT ON COLUMN electrodomestico.consumo_kwh_dia IS
  'Consumo energético promedio diario en kWh (para dashboard)';

COMMIT;
