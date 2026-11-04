-- =====================================================================
-- DATOS DE PRUEBA: tabla cliente (9 registros)
-- Requiere: tablas del modelo TAP creadas, con sus catálogos poblados
-- (comercializadora ENERTOTAL, zona_geografica, mercado_zona, tipo_cliente,
-- nivel_tension incluido N1_2_1_3 del script carga_configuracion_aplicable_v2).
--
-- Notas sobre el mapeo de tu tabla:
--   * id_zona se resuelve por municipio (no se fija a mano).
--   * cod_mercado debe ser un mercado que atienda esa zona (FK compuesta con mercado_zona).
--   * Niveles: 'Nivel 1.1' -> N1_1 ; 'N 1.2-1.3' -> N1_2_1_3.
--   * ESTRATO: la restricción ck_cliente_estrato_residencial exige estrato NULL
--     para clientes que no son 'R'. Por eso en los tipos C y E va NULL
--     (el estrato original de tu tabla queda como comentario en cada fila).
--   * 'Nodo' (I..IX) no tiene columna en cliente; queda solo como comentario.
--   * email: <nombre>@example.com (dominio reservado para pruebas).
--   * password_hash: valor ficticio NO válido (estos clientes no pueden iniciar sesión).
--   * cs_kwh_mes no se inserta: lo calcula el trigger trg_cliente_cs por la altura de la zona.
-- =====================================================================

BEGIN;


-- 1. TRUNCATE a cliente
TRUNCATE TABLE cliente RESTART IDENTITY CASCADE;

COMMIT;

-- =====================================================
-- Reseteo explícito de la secuencia (por si acaso)
-- =====================================================
-- Aunque TRUNCATE ... RESTART IDENTITY ya resetea,
-- ejecutamos esto por seguridad.
ALTER SEQUENCE cliente_id_cliente_seq RESTART WITH 1;

DO $$
DECLARE
    v_esperadas CONSTANT INT := 9;
    v_insertadas INT;
BEGIN
    INSERT INTO cliente
        (nombre, email, password_hash, cod_tipo_cliente, estrato, cod_nivel,
         id_zona, cod_mercado, cod_comercializadora)
    SELECT v.nombre,
           lower(v.nombre) || '@example.com',
           'HASH_DE_PRUEBA_NO_VALIDO',
           v.tipo, v.estrato, v.nivel,
           z.id_zona, v.mercado, 'ENERTOTAL'
    FROM (VALUES
        --  nombre          tipo  estrato  nivel        mercado       municipio
        ('MN1860D3B3B7',   'R',  5,       'N1_1',      'BOGOTA',      'Girardot'),          -- Nodo III   · Residencial
        ('MN9E60ABC91C',   'R',  3,       'N1_1',      'CALI',       'Santiago de Cali'), -- Nodo II  · Residencial
        ('MNC391C85C85',   'E',  5,       'N1_1',      'BOGOTA',     'Girardot'),         -- Nodo III · Especial    (estrato original: 5)
        ('MNE5D6840091',   'C',  2,       'N1_2_1_3',  'CARIBE_MAR', 'Cereté'),           -- Nodo IV  · Comercial   (estrato original: 2)
        ('MN809B65A6F1',   'R',  3,       'N1_1',      'CARIBE_MAR', 'Montería'),         -- Nodo V   · Residencial
        ('MND9A83DC2D2',   'R',  3,       'N1_1',      'CARIBE_MAR', 'Montería'),         -- Nodo VI  · Residencial
        ('MN157A243DFE',   'R',  3,       'N1_1',      'CARIBE_MAR', 'Caucasia'),         -- Nodo VII · Residencial
        ('MN233D2ED722',   'C',  4,       'N1_1',      'CALI',       'Santiago de Cali'), -- Nodo VIII· Comercial   (estrato original: 4)
        ('MNDD305C0D60',   'E',  4,       'N1_1',      'CALI',       'Santiago de Cali')  -- Nodo IX  · Especial    (estrato original: 4)
    ) AS v(nombre, tipo, estrato, nivel, mercado, municipio)
    JOIN zona_geografica z ON z.municipio = v.municipio;

    GET DIAGNOSTICS v_insertadas = ROW_COUNT;
    IF v_insertadas <> v_esperadas THEN
        RAISE EXCEPTION 'Se esperaban % clientes y se insertaron %', v_esperadas, v_insertadas;
    END IF;
END $$;

-- Verificación (incluye el CS calculado por el trigger)
SELECT c.id_cliente, c.nombre, c.cod_tipo_cliente AS tipo, c.estrato, c.cod_nivel,
       z.municipio, z.altura, c.cod_mercado, c.cs_kwh_mes
FROM cliente c
JOIN zona_geografica z USING (id_zona)
ORDER BY c.id_cliente;

COMMIT;

-- Limpieza de los datos de prueba:
--   DELETE FROM cliente WHERE email LIKE '%@example.com';
