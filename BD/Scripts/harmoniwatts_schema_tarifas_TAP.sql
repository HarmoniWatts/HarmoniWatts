------Nueva tabla de zonas geográficas (reemplaza STATE):
CREATE TABLE ZONA_GEOGRAFICA (
    id_zona SMALLSERIAL PRIMARY KEY,
    nombre_zona VARCHAR(50) NOT NULL,  -- 'CALI', 'VALLE', 'BOGOTA', etc.
    departamento VARCHAR(50),
    region VARCHAR(50)
);


-----Nivel 2: Tarifa (Tariff)
-----Campos a añadir a Tarifa:
ALTER TABLE Tarifa ADD COLUMN estrato_min TINYINT;
ALTER TABLE Tarifa ADD COLUMN estrato_max TINYINT;
ALTER TABLE Tarifa ADD COLUMN min_kwh FLOAT;
ALTER TABLE Tarifa ADD COLUMN max_kwh FLOAT;
ALTER TABLE Tarifa ADD COLUMN id_zona SMALLINT;
ALTER TABLE Tarifa ADD CONSTRAINT fk_tarifa_zona FOREIGN KEY (id_zona) REFERENCES ZONA_GEOGRAFICA(id_zona);


-----Nivel 3: GrupoTarifa (Group)
-----Transformación crítica: Por cada id_tarifa, se crean 6 registros en GRUPO_TARIFA
---#Generación, Transmisión, Distribución,Comercialización, Pérdidas,Restricciones

----Los valores de G, T, D, CV, PR, R pueden provenir de la suma/descomposición de CU_BASE
----Se recomienda mantener ComponenteTarifa para auditoría y migrar los valores a GRUPO_TARIFA
CREATE TABLE GRUPO_TARIFA (
    id_grupo BIGSERIAL PRIMARY KEY,
    id_tarifa BIGINT NOT NULL,
    codigo_grupo VARCHAR(5) NOT NULL,  -- 'G', 'T', 'D', 'CV', 'PR', 'R'
    nombre_grupo VARCHAR(50) NOT NULL,
    rate_type_id TINYINT DEFAULT 1,     -- 1=energía
    temporada ENUM('S', 'W', 'A') DEFAULT 'A',  -- S=verano, W=invierno, A=anual
    periodo_dia ENUM('N', 'F', 'S', 'A') DEFAULT 'A', -- N=punta, F=valle, S=intermedio, A=diario
    CONSTRAINT fk_grupo_tarifa FOREIGN KEY (id_tarifa) REFERENCES Tarifa(id_tarifa) ON DELETE CASCADE,
    UNIQUE(id_tarifa, codigo_grupo)
);



------Nivel 4: BloqueTarifa y TipoBloque (Block & Block Type)
---Para Consumo de Subsistencia (CS):

------Tipo Bloque	id	Función	Aplicación
---Límite fijo	1	param_kwh = límite fijo	Bloque 0: primeros 130/173 kWh
---Restante	99	Consumo - suma bloques anteriores	Bloque 1: excedente

-----Tabla TIPO_BLOQUE (maestra):
CREATE TABLE TIPO_BLOQUE (
    tipo_bloque_id TINYINT PRIMARY KEY,
    nombre_tipo VARCHAR(50) NOT NULL,
    funcion_calculo VARCHAR(100),
    descripcion VARCHAR(200)
);

INSERT INTO TIPO_BLOQUE VALUES
(1, 'Límite Fijo', 'param_kwh', 'Consumo de subsistencia - primeros kWh'),
(99, 'Restante', 'remaining', 'Excedente - todo el consumo restante');

------Tabla BLOQUE_TARIFA:
CREATE TABLE BLOQUE_TARIFA (
    id_bloque BIGSERIAL PRIMARY KEY,
    id_grupo BIGINT NOT NULL,
    secuencia TINYINT NOT NULL,        -- 0, 1, 2...
    tipo_bloque_id TINYINT NOT NULL,   -- 1 o 99
    limite_kwh FLOAT,                  -- Aplica para tipo_bloque_id=1
    limite_kw FLOAT,                   -- Para demandas futuras
    precio DECIMAL(12,6) NOT NULL,     -- Precio en $/kWh
    nombre_bloque VARCHAR(100),
    CONSTRAINT fk_bloque_grupo FOREIGN KEY (id_grupo) REFERENCES GRUPO_TARIFA(id_grupo) ON DELETE CASCADE,
    CONSTRAINT fk_bloque_tipo FOREIGN KEY (tipo_bloque_id) REFERENCES TIPO_BLOQUE(tipo_bloque_id)
);


-----Manejo de Franjas Horarias (TOU)
-----Tabla TIME_OF_DAY (24 horas mapeadas)
CREATE TABLE TIME_OF_DAY (
    id_time_of_day SMALLSERIAL PRIMARY KEY,
    id_tarifa BIGINT NOT NULL,
    temporada ENUM('S', 'W', 'A') NOT NULL,  -- S=verano, W=invierno, A=anual
    dias_pico TINYINT,                       -- 5=lunes-viernes, 6=incluye sábado, 7=todos
    -- 24 horas (he = hour ending)
    hora_1 ENUM('N', 'F', 'S'),   -- 1am
    hora_2 ENUM('N', 'F', 'S'),
    hora_3 ENUM('N', 'F', 'S'),
    hora_4 ENUM('N', 'F', 'S'),
    hora_5 ENUM('N', 'F', 'S'),
    hora_6 ENUM('N', 'F', 'S'),
    hora_7 ENUM('N', 'F', 'S'),
    hora_8 ENUM('N', 'F', 'S'),
    hora_9 ENUM('N', 'F', 'S'),
    hora_10 ENUM('N', 'F', 'S'),
    hora_11 ENUM('N', 'F', 'S'),
    hora_12 ENUM('N', 'F', 'S'),
    hora_13 ENUM('N', 'F', 'S'),
    hora_14 ENUM('N', 'F', 'S'),
    hora_15 ENUM('N', 'F', 'S'),
    hora_16 ENUM('N', 'F', 'S'),
    hora_17 ENUM('N', 'F', 'S'),
    hora_18 ENUM('N', 'F', 'S'),
    hora_19 ENUM('N', 'F', 'S'),
    hora_20 ENUM('N', 'F', 'S'),
    hora_21 ENUM('N', 'F', 'S'),
    hora_22 ENUM('N', 'F', 'S'),
    hora_23 ENUM('N', 'F', 'S'),
    hora_24 ENUM('N', 'F', 'S'),
    CONSTRAINT fk_timeofday_tarifa FOREIGN KEY (id_tarifa) REFERENCES Tarifa(id_tarifa) ON DELETE CASCADE
);