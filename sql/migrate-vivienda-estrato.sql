-- Añade estrato (1–6) a vivienda en bases ya existentes.
-- Ejecutar una vez contra `harmoniwatts` (p. ej. desde DBeaver o:
--   docker exec -i keycloak-postgres psql -U "$POSTGRES_USER" -d harmoniwatts < sql/migrate-vivienda-estrato.sql
-- Usar INTEGER para alinear con el mapeo JPA `Integer` y `ddl-auto: validate`.
ALTER TABLE vivienda ADD COLUMN IF NOT EXISTS estrato INTEGER;
UPDATE vivienda SET estrato = 3 WHERE estrato IS NULL;
ALTER TABLE vivienda ALTER COLUMN estrato SET NOT NULL;
ALTER TABLE vivienda ALTER COLUMN estrato SET DEFAULT 3;
DO $$
BEGIN
  ALTER TABLE vivienda ADD CONSTRAINT vivienda_estrato_chk CHECK (estrato >= 1 AND estrato <= 6);
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;
COMMENT ON COLUMN vivienda.estrato IS 'Estrato socioeconómico del servicio (1–6, Colombia)';
