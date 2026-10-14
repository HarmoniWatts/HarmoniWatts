-- =====================================================================
-- CARGA DE configuracion_aplicable (qué configuración horaria aplica a cada
-- mercado + nivel de tensión) para ENERTOTAL.   [v2]
--
-- Cambios respecto a la versión anterior:
--   * Niveles nuevos N1_2_1_3 ('N 1.2-1.3') y N1_2_1_3_50 ('N 1.2*-1.3* - 50%')
--     para TODOS los mercados.
--   * Mercado CENS (CH00) con N3, N2, N1_1, N1_2, N1_2_50, N1_2_1_3 y N1_2_1_3_50.
--   * Mercado ATENEA (CH00), en la sección 4: requiere que exista en mercado_red.
--
-- Regla para los niveles nuevos de cada mercado:
--   - mercado con una sola configuración  -> esa configuración
--   - mercado con varias (NARINO, ANTIOQUIA_UNIF, CAUCA, TOLIMA) -> la de su
--     familia N1 (N1_1 / N1_2 / N1_2_50): NARINO CH02, ANTIOQUIA_UNIF CH04,
--     CAUCA CH07, TOLIMA CH09.
-- =====================================================================

BEGIN;

-- 1. Niveles de tensión nuevos (catálogo)
INSERT INTO nivel_tension (cod_nivel, nombre, descripcion) VALUES
('N1_2_50',     'Nivel 1.2* - 50%',        'Conexión Nivel 1 con propiedad compartida de activos (50%)'),
('N1_2_1_3',    'Nivel 1.2-1.3',           'Conexión Nivel 1 con activos del cliente en Nivel 2 (1.2) o Nivel 3 (1.3)'),
('N1_2_1_3_50', 'Nivel 1.2*-1.3* - 50%',   'Conexión Nivel 1 con activos compartidos del cliente en Nivel 2 (1.2*) o Nivel 3 (1.3*) (50%)')
ON CONFLICT (cod_nivel) DO NOTHING;

-- 1. TRUNCATE a configuracion_aplicable
TRUNCATE TABLE configuracion_aplicable RESTART IDENTITY CASCADE;

COMMIT;

-- =====================================================
-- Reseteo explícito de la secuencia (por si acaso)
-- =====================================================
-- Aunque TRUNCATE ... RESTART IDENTITY ya resetea,
-- ejecutamos esto por seguridad.
ALTER SEQUENCE configuracion_aplicable_id_configuracion_aplicable_seq RESTART WITH 1;


-- 2. Asignación mercado + nivel -> configuración
DO $$
DECLARE
    v_desde CONSTANT DATE := DATE '2024-01-01';   -- <-- AJUSTAR: fecha desde la que rigen
    v_esperadas CONSTANT INT := 112;
    v_insertadas INT;
BEGIN
    INSERT INTO configuracion_aplicable
        (cod_comercializadora, cod_mercado, cod_nivel, id_configuracion_horaria, vigente_desde)
    SELECT 'ENERTOTAL', v.mercado, v.nivel, c.id_configuracion_horaria, v_desde
    FROM (VALUES
        ('CALI', 'N3', 'CH00'),
        ('CALI', 'N2', 'CH00'),
        ('CALI', 'N1_1', 'CH00'),
        ('CALI', 'N1_2', 'CH00'),
        ('CALI', 'N1_2_50', 'CH00'),
        ('CALI', 'N1_2_1_3', 'CH00'),
        ('CALI', 'N1_2_1_3_50', 'CH00'),
        ('VALLE', 'N4', 'CH00'),
        ('VALLE', 'N3', 'CH00'),
        ('VALLE', 'N2', 'CH00'),
        ('VALLE', 'N1_1', 'CH00'),
        ('VALLE', 'N1_2', 'CH00'),
        ('VALLE', 'N1_2_50', 'CH00'),
        ('VALLE', 'N1_2_1_3', 'CH00'),
        ('VALLE', 'N1_2_1_3_50', 'CH00'),
        ('NARINO', 'N2', 'CH01'),
        ('NARINO', 'N1_1', 'CH02'),
        ('NARINO', 'N1_2', 'CH02'),
        ('NARINO', 'N1_2_50', 'CH02'),
        ('NARINO', 'N1_2_1_3', 'CH02'),
        ('NARINO', 'N1_2_1_3_50', 'CH02'),
        ('ANTIOQUIA_UNIF', 'N3', 'CH03'),
        ('ANTIOQUIA_UNIF', 'N2', 'CH04'),
        ('ANTIOQUIA_UNIF', 'N1_1', 'CH04'),
        ('ANTIOQUIA_UNIF', 'N1_2', 'CH04'),
        ('ANTIOQUIA_UNIF', 'N1_2_50', 'CH04'),
        ('ANTIOQUIA_UNIF', 'N1_2_1_3', 'CH04'),
        ('ANTIOQUIA_UNIF', 'N1_2_1_3_50', 'CH04'),
        ('BOGOTA', 'N3', 'CH00'),
        ('BOGOTA', 'N2', 'CH00'),
        ('BOGOTA', 'N1_1', 'CH00'),
        ('BOGOTA', 'N1_2', 'CH00'),
        ('BOGOTA', 'N1_2_50', 'CH00'),
        ('BOGOTA', 'N1_2_1_3', 'CH00'),
        ('BOGOTA', 'N1_2_1_3_50', 'CH00'),
        ('CAUCA', 'N3', 'CH05'),
        ('CAUCA', 'N2', 'CH06'),
        ('CAUCA', 'N1_1', 'CH07'),
        ('CAUCA', 'N1_2', 'CH07'),
        ('CAUCA', 'N1_2_1_3', 'CH07'),
        ('CAUCA', 'N1_2_1_3_50', 'CH07'),
        ('BOYACA', 'N3', 'CH00'),
        ('BOYACA', 'N2', 'CH00'),
        ('BOYACA', 'N1_1', 'CH00'),
        ('BOYACA', 'N1_2', 'CH00'),
        ('BOYACA', 'N1_2_1_3', 'CH00'),
        ('BOYACA', 'N1_2_1_3_50', 'CH00'),
        ('CARIBE_MAR', 'N2', 'CH00'),
        ('CARIBE_MAR', 'N1_1', 'CH00'),
        ('CARIBE_MAR', 'N1_2', 'CH00'),
        ('CARIBE_MAR', 'N1_2_1_3', 'CH00'),
        ('CARIBE_MAR', 'N1_2_1_3_50', 'CH00'),
        ('CARIBE_SOL', 'N2', 'CH00'),
        ('CARIBE_SOL', 'N1_1', 'CH00'),
        ('CARIBE_SOL', 'N1_2', 'CH00'),
        ('CARIBE_SOL', 'N1_2_1_3', 'CH00'),
        ('CARIBE_SOL', 'N1_2_1_3_50', 'CH00'),
        ('CALDAS', 'N1_2_50', 'CH08'),
        ('CALDAS', 'N1_2_1_3', 'CH08'),
        ('CALDAS', 'N1_2_1_3_50', 'CH08'),
        ('CARTAGO', 'N2', 'CH00'),
        ('CARTAGO', 'N1_1', 'CH00'),
        ('CARTAGO', 'N1_2', 'CH00'),
        ('CARTAGO', 'N1_2_1_3', 'CH00'),
        ('CARTAGO', 'N1_2_1_3_50', 'CH00'),
        ('TOLIMA', 'N2', 'CH00'),
        ('TOLIMA', 'N1_1', 'CH09'),
        ('TOLIMA', 'N1_2', 'CH09'),
        ('TOLIMA', 'N1_2_1_3', 'CH09'),
        ('TOLIMA', 'N1_2_1_3_50', 'CH09'),
        ('PEREIRA', 'N2', 'CH00'),
        ('PEREIRA', 'N1_1', 'CH00'),
        ('PEREIRA', 'N1_2', 'CH00'),
        ('PEREIRA', 'N1_2_1_3', 'CH00'),
        ('PEREIRA', 'N1_2_1_3_50', 'CH00'),
        ('QUINDIO', 'N3', 'CH00'),
        ('QUINDIO', 'N2', 'CH00'),
        ('QUINDIO', 'N1_1', 'CH00'),
        ('QUINDIO', 'N1_2', 'CH00'),
        ('QUINDIO', 'N1_2_1_3', 'CH00'),
        ('QUINDIO', 'N1_2_1_3_50', 'CH00'),
        ('CETSA', 'N3', 'CH00'),
        ('CETSA', 'N2', 'CH00'),
        ('CETSA', 'N1_1', 'CH00'),
        ('CETSA', 'N1_2', 'CH00'),
        ('CETSA', 'N1_2_1_3', 'CH00'),
        ('CETSA', 'N1_2_1_3_50', 'CH00'),
        ('SANTANDER', 'N3', 'CH00'),
        ('SANTANDER', 'N2', 'CH00'),
        ('SANTANDER', 'N1_1', 'CH00'),
        ('SANTANDER', 'N1_2', 'CH00'),
        ('SANTANDER', 'N1_2_1_3', 'CH00'),
        ('SANTANDER', 'N1_2_1_3_50', 'CH00'),
        ('HUILA', 'N3', 'CH00'),
        ('HUILA', 'N2', 'CH00'),
        ('HUILA', 'N1_1', 'CH00'),
        ('HUILA', 'N1_2', 'CH00'),
        ('HUILA', 'N1_2_1_3', 'CH00'),
        ('HUILA', 'N1_2_1_3_50', 'CH00'),
        ('META', 'N3', 'CH00'),
        ('META', 'N2', 'CH00'),
        ('META', 'N1_1', 'CH00'),
        ('META', 'N1_2', 'CH00'),
        ('META', 'N1_2_1_3', 'CH00'),
        ('META', 'N1_2_1_3_50', 'CH00'),
        ('CENS', 'N3', 'CH00'),
        ('CENS', 'N2', 'CH00'),
        ('CENS', 'N1_1', 'CH00'),
        ('CENS', 'N1_2', 'CH00'),
        ('CENS', 'N1_2_50', 'CH00'),
        ('CENS', 'N1_2_1_3', 'CH00'),
        ('CENS', 'N1_2_1_3_50', 'CH00')
    ) AS v(mercado, nivel, cfg)
    JOIN configuracion_horaria c
      ON c.cod_comercializadora = 'ENERTOTAL' AND c.codigo = v.cfg;

    GET DIAGNOSTICS v_insertadas = ROW_COUNT;
    IF v_insertadas <> v_esperadas THEN
        RAISE EXCEPTION 'Se esperaban % filas y se insertaron %', v_esperadas, v_insertadas;
    END IF;
END $$;

-- 3. Verificación: combinaciones y mercados por configuración
SELECT c.codigo, count(*) AS combinaciones, count(DISTINCT a.cod_mercado) AS mercados
FROM configuracion_aplicable a
JOIN configuracion_horaria c USING (id_configuracion_horaria)
GROUP BY c.codigo ORDER BY c.codigo;

COMMIT;

-- =====================================================================
-- 4. ATENEA (transacción aparte: si el mercado aún no existe, solo falla esta sección)
--
-- ATENEA no está en mercado_red. Primero créalo con su operador de red real
-- (plantilla; reemplaza lo que está entre <>):
INSERT INTO operador_red (cod_or, nombre_operador, descripcion)
VALUES ('OR_ATENEA', 'Atenea', 'Operador de red de los departamentos de Cesar, Magdalena y Bolívar');
INSERT INTO mercado_red (cod_mercado, nombre_mercado, cod_or, descripcion, activo)
VALUES ('ATENEA', 'Mercado ATENEA', 'OR_ATENEA', 'Mercado-Red ATENEA', TRUE);
-- (si el operador ya existe, omite el primer INSERT y usa su cod_or)
-- =====================================================================
BEGIN;

DO $$
DECLARE
    v_desde CONSTANT DATE := DATE '2024-01-01';   -- <-- usar la misma fecha de la sección 2
    v_esperadas CONSTANT INT := 7;
    v_insertadas INT;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM mercado_red WHERE cod_mercado = 'ATENEA') THEN
        RAISE EXCEPTION 'ATENEA no existe en mercado_red: créelo (con su operador de red) y vuelva a ejecutar esta sección';
    END IF;

    INSERT INTO configuracion_aplicable
        (cod_comercializadora, cod_mercado, cod_nivel, id_configuracion_horaria, vigente_desde)
    SELECT 'ENERTOTAL', v.mercado, v.nivel, c.id_configuracion_horaria, v_desde
    FROM (VALUES
        ('ATENEA', 'N3', 'CH00'),
        ('ATENEA', 'N2', 'CH00'),
        ('ATENEA', 'N1_1', 'CH00'),
        ('ATENEA', 'N1_2', 'CH00'),
        ('ATENEA', 'N1_2_50', 'CH00'),
        ('ATENEA', 'N1_2_1_3', 'CH00'),
        ('ATENEA', 'N1_2_1_3_50', 'CH00')
    ) AS v(mercado, nivel, cfg)
    JOIN configuracion_horaria c
      ON c.cod_comercializadora = 'ENERTOTAL' AND c.codigo = v.cfg;

    GET DIAGNOSTICS v_insertadas = ROW_COUNT;
    IF v_insertadas <> v_esperadas THEN
        RAISE EXCEPTION 'Se esperaban % filas y se insertaron %', v_esperadas, v_insertadas;
    END IF;
END $$;

COMMIT;

--Adcional se quita una una restriccion en clientes

ALTER TABLE cliente DROP CONSTRAINT ck_cliente_estrato_residencial;


-- Prueba de la función:
-- SELECT fn_configuracion_aplicable('ENERTOTAL', 'CALI', 'N2', DATE '2025-03-01');   -- debe dar el id de CH00
-- SELECT fn_configuracion_aplicable('ENERTOTAL', 'TOLIMA', 'N1_2_1_3', DATE '2025-03-01');   -- debe dar el id de CH09
