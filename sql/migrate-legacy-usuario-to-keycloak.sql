-- =====================================================
-- Migración: esquema con tabla usuario → Keycloak (sub)
-- Ejecutar sobre una BD existente creada con init-harmoniwatts.sql antiguo.
-- Hacer copia de seguridad antes.
-- En PostgreSQL los identificadores sin comillas quedan en minúsculas.
-- =====================================================

BEGIN;

DROP VIEW IF EXISTS v_recomendaciones_pendientes;
DROP VIEW IF EXISTS v_usuarios_tarifa_activa;

ALTER TABLE tarifausuario DROP CONSTRAINT IF EXISTS fk_tarifausuario_usuario;
ALTER TABLE conexionexterna DROP CONSTRAINT IF EXISTS fk_conexion_usuario;
ALTER TABLE vivienda DROP CONSTRAINT IF EXISTS fk_vivienda_usuario;

ALTER TABLE tarifausuario RENAME COLUMN id_usuario TO id_usuario_legacy;
ALTER TABLE tarifausuario ADD COLUMN keycloak_user_id VARCHAR(36);
UPDATE tarifausuario SET keycloak_user_id = '00000000-0000-0000-0000-000000000000' WHERE keycloak_user_id IS NULL;
ALTER TABLE tarifausuario ALTER COLUMN keycloak_user_id SET NOT NULL;
ALTER TABLE tarifausuario DROP COLUMN id_usuario_legacy;

ALTER TABLE conexionexterna RENAME COLUMN id_usuario TO id_usuario_legacy;
ALTER TABLE conexionexterna ADD COLUMN keycloak_user_id VARCHAR(36);
UPDATE conexionexterna SET keycloak_user_id = '00000000-0000-0000-0000-000000000000' WHERE keycloak_user_id IS NULL;
ALTER TABLE conexionexterna ALTER COLUMN keycloak_user_id SET NOT NULL;
ALTER TABLE conexionexterna DROP COLUMN id_usuario_legacy;

ALTER TABLE vivienda DROP COLUMN IF EXISTS superficie;
ALTER TABLE vivienda RENAME COLUMN id_usuario TO id_usuario_legacy;
ALTER TABLE vivienda ADD COLUMN keycloak_user_id VARCHAR(36);
UPDATE vivienda SET keycloak_user_id = '00000000-0000-0000-0000-000000000000' WHERE keycloak_user_id IS NULL;
ALTER TABLE vivienda ALTER COLUMN keycloak_user_id SET NOT NULL;
ALTER TABLE vivienda DROP COLUMN id_usuario_legacy;

DROP INDEX IF EXISTS idx_vivienda_usuario;
DROP INDEX IF EXISTS idx_tarifausuario_usuario;
DROP INDEX IF EXISTS idx_conexion_usuario;

CREATE INDEX idx_vivienda_keycloak_user ON vivienda(keycloak_user_id);
CREATE INDEX idx_tarifausuario_keycloak ON tarifausuario(keycloak_user_id);
CREATE INDEX idx_conexion_keycloak ON conexionexterna(keycloak_user_id);

DROP TABLE IF EXISTS usuario CASCADE;

DROP FUNCTION IF EXISTS actualizar_ultimo_acceso();

CREATE OR REPLACE VIEW v_usuarios_tarifa_activa AS
SELECT 
    v.keycloak_user_id,
    v.id_vivienda,
    tu.id_tarifa_usuario,
    t.codigo_tarifa,
    t.nombre_tarifa,
    t.mercado,
    t.nivel_tension,
    t.tipo_tarifa,
    tu.fecha_asignacion
FROM vivienda v
INNER JOIN tarifausuario tu ON v.keycloak_user_id = tu.keycloak_user_id AND tu.activa = TRUE
INNER JOIN tarifa t ON tu.id_tarifa = t.id_tarifa;

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
    v.keycloak_user_id AS usuario_keycloak_id
FROM recomendacion r
INNER JOIN electrodomestico e ON r.id_electro = e.id_electro
INNER JOIN vivienda v ON r.id_vivienda = v.id_vivienda
WHERE r.estado = 'pendiente'
  AND r.fecha_propuesta >= CURRENT_DATE
ORDER BY r.prioridad ASC, r.ahorro_estimado_eur DESC;

COMMIT;
