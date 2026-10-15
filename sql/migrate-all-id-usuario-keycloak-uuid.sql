-- =============================================================================
-- Keycloak: el claim "sub" es un UUID (formato estándar 36 caracteres con guiones).
-- Migración: unificar en id_usuario VARCHAR(36) en vivienda, tarifausuario, conexionexterna.
-- =============================================================================
-- Casos:
--   A) Solo id_usuario BIGINT → sustituye por VARCHAR placeholder (actualiza luego con sub real).
--   B) Solo keycloak_user_id VARCHAR → RENAME a id_usuario.
--   C) id_usuario BIGINT + keycloak_user_id VARCHAR → elimina BIGINT y renombra keycloak → id_usuario.
--   D) id_usuario ya VARCHAR → solo elimina keycloak_user_id si sobra.
-- =============================================================================

BEGIN;

DROP VIEW IF EXISTS v_recomendaciones_pendientes;
DROP VIEW IF EXISTS v_usuarios_tarifa_activa;

ALTER TABLE vivienda DROP CONSTRAINT IF EXISTS fk_vivienda_usuario;
ALTER TABLE tarifausuario DROP CONSTRAINT IF EXISTS fk_tarifausuario_usuario;
ALTER TABLE conexionexterna DROP CONSTRAINT IF EXISTS fk_conexion_usuario;

-- vivienda
DO $$
DECLARE
  has_id boolean;
  has_kc boolean;
  dt_id  text;
BEGIN
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'vivienda' AND column_name = 'id_usuario'
  ) INTO has_id;
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'vivienda' AND column_name = 'keycloak_user_id'
  ) INTO has_kc;

  IF has_id THEN
    SELECT c.data_type INTO dt_id FROM information_schema.columns c
    WHERE c.table_schema = 'public' AND c.table_name = 'vivienda' AND c.column_name = 'id_usuario';
  ELSE
    dt_id := NULL;
  END IF;

  IF has_kc AND has_id AND dt_id = 'bigint' THEN
    ALTER TABLE vivienda DROP COLUMN id_usuario;
    ALTER TABLE vivienda RENAME COLUMN keycloak_user_id TO id_usuario;
  ELSIF has_id AND dt_id = 'bigint' THEN
    ALTER TABLE vivienda ADD COLUMN _mig_u VARCHAR(36);
    UPDATE vivienda SET _mig_u = '00000000-0000-0000-0000-000000000000';
    ALTER TABLE vivienda DROP COLUMN id_usuario;
    ALTER TABLE vivienda RENAME COLUMN _mig_u TO id_usuario;
    ALTER TABLE vivienda ALTER COLUMN id_usuario SET NOT NULL;
  ELSIF NOT has_id AND has_kc THEN
    ALTER TABLE vivienda RENAME COLUMN keycloak_user_id TO id_usuario;
  END IF;
END $$;

ALTER TABLE vivienda DROP COLUMN IF EXISTS keycloak_user_id;

-- tarifausuario
DO $$
DECLARE
  has_id boolean;
  has_kc boolean;
  dt_id  text;
BEGIN
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'tarifausuario' AND column_name = 'id_usuario'
  ) INTO has_id;
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'tarifausuario' AND column_name = 'keycloak_user_id'
  ) INTO has_kc;

  IF has_id THEN
    SELECT c.data_type INTO dt_id FROM information_schema.columns c
    WHERE c.table_schema = 'public' AND c.table_name = 'tarifausuario' AND c.column_name = 'id_usuario';
  ELSE
    dt_id := NULL;
  END IF;

  IF has_kc AND has_id AND dt_id = 'bigint' THEN
    ALTER TABLE tarifausuario DROP COLUMN id_usuario;
    ALTER TABLE tarifausuario RENAME COLUMN keycloak_user_id TO id_usuario;
  ELSIF has_id AND dt_id = 'bigint' THEN
    ALTER TABLE tarifausuario ADD COLUMN _mig_u VARCHAR(36);
    UPDATE tarifausuario SET _mig_u = '00000000-0000-0000-0000-000000000000';
    ALTER TABLE tarifausuario DROP COLUMN id_usuario;
    ALTER TABLE tarifausuario RENAME COLUMN _mig_u TO id_usuario;
    ALTER TABLE tarifausuario ALTER COLUMN id_usuario SET NOT NULL;
  ELSIF NOT has_id AND has_kc THEN
    ALTER TABLE tarifausuario RENAME COLUMN keycloak_user_id TO id_usuario;
  END IF;
END $$;

ALTER TABLE tarifausuario DROP COLUMN IF EXISTS keycloak_user_id;

-- conexionexterna
DO $$
DECLARE
  has_id boolean;
  has_kc boolean;
  dt_id  text;
BEGIN
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'conexionexterna' AND column_name = 'id_usuario'
  ) INTO has_id;
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'conexionexterna' AND column_name = 'keycloak_user_id'
  ) INTO has_kc;

  IF has_id THEN
    SELECT c.data_type INTO dt_id FROM information_schema.columns c
    WHERE c.table_schema = 'public' AND c.table_name = 'conexionexterna' AND c.column_name = 'id_usuario';
  ELSE
    dt_id := NULL;
  END IF;

  IF has_kc AND has_id AND dt_id = 'bigint' THEN
    ALTER TABLE conexionexterna DROP COLUMN id_usuario;
    ALTER TABLE conexionexterna RENAME COLUMN keycloak_user_id TO id_usuario;
  ELSIF has_id AND dt_id = 'bigint' THEN
    ALTER TABLE conexionexterna ADD COLUMN _mig_u VARCHAR(36);
    UPDATE conexionexterna SET _mig_u = '00000000-0000-0000-0000-000000000000';
    ALTER TABLE conexionexterna DROP COLUMN id_usuario;
    ALTER TABLE conexionexterna RENAME COLUMN _mig_u TO id_usuario;
    ALTER TABLE conexionexterna ALTER COLUMN id_usuario SET NOT NULL;
  ELSIF NOT has_id AND has_kc THEN
    ALTER TABLE conexionexterna RENAME COLUMN keycloak_user_id TO id_usuario;
  END IF;
END $$;

ALTER TABLE conexionexterna DROP COLUMN IF EXISTS keycloak_user_id;

DROP TABLE IF EXISTS usuario CASCADE;

DROP INDEX IF EXISTS idx_vivienda_keycloak_user;
DROP INDEX IF EXISTS idx_tarifausuario_keycloak;
DROP INDEX IF EXISTS idx_conexion_keycloak;
DROP INDEX IF EXISTS idx_vivienda_usuario;

CREATE INDEX IF NOT EXISTS idx_vivienda_id_usuario ON vivienda(id_usuario);
CREATE INDEX IF NOT EXISTS idx_tarifausuario_id_usuario ON tarifausuario(id_usuario);
CREATE INDEX IF NOT EXISTS idx_conexion_id_usuario ON conexionexterna(id_usuario);

COMMENT ON COLUMN vivienda.id_usuario IS 'UUID Keycloak (claim sub)';
COMMENT ON COLUMN tarifausuario.id_usuario IS 'UUID Keycloak (claim sub)';
COMMENT ON COLUMN conexionexterna.id_usuario IS 'UUID Keycloak (claim sub)';

CREATE OR REPLACE VIEW v_usuarios_tarifa_activa AS
SELECT
    v.id_usuario,
    v.id_vivienda,
    tu.id_tarifa_usuario,
    t.codigo_tarifa,
    t.nombre_tarifa,
    t.mercado,
    t.nivel_tension,
    t.tipo_tarifa,
    tu.fecha_asignacion
FROM vivienda v
INNER JOIN tarifausuario tu ON v.id_usuario = tu.id_usuario AND tu.activa = TRUE
INNER JOIN tarifa t ON tu.id_tarifa = t.id_tarifa;

COMMENT ON VIEW v_usuarios_tarifa_activa IS 'Viviendas con tarifa activa (mismo id_usuario Keycloak)';

CREATE OR REPLACE VIEW v_recomendaciones_pendientes AS
SELECT
    r.id_recomendacion,
    r.id_vivienda,
    e.nombre AS electrodomestico,
    r.fecha_propuesta,
    r.hora_inicio_sugerida,
    r.hora_fin_sugerida,
    r.ahorro_estimado_eur,
    r.impacto_confort,
    r.prioridad,
    v.direccion,
    v.id_usuario AS usuario_keycloak_id
FROM recomendacion r
INNER JOIN electrodomestico e ON r.id_electro = e.id_electro
INNER JOIN vivienda v ON r.id_vivienda = v.id_vivienda
WHERE r.estado = 'pendiente'
  AND r.fecha_propuesta >= CURRENT_DATE
ORDER BY r.prioridad ASC, r.ahorro_estimado_eur DESC;

COMMENT ON VIEW v_recomendaciones_pendientes IS 'Recomendaciones pendientes por vivienda';

COMMIT;
