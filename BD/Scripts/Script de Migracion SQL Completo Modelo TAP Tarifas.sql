-- =====================================================
-- MIGRACIÓN: Modelo Colombia → Modelo TAP (Español)
-- =====================================================



-- =====================================================
-- ELIMINACIÓN SEGURA - Versión corregida
-- =====================================================

DO $$
DECLARE
    tabla TEXT;
    tabla_min TEXT;
    tablas_a_eliminar TEXT[] := ARRAY[
        -- Orden: de hijas a padres
        'franjatarifa',
        'componentetarifa',
        'franja_horaria',
        'bloque_tarifa',
        'grupo_tarifa',
        'tarifa',
        'mercado_zona',
        'tarifausuario',
        'mercado_red',
        'operadorred',
        'tipo_usuario',
        'tipo_bloque',
        'zona_geografica',
        'comercializadora',
		'usuario'
    ];
BEGIN
    FOREACH tabla IN ARRAY tablas_a_eliminar
    LOOP
        -- Convertir a minúsculas para comparar con information_schema
        tabla_min := LOWER(tabla);
        
        IF EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public'
              AND LOWER(table_name) = tabla_min
        ) THEN
            EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', tabla_min);
            RAISE NOTICE '✓ Tabla eliminada: %', tabla_min;
        ELSE
            RAISE NOTICE '✗ Tabla no existe (omitida): %', tabla_min;
        END IF;
    END LOOP;
    
    RAISE NOTICE '--- Proceso de eliminación completado ---';
END $$;


-- Verificar que todas las tablas fueron eliminadas
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
  AND table_name IN (
    'franjatarifa', 'componentetarifa', 'franja_horaria', 'bloque_tarifa',
    'grupo_tarifa', 'tarifa', 'mercado_zona', 'tarifausuario',
    'mercado_red', 'operadorred', 'tipo_usuario', 'tipo_bloque',
    'zona_geografica', 'comercializadora'
  );
-- Resultado esperado: 0 filas
 
 


--------------------------------------------------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------------------------------------------

-- =====================================================
-- 1. TABLA: Comercializadora
-- =====================================================
CREATE TABLE comercializadora (
    cod_comercializadora VARCHAR(20) PRIMARY KEY, -- Código mnemotécnico/sigla XM
    nombre VARCHAR(100) NOT NULL UNIQUE,
    nit VARCHAR(20) UNIQUE,
    sitio_web VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE comercializadora IS 'Empresa que provee el servicio eléctrico';

-- Insertar comercializadora
INSERT INTO comercializadora (cod_comercializadora, nombre, nit, sitio_web, activo)
VALUES ('ENERTOTAL', 'ENERTOTAL S.A. E.S.P.', '900.039.901-5', 'https://www.enertotalesp.com/', TRUE);


-- 2. Crear tabla de ZONA_GEOGRAFICA (Nivel 1 - Utility complementario)
-- =====================================================
-- Catálogo geográfico
CREATE TABLE Zona_Geografica (
    id_zona SMALLSERIAL PRIMARY KEY,
    nombre_zona VARCHAR(50) NOT NULL,  -- puede ser el nombre del municipo, departamento o departamento
    municipio VARCHAR(50),             -- Opcional nuevo campo: nombre del municipio
    departamento VARCHAR(50),          -- Opcional nuevo campo: nombre del departamento
    region VARCHAR(50),                -- Opcional nuevo campo: nombre de la region
	altura INTEGER                     ---Altura de la zona/municipio
);

INSERT INTO Zona_Geografica (nombre_zona, municipio, departamento, region, altura) VALUES
('Popayán', 'Popayán', 'Cauca', 'Andina', 1760),
('Cali', 'Santiago de Cali', 'Valle del Cauca', 'Andina', 1018),
('Girardot', 'Girardot', 'Cundinamarca', 'Andina', 326),
('Cereté', 'Cereté', 'Córdoba', 'Caribe', 12),
('Montería', 'Montería', 'Córdoba', 'Caribe', 15),
('Caucasia', 'Caucasia', 'Antioquia', 'Andina', 150);


-- =====================================================
-- 3. TABLA: Operador de Red (Propietario de la Red)
-- =====================================================
CREATE TABLE operador_red (
    cod_or VARCHAR(20) PRIMARY KEY, -- Código mnemotécnico oficial
    nombre_operador VARCHAR(100) NOT NULL UNIQUE,
    nit VARCHAR(20),
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE operador_red IS 'Empresa propietaria o administradora del Sistema de Distribución Local (SDL)';

-- Poblar catálogo de operadores principales
INSERT INTO operador_red (cod_or, nombre_operador, descripcion) VALUES
('OR_EMCALI',     'EMCALI',             'Empresa Municipal de Cali'),
('OR_CELSIA',     'CELSIA',             'Operador de red en Valle y Tolima'),
('OR_EPM',        'EPM',                'Empresas Públicas de Medellín'),
('OR_AFINIA',     'Afinia',             'Operador de red Caribe Mar'),
('OR_AIR_E',      'Air-e',              'Operador de red Caribe Sol'),
('OR_ENEL',       'Enel',               'Operador de red Bogotá'),
('OR_CEDENAR',    'CEDENAR',            'Operador de red Nariño'),
('OR_EBSA',       'EBSA',               'Operador de red Boyacá'),
('OR_CHEC',       'CHEC',               'Operador de red Caldas'),
('OR_EEP',        'ENERGÍA DE PEREIRA', 'Operador de red Pereira y Cartago'),
('OR_EDEQ',       'EDEQ',               'Operador de red Quindío'),
('OR_CETSA',      'CETSA',              'Operador de red Compañía de Electricidad Tuluá'),
('OR_ESSA',       'ESSA',               'Operador de red Santander'),
('OR_ELECTROHUILA','Electrohuila',      'Operador de red Huila'),
('OR_EMSA',       'EMSA',               'Operador de red Meta'),
('OR_CENS',       'CENS',               'Operador de red Norte de Santander'),
('OR_CEO',        'CEO',                'Operador de red en Cauca');

-- =====================================================
--4. TABLA: Mercado-Red (definido por OR)
-- =====================================================
CREATE TABLE mercado_red (
    cod_mercado VARCHAR(30) PRIMARY KEY,                -- Nombre/código estándar del mercado (Ej: 'CALI', 'BOGOTA')
    nombre_mercado VARCHAR(100) NOT NULL,
    cod_or VARCHAR(20) NOT NULL REFERENCES operador_red(cod_or), -- FK a operador_red
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE mercado_red IS 'Mercados de comercialización delimitados por la infraestructura del Operador de Red';

-- Poblar catálogo de Mercado_Red
INSERT INTO mercado_red (cod_mercado, nombre_mercado, cod_or, descripcion, activo) VALUES
('CALI',           'Mercado EMCALI Cali',               'OR_EMCALI',      'Mercado-Red EMCALI Cali', TRUE),
('CAUCA',          'Mercado CEO Cauca',                 'OR_CEO',         'Mercado-Red CEO Cauca', TRUE),
('CARIBE_MAR',     'Mercado Caribe Mar (Afinia)',       'OR_AFINIA',      'Mercado-Red Caribe Mar (Afinia)', TRUE),
('BOGOTA',         'Mercado Enel Bogotá',               'OR_ENEL',        'Mercado-Red Enel Bogotá', TRUE),
('VALLE',          'Mercado CELSIA Valle del Cauca',    'OR_CELSIA',      'Mercado-Red CELSIA Valle del Cauca', TRUE),
('NARINO',         'Mercado CEDENAR Nariño',            'OR_CEDENAR',     'Mercado-Red CEDENAR Nariño', TRUE),
('ANTIOQUIA_UNIF', 'Mercado EPM Antioquia Unificado',   'OR_EPM',         'Mercado-Red EPM Antioquia Unificado', TRUE),
('BOYACA',         'Mercado EBSA Boyacá',               'OR_EBSA',        'Mercado-Red EBSA Boyacá', TRUE),
('CARIBE_SOL',     'Mercado Caribe Sol (Air-e)',        'OR_AIR_E',       'Mercado-Red Caribe Sol (Air-e)', TRUE),
('CALDAS',         'Mercado CHEC Caldas',               'OR_CHEC',        'Mercado-Red CHEC Caldas', TRUE),
('CARTAGO',        'Mercado EEP Cartago',               'OR_EEP',         'Mercado-Red EEP Cartago', TRUE),
('TOLIMA',         'Mercado CELSIA Tolima',             'OR_CELSIA',      'Mercado-Red CELSIA Tolima', TRUE),
('PEREIRA',        'Mercado ENERGÍA DE PEREIRA',        'OR_EEP',         'Mercado-Red ENERGÍA DE PEREIRA', TRUE),
('QUINDIO',        'Mercado EDEQ Quindío',              'OR_EDEQ',        'Mercado-Red EDEQ Quindío', TRUE),
('CETSA',          'Mercado CETSA Tuluá',               'OR_CETSA',       'Mercado-Red CETSA Tuluá', TRUE),
('SANTANDER',      'Mercado ESSA Santander',            'OR_ESSA',        'Mercado-Red ESSA Santander', TRUE),
('HUILA',          'Mercado Electrohuila',              'OR_ELECTROHUILA','Mercado-Red Electrohuila', TRUE),
('META',           'Mercado EMSA Meta',                 'OR_EMSA',        'Mercado-Red EMSA Meta', TRUE),
('CENS',           'Mercado CENS Norte de Santander',   'OR_CENS',        'Mercado-Red CENS Norte de Santander', TRUE);




-- =====================================================
--5. TABLA: Mercado Zona
-- =====================================================
-- Relación entre municipios (zonas) y mercados-red
CREATE TABLE Mercado_Zona (
    id_mercado_zona BIGSERIAL PRIMARY KEY,
    cod_mercado VARCHAR(30) NOT NULL REFERENCES Mercado_Red(cod_mercado),
    id_zona SMALLINT NOT NULL REFERENCES Zona_Geografica(id_zona),
    UNIQUE(cod_mercado, id_zona)
);


-- Inserción masiva de relaciones únicas Mercado - Zona
INSERT INTO Mercado_Zona (cod_mercado, id_zona) VALUES

-- Popayán -> Mercado CAUCA
(
    (SELECT cod_mercado FROM Mercado_Red WHERE cod_mercado = 'CAUCA' LIMIT 1),
    (SELECT id_zona FROM Zona_Geografica WHERE municipio = 'Popayán' LIMIT 1)
),

-- Cali -> Mercado CALI
(
    (SELECT cod_mercado FROM Mercado_Red WHERE cod_mercado = 'CALI' LIMIT 1),
    (SELECT id_zona FROM Zona_Geografica WHERE municipio = 'Santiago de Cali' LIMIT 1)
),

-- Girardot -> Mercado BOGOTA
(
    (SELECT cod_mercado FROM Mercado_Red WHERE cod_mercado = 'BOGOTA' LIMIT 1),
    (SELECT id_zona FROM Zona_Geografica WHERE municipio = 'Girardot' LIMIT 1)
),

-- Cereté -> Mercado CARIBE_MAR
(
    (SELECT cod_mercado FROM Mercado_Red WHERE cod_mercado = 'CARIBE_MAR' LIMIT 1),
    (SELECT id_zona FROM Zona_Geografica WHERE municipio = 'Cereté' LIMIT 1)
),

-- Montería -> Mercado CARIBE_MAR
(
    (SELECT cod_mercado FROM Mercado_Red WHERE cod_mercado = 'CARIBE_MAR' LIMIT 1),
    (SELECT id_zona FROM Zona_Geografica WHERE municipio = 'Montería' LIMIT 1)
),

-- Caucasia -> Mercado CARIBE_MAR
(
    (SELECT cod_mercado FROM Mercado_Red WHERE cod_mercado = 'CARIBE_MAR' LIMIT 1),
    (SELECT id_zona FROM Zona_Geografica WHERE municipio = 'Caucasia' LIMIT 1)
);



-- =====================================================
--6. TABLA: Tipo de Clientes--Catálogo de tipos de clientes(Sectores de Consumo)
-- =====================================================
CREATE TABLE tipo_cliente (
    cod_tipo_cliente CHAR(1) PRIMARY KEY, -- 'I', 'C', 'O', 'E', 'R'
    nombre VARCHAR(50) NOT NULL,
    descripcion VARCHAR(150) NOT NULL
);

COMMENT ON TABLE tipo_cliente IS 'Clasificación del uso del servicio (Industrial, Comercial, Oficial, Especial, Residencial)';

-- Poblar catálogo de Tipo de Cliente
INSERT INTO tipo_cliente (cod_tipo_cliente, nombre, descripcion) VALUES
('I', 'Industrial',  'Uso industrial para procesos de manufactura o transformación'),
('C', 'Comercial',   'Uso comercial para prestación de servicios o venta de bienes'),
('O', 'Oficial',     'Entidades gubernamentales e instituciones públicas'),
('E', 'Especial',    'Instalaciones de asistencia social, centros de salud, educación, etc.'),
('R', 'Residencial', 'Uso doméstico en viviendas y residencias');


-- ============================================================
-- 7. TABLA: NIVEL DE TENSIÓN
-- Ejemplo:
--   Nivel 1.1
--   Nivel 1.2
--   Nivel 1.3
--   Nivel 2
--   Nivel 3
-- ============================================================

CREATE TABLE nivel_tension (
    cod_nivel VARCHAR(15) PRIMARY KEY, -- 'N1_1', 'N1_2', 'N2', 'N3', 'N4'
    nombre VARCHAR(50) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE nivel_tension IS 'Niveles de tensión del sistema de distribución (CREG)';

-- Poblar catálogo de Niveles de Tensión
INSERT INTO nivel_tension (cod_nivel, nombre, descripcion) VALUES
('N1_1', 'Nivel 1.1', 'Conexión Nivel 1 con propiedad de activos del OR o de un tercero'),
('N1_2', 'Nivel 1.2', 'Conexión Nivel 1 con propiedad de activos del cliente'),
('N1_2_50', 'Nivel 1.2* - 50%', 'Conexión Nivel 1 con propiedad compartida de activos (50%)'),
('N2',   'Nivel 2',   'Tensión nominal mayor o igual a 1 kV y menor a 30 kV'),
('N3',   'Nivel 3',   'Tensión nominal mayor o igual a 30 kV y menor a 62 kV'),
('N4',   'Nivel 4',   'Tensión nominal mayor o igual a 62 kV');



-- =====================================================================
-- 8. TABLA: CLIENTE (antes Usuario)
--
-- Ubicar DESPUÉS de: comercializadora, zona_geografica, mercado_red,
-- mercado_zona, tipo_cliente y nivel_tension.
-- Agregar 'cliente' a la lista de tablas del bloque de eliminación.
-- =====================================================================

CREATE TABLE cliente (
    id_cliente           BIGSERIAL PRIMARY KEY,

    -- Cuenta de acceso
    nombre               VARCHAR(100) NOT NULL,
    email                VARCHAR(100) NOT NULL UNIQUE,
    password_hash        VARCHAR(255) NOT NULL,
    telefono             VARCHAR(20),

    -- Clasificación del servicio
    cod_tipo_cliente     CHAR(1)      NOT NULL REFERENCES tipo_cliente(cod_tipo_cliente),
    estrato              SMALLINT,
    cod_nivel            VARCHAR(15)  NOT NULL REFERENCES nivel_tension(cod_nivel),

    -- Ubicación y proveedor
    id_zona              SMALLINT     NOT NULL,
    cod_mercado          VARCHAR(30)  NOT NULL,
    cod_comercializadora VARCHAR(20)  NOT NULL REFERENCES comercializadora(cod_comercializadora),

    -- Consumo de subsistencia (kWh/mes): lo calcula el trigger según la altura de la zona
    cs_kwh_mes           NUMERIC(8,2),

    fecha_registro       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    ultimo_acceso        TIMESTAMPTZ,
    activo               BOOLEAN      NOT NULL DEFAULT TRUE,

    -- Zona y mercado en una sola FK: el mercado debe ser uno de los que atienden la zona
    CONSTRAINT fk_cliente_mercado_zona
        FOREIGN KEY (cod_mercado, id_zona)
        REFERENCES mercado_zona (cod_mercado, id_zona),

    CONSTRAINT ck_cliente_estrato
        CHECK (estrato BETWEEN 1 AND 6),

    -- El estrato aplica solo a clientes residenciales ('R') y es obligatorio para ellos
    CONSTRAINT ck_cliente_estrato_residencial
        CHECK ((cod_tipo_cliente = 'R') = (estrato IS NOT NULL))
);

CREATE INDEX idx_cliente_mercado_zona ON cliente (cod_mercado, id_zona);
CREATE INDEX idx_cliente_tarifa       ON cliente (cod_comercializadora, cod_mercado, cod_nivel);

COMMENT ON TABLE  cliente IS 'Cliente (suscriptor): clasificación, ubicación y comercializadora';
COMMENT ON COLUMN cliente.estrato IS 'Estrato 1 a 6; solo para clientes residenciales (tipo R)';
COMMENT ON COLUMN cliente.cod_nivel IS 'Nivel de tensión de conexión; junto con el mercado define la tarifa y la configuración horaria';
COMMENT ON COLUMN cliente.cs_kwh_mes IS 'Consumo de subsistencia: 173 kWh/mes (< 1000 m.s.n.m.) o 130 kWh/mes (>= 1000 m.s.n.m.)';

-- ---------------------------------------------------------------------
-- Consumo de subsistencia según la altura del municipio
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_cs_kwh_mes(p_altura INTEGER)
RETURNS NUMERIC LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE
             WHEN p_altura IS NULL THEN NULL::NUMERIC
             WHEN p_altura < 1000  THEN 173::NUMERIC
             ELSE 130::NUMERIC
           END
$$;

-- Llena cs_kwh_mes al insertar el cliente o al cambiar su zona.
-- Queda NULL si la zona no tiene altura registrada.
CREATE OR REPLACE FUNCTION trg_cliente_cs() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    SELECT fn_cs_kwh_mes(z.altura)
      INTO NEW.cs_kwh_mes
      FROM zona_geografica z
     WHERE z.id_zona = NEW.id_zona;
    RETURN NEW;
END $$;

CREATE TRIGGER trg_cliente_cs
    BEFORE INSERT OR UPDATE OF id_zona ON cliente
    FOR EACH ROW EXECUTE FUNCTION trg_cliente_cs();

-- Si se corrige la altura de una zona, recalcular el CS de sus clientes:
--   UPDATE cliente SET id_zona = id_zona WHERE id_zona = <id>;

-- ---------------------------------------------------------------------
-- Vista de consulta: incluye zona, operador de red y CS (sin password_hash)
-- El operador de red no se guarda en cliente: se deriva de mercado_red.cod_or
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_cliente AS
SELECT c.id_cliente, c.nombre, c.email, c.telefono,
       c.cod_tipo_cliente, c.estrato, c.cod_nivel,
       c.id_zona, z.nombre_zona, z.municipio, z.departamento, z.altura,
       c.cod_mercado, m.nombre_mercado,
       m.cod_or, o.nombre_operador,
       c.cod_comercializadora,
       c.cs_kwh_mes,
       c.activo
FROM cliente c
JOIN zona_geografica z ON z.id_zona     = c.id_zona
JOIN mercado_red     m ON m.cod_mercado = c.cod_mercado
JOIN operador_red    o ON o.cod_or      = m.cod_or;

-- ============================================================
-- 9. TABLA: TIPO DE TARIFA DEL COMERCIALIZADOR
--
-- IMPORTANTE:
-- A, B, C, D NO se consideran códigos regulatorios universales.
-- Cada comercializador puede definir su propia nomenclatura.
--
-- Ejemplo:
--   A
--   B
--   C
--   D
-- ============================================================

CREATE TABLE tipo_tarifa (
    cod_tipo_tarifa VARCHAR(20) NOT NULL,                        -- 'A', 'B', 'C', 'D'
    cod_comercializadora VARCHAR(20) NOT NULL 
        REFERENCES comercializadora(cod_comercializadora),       -- FK a comercializadora ('ENERTOTAL', etc.)
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    -- La combinación Tipo + Comercializador garantiza la unicidad
    PRIMARY KEY (cod_comercializadora, cod_tipo_tarifa)
);

COMMENT ON TABLE tipo_tarifa IS 'Estructuras o esquemas tarifarios definidos por cada comercializador';

-- Poblar catálogo de Tipo de Tarifa (Ejemplo para ENERTOTAL)
INSERT INTO tipo_tarifa (cod_comercializadora, cod_tipo_tarifa, nombre, descripcion) VALUES
('ENERTOTAL', 'A', 'Tipo A', 'CU. Aplica para I, C, O y E; estratos 4, 5 y 6; y estratos 1, 2 y 3 cuando el consumo es mayor que CS*'),
('ENERTOTAL', 'B', 'Tipo B', 'CU. Aplica para estrato 3 cuando el consumo es menor que CS*'),
('ENERTOTAL', 'C', 'Tipo C', 'CU. Aplica para estrato 2 cuando el consumo es menor que CS*'),
('ENERTOTAL', 'D', 'Tipo D', 'CU. Aplica para estrato 1 cuando el consumo es menor que CS*');


-- =====================================================
--10. TABLA: TARIFA
-- =====================================================
CREATE TABLE Tarifa (
    id_tarifa BIGSERIAL PRIMARY KEY,
    cod_comercializadora VARCHAR(30) NOT NULL,
    cod_mercado VARCHAR(50) NOT NULL,
    cod_nivel VARCHAR(20) NOT NULL,
    cod_tipo_tarifa VARCHAR(5),
    codigo_tarifa VARCHAR(50) UNIQUE,
    nombre_tarifa VARCHAR(200),
	estrato VARCHAR(5),
    resolucion_regulatoria VARCHAR(100),
    activa BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_tarifa_comercializadora FOREIGN KEY (cod_comercializadora) REFERENCES Comercializadora(cod_comercializadora),
	CONSTRAINT fk_tarifa_mercado FOREIGN KEY (cod_mercado) REFERENCES Mercado_Red(cod_mercado),
	CONSTRAINT fk_tarifa_nivel_tension FOREIGN KEY (cod_nivel) REFERENCES nivel_tension(cod_nivel),
	CONSTRAINT fk_tarifa_tipo_tarifa FOREIGN KEY (cod_comercializadora, cod_tipo_tarifa)
    REFERENCES tipo_tarifa (cod_comercializadora, cod_tipo_tarifa)
);

COMMENT ON TABLE Tarifa IS 'Plan tarifario del usuario - versión simplificada';
COMMENT ON COLUMN Tarifa.cod_comercializadora IS 'ENERTOTAL, VATIA, QIENERGY, etc.';
COMMENT ON COLUMN Tarifa.cod_mercado IS 'CALI, VALLE, NARIÑO, ANTIOQUIA UNIF, BOGOTA';
COMMENT ON COLUMN Tarifa.cod_nivel IS 'Nivel 3, Nivel 2, Nivel 1.1, N 1.2-1.3, etc.';
COMMENT ON COLUMN Tarifa.cod_tipo_tarifa IS 'A, B, C, D - puede ser null';
COMMENT ON COLUMN Tarifa.codigo_tarifa IS 'Ej: CALI-N1.1-A';
COMMENT ON COLUMN Tarifa.resolucion_regulatoria IS 'CREG 119/2007, CREG 101/2023, etc.';

CREATE INDEX idx_tarifa_comercializadora ON Tarifa(cod_comercializadora);
CREATE INDEX idx_tarifa_activa ON Tarifa(activa);




-- ============================================================
-- =====================================================
-- 11. TABLA: Tipo de Cargo (Naturaleza Matemática del Cobro)
-- =====================================================
CREATE TABLE tipo_cargo (
    cod_tipo_cargo VARCHAR(30) PRIMARY KEY, -- 'VARIABLE_ENERGIA', 'CFM_CREG', 'DEMANDA_POTENCIA', etc.
    nombre VARCHAR(100) NOT NULL,
    unidad VARCHAR(20) NOT NULL                 -- 'COP/kWh', 'COP/mes', 'COP/kW-mes', 'COP/día'
);

COMMENT ON TABLE tipo_cargo IS 'Catálogo que define la dimensión matemática y la unidad de medida de cada concepto tarifario';

-- Poblar catálogo de Tipos de Cargo
INSERT INTO tipo_cargo (cod_tipo_cargo, nombre, unidad) VALUES
-- Cargos por Consumo de Energía (Volumétricos / Variables)
('VARIABLE_ENERGIA', 'Costo Variable por Consumo de Energía',     'COP/kWh'),
('ENERGIA_EXCEDENTE', 'Cobro o Crédito por Excedentes de Energía',   'COP/kWh'),
('OPCION_TARIFARIA', 'Recuperación o Diferimiento por Opción Tarifaria', 'COP/kWh'),

-- Cargos Fijos (Periódicos por Usuario o Punto de Medición)
('CFMJ_CREG',         'Costo Fijo de Comercialización CREG',      'COP/mes'),
('CARGO_FIJO',       'Cargo Fijo General por Suscriptor',         'COP/mes'),
('CONEXION_DIA',     'Cargo Fijo Diario por Punto de Conexión',  'COP/día'),

-- Cargos por Potencia y Capacidad (Demanda)
('DEMANDA_POTENCIA', 'Cargo por Demanda Máxima de Potencia',      'COP/kW-mes'),
('DEMANDA_KW',       'Cargo por Potencia Facturable o Suscrita',  'COP/kW-mes'),
('DEMANDA_PICO',     'Cargo por Demanda en Horas de Pico',        'COP/kW-mes'),
('EXCESO_REACTIVA',  'Penalización por Energía Reactiva',         'COP/kVARh');



-- ============================================================
-- 12. COMPONENTES DEL CU
--
-- Ejemplos:
--   G
--   T
--   D
--   C / Cv
--   PR
--   R
--   COT
-- ============================================================

CREATE TABLE componente_costo (
    cod_componente VARCHAR(15) PRIMARY KEY, -- 'Gm', 'Tm', 'Dm', 'Cm', 'PRm', 'Rm', 'Cfmj'
    nombre VARCHAR(100) NOT NULL,
    cod_tipo_cargo VARCHAR(30) NOT NULL REFERENCES tipo_cargo(cod_tipo_cargo),
    descripcion TEXT
);

COMMENT ON TABLE componente_costo IS 'Catálogo maestro de componentes del Costo Unitario de Prestación del Servicio (CU) y Costo Fijo';

-- Poblar el catálogo completo CREG
INSERT INTO componente_costo (cod_componente, nombre, cod_tipo_cargo, descripcion) VALUES
('Gm',   'Costo de Generación',                'VARIABLE_ENERGIA', 'Costo de compra de energía en bolsa y contratos ($/kWh)'),
('Tm',   'Costo de Transmisión Nacional',       'VARIABLE_ENERGIA', 'Costo por uso del Sistema de Transmisión Nacional STN ($/kWh)'),
('Dm',   'Costo de Distribución',               'VARIABLE_ENERGIA', 'Costo por uso del Sistema de Distribución Local SDL ($/kWh)'),
('Cm',   'Costo Comercialización Volumétrico',  'VARIABLE_ENERGIA', 'Margen o costo de comercialización por unidad de energía ($/kWh)'),
('PRm',  'Costo de Pérdidas Reconocidas',       'VARIABLE_ENERGIA', 'Costo de pérdidas de energía transferidas al usuario ($/kWh)'),
('Rm',   'Costo de Restricciones',              'VARIABLE_ENERGIA', 'Costo de restricciones y servicios asociados a la generación ($/kWh)'),
('COT', 'Costo de Opción Tarifaria', 'VARIABLE_ENERGIA', 'Costo asociado con la recuperación del saldo de la opción tarifaria del nivel n, mercado j y mes m ($/kWh)'),
('Cfmj', 'Costo Fijo de Comercialización',      'CFMJ_CREG',        'Costo fijo base por suscriptor/mes del mercado j (COP/mes)');
	 
-- ============================================================
-- 13. FRANJA_HORARIA
--
--Identifica la configuración aplicable a una tarifa o conjunto de tarifas.
-- ============================================================

CREATE TABLE franja_horaria (
    id_franja_horaria SMALLINT
        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    cod_comercializadora VARCHAR(30) NOT NULL,
	codigo            VARCHAR(30) NOT NULL,

    tipo_dia        varchar(10) NOT NULL,
	activo BOOLEAN DEFAULT TRUE,
	
	
	CONSTRAINT fk_tarifa_comercializadora FOREIGN KEY (cod_comercializadora) REFERENCES Comercializadora(cod_comercializadora),
	CONSTRAINT ck_tipo_dia
		CHECK (tipo_dia IN (
			'TODOS',
			'LABORAL',
			'SABADO',
			'DOMINGO',
			'FESTIVO'
		)),
	CONSTRAINT uq_franja_comercializadora_tipo_dia 
        UNIQUE (cod_comercializadora, codigo, tipo_dia)
);


INSERT INTO franja_horaria (
    cod_comercializadora,
    codigo,
    tipo_dia,
    activo
)
VALUES
    ('ENERTOTAL', 'F1', 'TODOS', TRUE),
    ('ENERTOTAL', 'F2', 'TODOS', TRUE),
    ('ENERTOTAL', 'F3', 'TODOS', TRUE),
    ('ENERTOTAL', 'F4', 'TODOS', TRUE),
    ('ENERTOTAL', 'F5', 'TODOS', TRUE),
    ('ENERTOTAL', 'F6', 'TODOS', TRUE),
    ('ENERTOTAL', 'F7', 'TODOS', TRUE),
    ('ENERTOTAL', 'F8', 'TODOS', TRUE);
	

-- ============================================================
-- 14. Catálogo de configuraciones horarias
--
-- Relaciona el grupo de horas relacionado a una misma franja y define el bloque horario de la tarifa.	
-- ============================================================


CREATE TABLE configuracion_horaria (
    id_configuracion_horaria SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cod_comercializadora     VARCHAR(20) NOT NULL REFERENCES comercializadora(cod_comercializadora),
    codigo                   VARCHAR(30) NOT NULL,
    descripcion              TEXT,
    activo                   BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (cod_comercializadora, codigo),
    UNIQUE (id_configuracion_horaria, cod_comercializadora)   -- para la FK compuesta de configuracion_aplicable
);

-- Datos: configuraciones (filas 0..9 del cuadro)
INSERT INTO configuracion_horaria (cod_comercializadora, codigo, descripcion) VALUES
('ENERTOTAL','CH00','Fila 0 del cuadro de franjas'),
('ENERTOTAL','CH01','Fila 1 del cuadro de franjas'),
('ENERTOTAL','CH02','Fila 2 del cuadro de franjas'),
('ENERTOTAL','CH03','Fila 3 del cuadro de franjas'),
('ENERTOTAL','CH04','Fila 4 del cuadro de franjas'),
('ENERTOTAL','CH05','Fila 5 del cuadro de franjas'),
('ENERTOTAL','CH06','Fila 6 del cuadro de franjas'),
('ENERTOTAL','CH07','Fila 7 del cuadro de franjas'),
('ENERTOTAL','CH08','Fila 8 del cuadro de franjas'),
('ENERTOTAL','CH09','Fila 9 del cuadro de franjas');


-- ============================================================
-- 15. CONFIGURACIÓN-FRANJA
--
-- Define Qué franjas existen en cada configuración (las N.A. no tienen fila)
-- ============================================================

CREATE TABLE configuracion_franja (
    id_configuracion_horaria SMALLINT NOT NULL REFERENCES configuracion_horaria(id_configuracion_horaria) ON DELETE CASCADE,
    id_franja_horaria        SMALLINT NOT NULL REFERENCES franja_horaria(id_franja_horaria),
    tipo_hora                VARCHAR(10) CHECK (tipo_hora IN ('PICO','MEDIA','VALLE')),  -- opcional
    PRIMARY KEY (id_configuracion_horaria, id_franja_horaria)
);


-- Franjas que existen en cada configuración
INSERT INTO configuracion_franja (id_configuracion_horaria, id_franja_horaria)
SELECT c.id_configuracion_horaria, f.id_franja_horaria
FROM (VALUES
    ('CH00','F1'),
    ('CH00','F2'),
    ('CH00','F3'),
    ('CH00','F4'),
    ('CH00','F5'),
    ('CH01','F1'),
    ('CH01','F2'),
    ('CH01','F3'),
    ('CH01','F4'),
    ('CH01','F5'),
    ('CH01','F6'),
    ('CH01','F7'),
    ('CH01','F8'),
    ('CH02','F1'),
    ('CH02','F2'),
    ('CH02','F3'),
    ('CH02','F4'),
    ('CH02','F5'),
    ('CH02','F6'),
    ('CH02','F7'),
    ('CH02','F8'),
    ('CH03','F1'),
    ('CH03','F2'),
    ('CH03','F3'),
    ('CH03','F4'),
    ('CH03','F5'),
    ('CH03','F6'),
    ('CH03','F7'),
    ('CH04','F1'),
    ('CH04','F2'),
    ('CH04','F3'),
    ('CH04','F4'),
    ('CH04','F5'),
    ('CH04','F6'),
    ('CH04','F7'),
    ('CH05','F1'),
    ('CH05','F2'),
    ('CH05','F3'),
    ('CH05','F4'),
    ('CH05','F5'),
    ('CH05','F6'),
    ('CH05','F7'),
    ('CH06','F1'),
    ('CH06','F2'),
    ('CH06','F3'),
    ('CH06','F4'),
    ('CH06','F5'),
    ('CH06','F6'),
    ('CH06','F7'),
    ('CH07','F1'),
    ('CH07','F2'),
    ('CH07','F3'),
    ('CH07','F4'),
    ('CH07','F5'),
    ('CH07','F6'),
    ('CH08','F1'),
    ('CH08','F2'),
    ('CH08','F3'),
    ('CH08','F4'),
    ('CH08','F5'),
    ('CH08','F6'),
    ('CH09','F1'),
    ('CH09','F2'),
    ('CH09','F3'),
    ('CH09','F4'),
    ('CH09','F5'),
    ('CH09','F6')
) AS v(cfg, fr)
JOIN configuracion_horaria c ON c.cod_comercializadora = 'ENERTOTAL' AND c.codigo = v.cfg
JOIN franja_horaria f        ON f.cod_comercializadora = 'ENERTOTAL' AND f.codigo = v.fr
                            AND f.tipo_dia = 'TODOS';

-- ============================================================
-- 16. CONFIGURACIÓN-HORA
--
-- Define Hora -> franja dentro de una configuración (una sola franja por hora)
-- ============================================================

CREATE TABLE configuracion_hora (
    id_configuracion_horaria SMALLINT NOT NULL,
    hora                     SMALLINT NOT NULL CHECK (hora BETWEEN 1 AND 24),
    id_franja_horaria        SMALLINT NOT NULL,
    PRIMARY KEY (id_configuracion_horaria, hora),
    FOREIGN KEY (id_configuracion_horaria, id_franja_horaria)
        REFERENCES configuracion_franja (id_configuracion_horaria, id_franja_horaria)
        ON DELETE CASCADE
);
COMMENT ON COLUMN configuracion_hora.hora IS 'hora = 1 es 00:00-01:00; hora = 24 es 23:00-24:00';



-- Horas de cada franja, por configuración
INSERT INTO configuracion_hora (id_configuracion_horaria, hora, id_franja_horaria)
SELECT c.id_configuracion_horaria, h, f.id_franja_horaria
FROM (VALUES
    ('CH00','F1', ARRAY[1,2,3,4,24]),
    ('CH00','F2', ARRAY[5,6,7,8,9,13,14,15,16,17,18,23]),
    ('CH00','F3', ARRAY[10,11,12]),
    ('CH00','F4', ARRAY[19,20,21]),
    ('CH00','F5', ARRAY[22]),
    ('CH01','F1', ARRAY[1,2,3,4,24]),
    ('CH01','F2', ARRAY[5,23]),
    ('CH01','F3', ARRAY[6,7,8,13,14,15,16,17,18]),
    ('CH01','F4', ARRAY[9]),
    ('CH01','F5', ARRAY[10,11,12]),
    ('CH01','F6', ARRAY[19,20]),
    ('CH01','F7', ARRAY[21]),
    ('CH01','F8', ARRAY[22]),
    ('CH02','F1', ARRAY[1,2,3,4,24]),
    ('CH02','F2', ARRAY[5,15,16,23]),
    ('CH02','F3', ARRAY[6,7,8,13,14,17,18]),
    ('CH02','F4', ARRAY[9]),
    ('CH02','F5', ARRAY[10,11,12]),
    ('CH02','F6', ARRAY[19,20]),
    ('CH02','F7', ARRAY[21]),
    ('CH02','F8', ARRAY[22]),
    ('CH03','F1', ARRAY[1,2,3,4,24]),
    ('CH03','F2', ARRAY[5,6,7,8,13,14,15,16,17,23]),
    ('CH03','F3', ARRAY[9,18]),
    ('CH03','F4', ARRAY[10,11,12]),
    ('CH03','F5', ARRAY[19,20]),
    ('CH03','F6', ARRAY[21]),
    ('CH03','F7', ARRAY[22]),
    ('CH04','F1', ARRAY[1,2,3,4,24]),
    ('CH04','F2', ARRAY[5,23]),
    ('CH04','F3', ARRAY[6,7,8,9,13,14,15,16,17,18]),
    ('CH04','F4', ARRAY[10,11,12]),
    ('CH04','F5', ARRAY[19,20]),
    ('CH04','F6', ARRAY[21]),
    ('CH04','F7', ARRAY[22]),
    ('CH05','F1', ARRAY[1,2,3,4,24]),
    ('CH05','F2', ARRAY[5,6,7,8,23]),
    ('CH05','F3', ARRAY[9,13,14,15,16,17,18]),
    ('CH05','F4', ARRAY[10,11,12]),
    ('CH05','F5', ARRAY[19,20]),
    ('CH05','F6', ARRAY[21]),
    ('CH05','F7', ARRAY[22]),
    ('CH06','F1', ARRAY[1,2,3,4,24]),
    ('CH06','F2', ARRAY[5,6,7,13,18,23]),
    ('CH06','F3', ARRAY[8,9,14,15,16,17]),
    ('CH06','F4', ARRAY[10,11,12]),
    ('CH06','F5', ARRAY[19,21]),
    ('CH06','F6', ARRAY[20]),
    ('CH06','F7', ARRAY[22]),
    ('CH07','F1', ARRAY[1,2,3,4,24]),
    ('CH07','F2', ARRAY[5,14,15]),
    ('CH07','F3', ARRAY[6,7,8,9,13,16,17,18,23]),
    ('CH07','F4', ARRAY[10,11,12]),
    ('CH07','F5', ARRAY[19,20,21]),
    ('CH07','F6', ARRAY[22]),
    ('CH08','F1', ARRAY[1,2,3,4,24]),
    ('CH08','F2', ARRAY[5]),
    ('CH08','F3', ARRAY[6,7,8,9,13,14,15,16,17,18,23]),
    ('CH08','F4', ARRAY[10,11,12]),
    ('CH08','F5', ARRAY[19,20,21]),
    ('CH08','F6', ARRAY[22]),
    ('CH09','F1', ARRAY[1,24]),
    ('CH09','F2', ARRAY[2,3,4]),
    ('CH09','F3', ARRAY[5,6,7,8,9,13,14,15,16,17,18,23]),
    ('CH09','F4', ARRAY[10,11,12]),
    ('CH09','F5', ARRAY[19,20,21]),
    ('CH09','F6', ARRAY[22])
) AS v(cfg, fr, horas)
CROSS JOIN LATERAL unnest(v.horas) AS h
JOIN configuracion_horaria c ON c.cod_comercializadora = 'ENERTOTAL' AND c.codigo = v.cfg
JOIN franja_horaria f        ON f.cod_comercializadora = 'ENERTOTAL' AND f.codigo = v.fr
                            AND f.tipo_dia = 'TODOS';


-- ============================================================
-- 17. CONFIGURACIÓN-APLICABLE
--
-- Define qué configuración aplica a cada mercado + nivel de tensión (con vigencia)
-- ============================================================
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE configuracion_aplicable (
    id_configuracion_aplicable BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cod_comercializadora       VARCHAR(20) NOT NULL,
    cod_mercado                VARCHAR(30) NOT NULL REFERENCES mercado_red(cod_mercado),
    cod_nivel                  VARCHAR(15) NOT NULL REFERENCES nivel_tension(cod_nivel),
    id_configuracion_horaria   SMALLINT    NOT NULL,
    vigente_desde              DATE        NOT NULL,
    vigente_hasta              DATE,                       -- NULL = sigue vigente
    CONSTRAINT ck_aplicable_fechas
        CHECK (vigente_hasta IS NULL OR vigente_hasta >= vigente_desde),
    CONSTRAINT fk_aplicable_configuracion
        FOREIGN KEY (id_configuracion_horaria, cod_comercializadora)
        REFERENCES configuracion_horaria (id_configuracion_horaria, cod_comercializadora),
    CONSTRAINT ex_aplicable_sin_traslape EXCLUDE USING gist (
        cod_comercializadora WITH =,
        cod_mercado          WITH =,
        cod_nivel            WITH =,
        (daterange(vigente_desde, vigente_hasta, '[]')) WITH &&
    )
);



-- ============================================================
-- 18. PERÍODO TARIFARIO
--
-- Ejemplo:
--   Octubre 2024
--   Noviembre 2024
--
-- Se separa del período de facturación.
-- Una misma tarifa puede tener varias versiones para el mismo
-- período debido a correcciones o republicaciones.
-- ============================================================

CREATE TABLE periodo_tarifario (
    id_periodo_tarifario BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	id_tarifa            BIGINT NOT NULL,
	id_configuracion_horaria SMALLINT,

    anio                 SMALLINT NOT NULL,
    mes                  SMALLINT NOT NULL,

    fecha_inicio         DATE NOT NULL,
    fecha_fin            DATE NOT NULL,
	
	numero_version       INTEGER NOT NULL,

    fecha_calculo        DATE,
    fecha_publicacion    DATE,

    estado               VARCHAR(20) NOT NULL DEFAULT 'BORRADOR',

    observaciones        TEXT,

    creada_en            TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_periodo_tarifario_anio_mes
        UNIQUE (id_tarifa, anio, mes, numero_version),
		
	CONSTRAINT uq_periodo_config
    UNIQUE (id_periodo_tarifario, id_configuracion_horaria),   -- destino de la FK compuesta de tarifa_valor
	
	CONSTRAINT fk_periodo_configuracion
    FOREIGN KEY (id_configuracion_horaria) REFERENCES configuracion_horaria(id_configuracion_horaria),

    CONSTRAINT ck_periodo_tarifario_mes
        CHECK (mes BETWEEN 1 AND 12),

    CONSTRAINT ck_periodo_tarifario_fechas
        CHECK (fecha_inicio <= fecha_fin),
		
	CONSTRAINT fk_version_tarifa_tarifa
        FOREIGN KEY (id_tarifa)
        REFERENCES tarifa(id_tarifa),

    CONSTRAINT ck_version_tarifa_numero
        CHECK (numero_version > 0),

    CONSTRAINT ck_version_tarifa_estado
        CHECK (
            estado IN (
                'BORRADOR',
                'PUBLICADA',
                'SUPERADA',
                'ANULADA'
            )
        )
		
);

CREATE UNIQUE INDEX uq_periodo_publicado
    ON periodo_tarifario (id_tarifa, anio, mes) WHERE estado = 'PUBLICADA';

-- ============================================================
-- Función de búsqueda y enlace con periodo_tarifario
-- ============================================================
CREATE OR REPLACE FUNCTION fn_configuracion_aplicable(
    p_comercializadora VARCHAR, p_mercado VARCHAR, p_nivel VARCHAR, p_fecha DATE)
RETURNS SMALLINT LANGUAGE sql STABLE AS $$
    SELECT id_configuracion_horaria
    FROM configuracion_aplicable
    WHERE cod_comercializadora = p_comercializadora
      AND cod_mercado          = p_mercado
      AND cod_nivel            = p_nivel
      AND daterange(vigente_desde, vigente_hasta, '[]') @> p_fecha
$$;



-- Si no se indica configuración, se toma la aplicable al mercado+nivel de la tarifa
-- en la fecha de inicio del período. Si no hay vigencia cargada queda NULL.
CREATE OR REPLACE FUNCTION trg_periodo_config() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.id_configuracion_horaria IS NULL THEN
        SELECT fn_configuracion_aplicable(t.cod_comercializadora, t.cod_mercado, t.cod_nivel, NEW.fecha_inicio)
          INTO NEW.id_configuracion_horaria
          FROM tarifa t
         WHERE t.id_tarifa = NEW.id_tarifa;
    END IF;
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_periodo_config ON periodo_tarifario;
CREATE TRIGGER trg_periodo_config
    BEFORE INSERT ON periodo_tarifario
    FOR EACH ROW EXECUTE FUNCTION trg_periodo_config();

-- ============================================================
-- 19. TARIFA POR FRANJA y CU
--
-- Esta es la tabla que contiene el valor monetario.
--
-- Para monomia sencilla:
--
--   id_configuracion_horaria = NULL
--
-- Para monomia horaria:
--
--   id_configuracion_horaria
-- ============================================================

CREATE TABLE tarifa_valor (
    id_tarifa_valor          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_periodo_tarifario     BIGINT NOT NULL REFERENCES periodo_tarifario(id_periodo_tarifario),
    id_configuracion_horaria SMALLINT,
    id_franja_horaria        SMALLINT,
    valor                    NUMERIC(18,6) NOT NULL CHECK (valor >= 0),
    unidad                   VARCHAR(30) NOT NULL DEFAULT 'COP/kWh',
    CONSTRAINT fk_tv_periodo_config
        FOREIGN KEY (id_periodo_tarifario, id_configuracion_horaria)
        REFERENCES periodo_tarifario (id_periodo_tarifario, id_configuracion_horaria),
    CONSTRAINT fk_tv_config_franja
        FOREIGN KEY (id_configuracion_horaria, id_franja_horaria)
        REFERENCES configuracion_franja (id_configuracion_horaria, id_franja_horaria),
    CONSTRAINT ck_tv_config_franja
        CHECK ((id_configuracion_horaria IS NULL) = (id_franja_horaria IS NULL))
);
CREATE UNIQUE INDEX uq_tv_franja ON tarifa_valor
    (id_periodo_tarifario, id_franja_horaria) WHERE id_franja_horaria IS NOT NULL;
CREATE UNIQUE INDEX uq_tv_monomia ON tarifa_valor (id_periodo_tarifario)
    WHERE id_franja_horaria IS NULL;


-- ============================================================
-- 20. EL VALOR DE CADA COMPONENTE AL MES
--
-- Los valores de los componentes fijos y variables con los que se construye la tarifa,
---en especial el costo unitario
-- ============================================================

CREATE TABLE componente_valor_mes (
    id_componente_valor_mes BIGSERIAL PRIMARY KEY,
	id_periodo_tarifario  BIGINT NOT NULL,
    cod_componente VARCHAR(15) NOT NULL REFERENCES componente_costo(cod_componente),

    valor NUMERIC(12,4) NOT NULL,
	
	CONSTRAINT fk_tarifa_valor_periodo_tarifario
        FOREIGN KEY (id_periodo_tarifario)
        REFERENCES periodo_tarifario(id_periodo_tarifario),
    
    -- Unicidad del precio por combinación de dimensiones
    CONSTRAINT unq_componente_dimensiones_periodo 
        UNIQUE (id_periodo_tarifario, cod_componente)
);
	



-- 8. Validaciones (deben devolver 0 filas)
-- 8.1 Configuraciones que no cubren las 24 horas
SELECT c.codigo, count(h.hora) AS horas_cargadas
FROM configuracion_horaria c
LEFT JOIN configuracion_hora h USING (id_configuracion_horaria)
GROUP BY c.codigo
HAVING count(h.hora) <> 24;

-- 8.2 Franjas declaradas sin ninguna hora
SELECT c.codigo, f.codigo AS franja
FROM configuracion_franja cf
JOIN configuracion_horaria c USING (id_configuracion_horaria)
JOIN franja_horaria f USING (id_franja_horaria)
LEFT JOIN configuracion_hora h USING (id_configuracion_horaria, id_franja_horaria)
WHERE h.hora IS NULL;

-- =====================================================================
-- Qué configuración aplica a cada mercado + nivel.
--    Plantilla (los valores son SOLO un ejemplo; reemplázalos por los reales):
-- =====================================================================
-- =====================================================================
-- CARGA DE configuracion_aplicable (qué configuración horaria aplica a cada
-- mercado + nivel de tensión) para ENERTOTAL.
--==============================================================

BEGIN;

-- 2. Asignación mercado + nivel -> configuración
DO $$
DECLARE
    v_desde CONSTANT DATE := DATE '2024-01-01';   -- <-- AJUSTAR: fecha desde la que rigen
    v_esperadas CONSTANT INT := 69;
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
        ('VALLE', 'N4', 'CH00'),
        ('VALLE', 'N3', 'CH00'),
        ('VALLE', 'N2', 'CH00'),
        ('VALLE', 'N1_1', 'CH00'),
        ('VALLE', 'N1_2', 'CH00'),
        ('VALLE', 'N1_2_50', 'CH00'),
        ('NARINO', 'N2', 'CH01'),
        ('NARINO', 'N1_1', 'CH02'),
        ('NARINO', 'N1_2', 'CH02'),
        ('NARINO', 'N1_2_50', 'CH02'),
        ('ANTIOQUIA_UNIF', 'N3', 'CH03'),
        ('ANTIOQUIA_UNIF', 'N2', 'CH04'),
        ('ANTIOQUIA_UNIF', 'N1_1', 'CH04'),
        ('ANTIOQUIA_UNIF', 'N1_2', 'CH04'),
        ('ANTIOQUIA_UNIF', 'N1_2_50', 'CH04'),
        ('BOGOTA', 'N3', 'CH00'),
        ('BOGOTA', 'N2', 'CH00'),
        ('BOGOTA', 'N1_1', 'CH00'),
        ('BOGOTA', 'N1_2', 'CH00'),
        ('BOGOTA', 'N1_2_50', 'CH00'),
        ('CAUCA', 'N3', 'CH05'),
        ('CAUCA', 'N2', 'CH06'),
        ('CAUCA', 'N1_1', 'CH07'),
        ('CAUCA', 'N1_2', 'CH07'),
        ('BOYACA', 'N3', 'CH00'),
        ('BOYACA', 'N2', 'CH00'),
        ('BOYACA', 'N1_1', 'CH00'),
        ('BOYACA', 'N1_2', 'CH00'),
        ('CARIBE_MAR', 'N2', 'CH00'),
        ('CARIBE_MAR', 'N1_1', 'CH00'),
        ('CARIBE_MAR', 'N1_2', 'CH00'),
        ('CARIBE_SOL', 'N2', 'CH00'),
        ('CARIBE_SOL', 'N1_1', 'CH00'),
        ('CARIBE_SOL', 'N1_2', 'CH00'),
        ('CALDAS', 'N1_2_50', 'CH08'),
        ('CARTAGO', 'N2', 'CH00'),
        ('CARTAGO', 'N1_1', 'CH00'),
        ('CARTAGO', 'N1_2', 'CH00'),
        ('TOLIMA', 'N2', 'CH00'),
        ('TOLIMA', 'N1_1', 'CH09'),
        ('TOLIMA', 'N1_2', 'CH09'),
        ('PEREIRA', 'N2', 'CH00'),
        ('PEREIRA', 'N1_1', 'CH00'),
        ('PEREIRA', 'N1_2', 'CH00'),
        ('QUINDIO', 'N3', 'CH00'),
        ('QUINDIO', 'N2', 'CH00'),
        ('QUINDIO', 'N1_1', 'CH00'),
        ('QUINDIO', 'N1_2', 'CH00'),
        ('CETSA', 'N3', 'CH00'),
        ('CETSA', 'N2', 'CH00'),
        ('CETSA', 'N1_1', 'CH00'),
        ('CETSA', 'N1_2', 'CH00'),
        ('SANTANDER', 'N3', 'CH00'),
        ('SANTANDER', 'N2', 'CH00'),
        ('SANTANDER', 'N1_1', 'CH00'),
        ('SANTANDER', 'N1_2', 'CH00'),
        ('HUILA', 'N3', 'CH00'),
        ('HUILA', 'N2', 'CH00'),
        ('HUILA', 'N1_1', 'CH00'),
        ('HUILA', 'N1_2', 'CH00'),
        ('META', 'N3', 'CH00'),
        ('META', 'N2', 'CH00'),
        ('META', 'N1_1', 'CH00'),
        ('META', 'N1_2', 'CH00')
    ) AS v(mercado, nivel, cfg)
    JOIN configuracion_horaria c
      ON c.cod_comercializadora = 'ENERTOTAL' AND c.codigo = v.cfg;

    GET DIAGNOSTICS v_insertadas = ROW_COUNT;
    IF v_insertadas <> v_esperadas THEN
        RAISE EXCEPTION 'Se esperaban % filas y se insertaron %', v_esperadas, v_insertadas;
    END IF;
END $$;

-- 3. Verificación: configuración y cantidad de mercado+nivel por configuración
SELECT c.codigo, count(*) AS combinaciones, count(DISTINCT a.cod_mercado) AS mercados
FROM configuracion_aplicable a
JOIN configuracion_horaria c USING (id_configuracion_horaria)
GROUP BY c.codigo ORDER BY c.codigo;




-- =====================================================================
-- MIGRACIÓN: Usuario -> Cliente en las tablas de HarmoniWatts
-- Ejecutar DESPUÉS de crear la tabla cliente (script TAP).
--
-- Antes de ejecutar, revisa si hay datos (la FK nueva exige que cada
-- id_cliente exista en cliente):
--   SELECT 'vivienda' AS tabla, count(*) FROM vivienda
--   UNION ALL SELECT 'conexionexterna', count(*) FROM conexionexterna;
-- Si hay filas, primero hay que crear en cliente los registros que
-- correspondan a esos id; de lo contrario ADD CONSTRAINT falla y la
-- transacción se revierte completa.
--
-- Como ahora hay una sola vivienda por cliente, verifica que no existan
-- usuarios con varias (debe devolver 0 filas; si no, el UNIQUE falla):
--   SELECT id_usuario, count(*) FROM vivienda GROUP BY id_usuario HAVING count(*) > 1;
-- =====================================================================

BEGIN;

-- 1. VIVIENDA --------------------------------------------------------
-- Un cliente tiene una sola vivienda: el UNIQUE hace la relación 1 a 1
-- (y su índice reemplaza al índice simple anterior).
ALTER TABLE vivienda DROP CONSTRAINT IF EXISTS fk_vivienda_usuario;
ALTER TABLE vivienda RENAME COLUMN id_usuario TO id_cliente;
DROP INDEX IF EXISTS idx_vivienda_usuario;
ALTER TABLE vivienda
    ADD CONSTRAINT uq_vivienda_cliente UNIQUE (id_cliente);
ALTER TABLE vivienda
    ADD CONSTRAINT fk_vivienda_cliente
    FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente) ON DELETE CASCADE;
COMMENT ON TABLE vivienda IS 'Vivienda del cliente (una por cliente)';

-- 2. CONEXIONEXTERNA -------------------------------------------------
ALTER TABLE conexionexterna DROP CONSTRAINT IF EXISTS fk_conexion_usuario;
ALTER TABLE conexionexterna RENAME COLUMN id_usuario TO id_cliente;
ALTER INDEX IF EXISTS idx_conexion_usuario RENAME TO idx_conexion_cliente;
ALTER TABLE conexionexterna
    ADD CONSTRAINT fk_conexion_cliente
    FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente) ON DELETE CASCADE;

-- 3. FUNCIÓN que apuntaba a Usuario ----------------------------------
-- (el trigger sigue comentado, como en el esquema original)
CREATE OR REPLACE FUNCTION actualizar_ultimo_acceso()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE cliente SET ultimo_acceso = NOW() WHERE id_cliente = NEW.id_cliente;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. VISTA que unía Recomendacion -> Vivienda -> Usuario -------------
-- Se elimina porque no se puede renombrar su columna de salida "usuario".
-- La columna ahora se llama "cliente".
DROP VIEW IF EXISTS v_recomendaciones_pendientes;

CREATE VIEW v_recomendaciones_pendientes AS
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
    c.nombre AS cliente
FROM Recomendacion r
INNER JOIN Electrodomestico e ON r.id_electro = e.id_electro
INNER JOIN Vivienda v         ON r.id_vivienda = v.id_vivienda
INNER JOIN cliente c          ON v.id_cliente = c.id_cliente
WHERE r.estado = 'pendiente'
  AND r.fecha_propuesta >= CURRENT_DATE
ORDER BY r.prioridad ASC, r.ahorro_estimado_eur DESC;

COMMENT ON VIEW v_recomendaciones_pendientes IS 'Recomendaciones pendientes por vivienda';


COMMIT;

