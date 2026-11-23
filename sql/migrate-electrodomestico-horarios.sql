-- =============================================================================
-- Migración HAR-20: estimación de consumo por electrodoméstico
-- =============================================================================
-- Añade:
--   * electrodomestico.potencia_w              potencia nominal (W) para estimar por horario
--   * electrodomestico.consumo_ajustado_kwh_mes ajuste manual del usuario (datos más precisos)
--   * tabla electrodomestico_horario          franjas de uso por día de la semana
--
-- Ejecutar desde la carpeta HarmoniWatts (PowerShell):
--   Get-Content sql/migrate-electrodomestico-horarios.sql -Raw | docker exec -i keycloak-postgres psql -U keycloak_user -d harmoniwatts -v ON_ERROR_STOP=1
--
-- Idempotente (IF NOT EXISTS).
-- =============================================================================

BEGIN;

ALTER TABLE electrodomestico ADD COLUMN IF NOT EXISTS potencia_w NUMERIC(10,2);
ALTER TABLE electrodomestico ADD COLUMN IF NOT EXISTS consumo_ajustado_kwh_mes NUMERIC(10,3);

COMMENT ON COLUMN electrodomestico.potencia_w IS 'Potencia nominal en vatios; con los horarios permite estimar kWh';
COMMENT ON COLUMN electrodomestico.consumo_ajustado_kwh_mes IS 'Consumo mensual indicado por el usuario (prevalece sobre la estimación)';

CREATE TABLE IF NOT EXISTS electrodomestico_horario (
    id_horario   BIGSERIAL PRIMARY KEY,
    id_electro   BIGINT   NOT NULL REFERENCES electrodomestico(id_electro) ON DELETE CASCADE,
    -- ISO-8601: 1 = lunes … 7 = domingo
    dia_semana   SMALLINT NOT NULL CHECK (dia_semana BETWEEN 1 AND 7),
    hora_inicio  TIME     NOT NULL,
    -- Si hora_fin <= hora_inicio la franja cruza la medianoche (p. ej. 22:00–06:00)
    hora_fin     TIME     NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_electro_horario_electro ON electrodomestico_horario(id_electro);

COMMENT ON TABLE electrodomestico_horario IS 'Franjas en las que el usuario usa cada electrodoméstico (HAR-20)';

COMMIT;
