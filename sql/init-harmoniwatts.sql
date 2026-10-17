-- =====================================================
-- BASE DE DATOS: HarmoniWatts
-- SISTEMA INTELIGENTE DE GESTIÓN DE DEMANDA ELÉCTRICA
-- =====================================================

-- Crear la base de datos (opcional - ejecutar si no existe)
-- CREATE DATABASE harmoniwatts;
-- \c harmoniwatts;

-- =====================================================
-- HABILITAR EXTENSIONES
-- =====================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- IDENTIDAD: usuarios gestionados en Keycloak (sub del JWT)
-- =====================================================

-- =====================================================
-- TABLA: VIVIENDA
-- =====================================================
CREATE TABLE Vivienda (
    id_vivienda BIGSERIAL PRIMARY KEY,
    id_usuario VARCHAR(36) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    habitantes INTEGER,
    direccion VARCHAR(200),
    estrato INTEGER NOT NULL DEFAULT 3 CHECK (estrato >= 1 AND estrato <= 6),
    zona_climatica VARCHAR(20),
    fecha_registro TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE Vivienda IS 'Hogar del usuario (propietario = sub de Keycloak)';
COMMENT ON COLUMN Vivienda.id_usuario IS 'UUID del usuario en Keycloak (claim sub del JWT)';
COMMENT ON COLUMN Vivienda.tipo IS 'Casa, piso, apartamento, etc.';
COMMENT ON COLUMN Vivienda.direccion IS 'Ubicación / dirección del hogar';
COMMENT ON COLUMN Vivienda.estrato IS 'Estrato socioeconómico del servicio (1–6, Colombia)';
COMMENT ON COLUMN Vivienda.zona_climatica IS 'Zona climática según ubicación';

CREATE INDEX idx_vivienda_id_usuario ON Vivienda(id_usuario);

-- =====================================================
-- TABLAS: CATÁLOGOS (tipos y marcas predefinidos; incluyen «Otro»)
-- =====================================================
CREATE TABLE electrodomestico_tipo_predefinido (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nombre_es VARCHAR(100) NOT NULL,
    orden SMALLINT NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE electrodomestico_tipo_predefinido IS 'Tipos de electrodoméstico seleccionables (codigo OTRO = personalizado)';

CREATE TABLE marca_predefinida (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    orden SMALLINT NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE marca_predefinida IS 'Marcas seleccionables (nombre «Otro» = texto libre en marca_otro)';

INSERT INTO electrodomestico_tipo_predefinido (codigo, nombre_es, orden) VALUES
    ('LAVADORA', 'Lavadora', 10),
    ('LAVAVAJILLAS', 'Lavavajillas', 20),
    ('TERMO_ELECTRICO', 'Termo eléctrico / calentador', 30),
    ('VEHICULO_ELECTRICO', 'Vehículo eléctrico (EV)', 40),
    ('AIRE_ACONDICIONADO', 'Aire acondicionado', 50),
    ('NEVERA', 'Nevera / refrigerador', 60),
    ('CONGELADOR', 'Congelador', 70),
    ('HORNO', 'Horno', 80),
    ('MICROONDAS', 'Microondas', 90),
    ('SECADORA', 'Secadora', 100),
    ('VITROCERAMICA', 'Vitrocerámica / cocina eléctrica', 110),
    ('TELEVISOR', 'Televisor', 120),
    ('OTRO', 'Otro (personalizado)', 999);

INSERT INTO marca_predefinida (nombre, orden) VALUES
    ('Samsung', 10),
    ('LG', 20),
    ('Whirlpool', 30),
    ('Bosch', 40),
    ('Mabe', 50),
    ('Electrolux', 60),
    ('Haier', 70),
    ('Panasonic', 80),
    ('Daikin', 90),
    ('Mitsubishi Electric', 100),
    ('Generico / sin marca', 200),
    ('Otro', 999);

-- =====================================================
-- TABLA: ELECTRODOMESTICO
-- =====================================================
CREATE TABLE Electrodomestico (
    id_electro BIGSERIAL PRIMARY KEY,
    id_vivienda BIGINT NOT NULL,
    id_tipo_predefinido INTEGER NOT NULL REFERENCES electrodomestico_tipo_predefinido(id),
    id_marca_predefinida INTEGER REFERENCES marca_predefinida(id),
    marca_otro VARCHAR(100),
    nombre VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    consumo_kwh_dia NUMERIC(10,4) NOT NULL,
    es_desplazable BOOLEAN DEFAULT FALSE,
    uso_semanal INTEGER,
    horario_habitual TIME,
    activo BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_electro_vivienda FOREIGN KEY (id_vivienda) REFERENCES Vivienda(id_vivienda) ON DELETE CASCADE
);

COMMENT ON TABLE Electrodomestico IS 'Aparatos eléctricos del hogar';
COMMENT ON COLUMN Electrodomestico.id_tipo_predefinido IS 'FK al catálogo; codigo OTRO = nombre personalizado';
COMMENT ON COLUMN Electrodomestico.id_marca_predefinida IS 'FK marca; si es «Otro», usar marca_otro';
COMMENT ON COLUMN Electrodomestico.marca_otro IS 'Texto libre si la marca elegida es «Otro»';
COMMENT ON COLUMN Electrodomestico.tipo IS 'Redundante: mismo codigo del tipo predefinido (consultas legadas)';
COMMENT ON COLUMN Electrodomestico.consumo_kwh_dia IS 'Consumo energético promedio diario en kWh (para dashboard)';
COMMENT ON COLUMN Electrodomestico.es_desplazable IS 'Indica si el electrodoméstico puede moverse a otra hora';
COMMENT ON COLUMN Electrodomestico.uso_semanal IS 'Veces por semana que se usa (estimado)';
COMMENT ON COLUMN Electrodomestico.horario_habitual IS 'Horario preferente o típico de uso (TIME, opcional)';

CREATE INDEX idx_electro_vivienda ON Electrodomestico(id_vivienda);
CREATE INDEX idx_electro_activo ON Electrodomestico(activo);
CREATE INDEX idx_electro_tipo_pre ON Electrodomestico(id_tipo_predefinido);
CREATE INDEX idx_electro_marca_pre ON Electrodomestico(id_marca_predefinida);

-- =====================================================
-- TABLA: PREFERENCIACONFORT
-- =====================================================
CREATE TABLE PreferenciaConfort (
    id_preferencia BIGSERIAL PRIMARY KEY,
    id_vivienda BIGINT NOT NULL UNIQUE,
    balance_ahorro_confort INTEGER DEFAULT 50,
    modo_automatizacion BOOLEAN DEFAULT FALSE,
    fecha_actualizacion TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_preferencia_vivienda FOREIGN KEY (id_vivienda) REFERENCES Vivienda(id_vivienda) ON DELETE CASCADE,
    CONSTRAINT chk_balance CHECK (balance_ahorro_confort BETWEEN 1 AND 100)
);

COMMENT ON TABLE PreferenciaConfort IS 'Configuración de confort del hogar';
COMMENT ON COLUMN PreferenciaConfort.balance_ahorro_confort IS '1-100: 1=máximo confort, 100=máximo ahorro';
COMMENT ON COLUMN PreferenciaConfort.modo_automatizacion IS 'true=automático, false=solo recomendaciones';

-- =====================================================
-- TABLA: HORARIONOINTERRUPCION
-- =====================================================
CREATE TABLE HorarioNoInterrupcion (
    id_horario BIGSERIAL PRIMARY KEY,
    id_vivienda BIGINT NOT NULL,
    dia_semana INTEGER,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_horario_vivienda FOREIGN KEY (id_vivienda) REFERENCES Vivienda(id_vivienda) ON DELETE CASCADE,
    CONSTRAINT chk_dia_semana CHECK (dia_semana BETWEEN 1 AND 7)
);

COMMENT ON TABLE HorarioNoInterrupcion IS 'Bloques horarios restringidos donde no se debe interrumpir';
COMMENT ON COLUMN HorarioNoInterrupcion.dia_semana IS '1=lunes, 7=domingo';

CREATE INDEX idx_horario_vivienda ON HorarioNoInterrupcion(id_vivienda);

-- =====================================================
-- TABLA: TEMPERATURAPREFERIDA
-- =====================================================
CREATE TABLE TemperaturaPreferida (
    id_temp BIGSERIAL PRIMARY KEY,
    id_vivienda BIGINT NOT NULL,
    estacion VARCHAR(20) NOT NULL,
    temp_preferida DECIMAL(3,1),
    temp_max_desvio DECIMAL(3,1),
    activo BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_temp_vivienda FOREIGN KEY (id_vivienda) REFERENCES Vivienda(id_vivienda) ON DELETE CASCADE
);

COMMENT ON TABLE TemperaturaPreferida IS 'Preferencias de temperatura por estación';
COMMENT ON COLUMN TemperaturaPreferida.estacion IS 'Verano, invierno, primavera, otoño';
COMMENT ON COLUMN TemperaturaPreferida.temp_max_desvio IS 'Máxima desviación aceptable en °C';

CREATE INDEX idx_temp_vivienda ON TemperaturaPreferida(id_vivienda);

-- =====================================================
-- TABLA: DISPOSITIVOIOT
-- =====================================================
CREATE TABLE DispositivoIoT (
    id_dispositivo BIGSERIAL PRIMARY KEY,
    id_vivienda BIGINT NOT NULL,
    id_electro BIGINT,
    nombre VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    marca VARCHAR(50),
    modelo VARCHAR(50),
    identificador_unico VARCHAR(100) UNIQUE,
    protocolo_conexion VARCHAR(30),
    configuracion_json JSONB,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_dispositivo_vivienda FOREIGN KEY (id_vivienda) REFERENCES Vivienda(id_vivienda) ON DELETE CASCADE,
    CONSTRAINT fk_dispositivo_electro FOREIGN KEY (id_electro) REFERENCES Electrodomestico(id_electro) ON DELETE SET NULL
);

COMMENT ON TABLE DispositivoIoT IS 'Dispositivos inteligentes conectados al sistema';
COMMENT ON COLUMN DispositivoIoT.protocolo_conexion IS 'wifi, zigbee, mqtt, etc.';
COMMENT ON COLUMN DispositivoIoT.configuracion_json IS 'Configuración específica del dispositivo';

CREATE INDEX idx_dispositivo_vivienda ON DispositivoIoT(id_vivienda);
CREATE INDEX idx_dispositivo_electro ON DispositivoIoT(id_electro);
CREATE INDEX idx_dispositivo_identificador ON DispositivoIoT(identificador_unico);

-- =====================================================
-- TABLA: COMERCIALIZADORA
-- =====================================================
CREATE TABLE Comercializadora (
    id_comercializadora SMALLSERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    nit VARCHAR(20) UNIQUE,
    sitio_web VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE Comercializadora IS 'Empresa que provee el servicio eléctrico';

-- =====================================================
-- TABLA: TARIFA
-- =====================================================
CREATE TABLE Tarifa (
    id_tarifa BIGSERIAL PRIMARY KEY,
    id_comercializadora SMALLINT NOT NULL,
    mercado VARCHAR(50) NOT NULL,
    nivel_tension VARCHAR(20) NOT NULL,
    tipo_tarifa VARCHAR(5),
    codigo_tarifa VARCHAR(50) UNIQUE,
    nombre_tarifa VARCHAR(200),
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    resolucion_regulatoria VARCHAR(100),
    activa BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_tarifa_comercializadora FOREIGN KEY (id_comercializadora) REFERENCES Comercializadora(id_comercializadora),
    CONSTRAINT chk_fechas CHECK (fecha_fin >= fecha_inicio)
);

COMMENT ON TABLE Tarifa IS 'Plan tarifario del usuario - versión simplificada';
COMMENT ON COLUMN Tarifa.mercado IS 'CALI, VALLE, NARIÑO, ANTIOQUIA UNIF, BOGOTA';
COMMENT ON COLUMN Tarifa.nivel_tension IS 'Nivel 3, Nivel 2, Nivel 1.1, N 1.2-1.3, etc.';
COMMENT ON COLUMN Tarifa.tipo_tarifa IS 'A, B, C, D - puede ser null';
COMMENT ON COLUMN Tarifa.codigo_tarifa IS 'Ej: CALI-N1.1-A-202410';
COMMENT ON COLUMN Tarifa.resolucion_regulatoria IS 'CREG 119/2007, CREG 101/2023, etc.';

CREATE INDEX idx_tarifa_comercializadora ON Tarifa(id_comercializadora);
CREATE INDEX idx_tarifa_fechas ON Tarifa(fecha_inicio, fecha_fin);
CREATE INDEX idx_tarifa_activa ON Tarifa(activa);

-- =====================================================
-- TABLA: FRANJATARIFA
-- =====================================================
CREATE TABLE FranjaTarifa (
    id_franja BIGSERIAL PRIMARY KEY,
    id_tarifa BIGINT NOT NULL,
    codigo_franja VARCHAR(5) NOT NULL,
    valor DECIMAL(12,6) NOT NULL,
    es_precio_directo BOOLEAN DEFAULT TRUE,
    definicion_horas VARCHAR(100),
    orden SMALLINT,
    CONSTRAINT fk_franja_tarifa FOREIGN KEY (id_tarifa) REFERENCES Tarifa(id_tarifa) ON DELETE CASCADE,
    CONSTRAINT chk_codigo_franja CHECK (codigo_franja IN ('F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8')),
    CONSTRAINT chk_orden CHECK (orden BETWEEN 1 AND 8),
    UNIQUE(id_tarifa, codigo_franja)
);

COMMENT ON TABLE FranjaTarifa IS 'Valores por franja horaria (F1 a F8)';
COMMENT ON COLUMN FranjaTarifa.codigo_franja IS 'F1, F2, F3, F4, F5, F6, F7, F8';
COMMENT ON COLUMN FranjaTarifa.es_precio_directo IS 'false si es un índice que requiere cálculo';
COMMENT ON COLUMN FranjaTarifa.definicion_horas IS 'Ej: 1-4,24 o 5-9,13-18 o N.A.';
COMMENT ON COLUMN FranjaTarifa.orden IS '1 para F1, 2 para F2, etc.';

CREATE INDEX idx_franja_tarifa ON FranjaTarifa(id_tarifa);
CREATE INDEX idx_franja_orden ON FranjaTarifa(orden);

-- =====================================================
-- TABLA: COMPONENTETARIFA
-- =====================================================
CREATE TABLE ComponenteTarifa (
    id_componente BIGSERIAL PRIMARY KEY,
    id_tarifa BIGINT NOT NULL,
    codigo_componente VARCHAR(20) NOT NULL,
    nombre_componente VARCHAR(100),
    valor DECIMAL(12,6) NOT NULL,
    unidad VARCHAR(20) DEFAULT '$/kWh',
    CONSTRAINT fk_componente_tarifa FOREIGN KEY (id_tarifa) REFERENCES Tarifa(id_tarifa) ON DELETE CASCADE,
    UNIQUE(id_tarifa, codigo_componente)
);

COMMENT ON TABLE ComponenteTarifa IS 'Componentes adicionales de la tarifa (CU_BASE, CU_APLICADO, CS, etc.)';
COMMENT ON COLUMN ComponenteTarifa.codigo_componente IS 'CU_BASE, CU_APLICADO, CS, etc.';

CREATE INDEX idx_componente_tarifa ON ComponenteTarifa(id_tarifa);

-- =====================================================
-- TABLA: TARIFAUSUARIO
-- =====================================================
CREATE TABLE TarifaUsuario (
    id_tarifa_usuario BIGSERIAL PRIMARY KEY,
    id_usuario VARCHAR(36) NOT NULL,
    id_tarifa BIGINT NOT NULL,
    fecha_asignacion DATE NOT NULL,
    fecha_desasignacion DATE,
    activa BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_tarifausuario_tarifa FOREIGN KEY (id_tarifa) REFERENCES Tarifa(id_tarifa),
    CONSTRAINT chk_fechas_asignacion CHECK (fecha_desasignacion IS NULL OR fecha_desasignacion >= fecha_asignacion)
);

COMMENT ON TABLE TarifaUsuario IS 'Asignación de tarifas a usuarios (histórico; usuario = Keycloak sub)';
COMMENT ON COLUMN TarifaUsuario.fecha_desasignacion IS 'null si sigue activa';

CREATE INDEX idx_tarifausuario_id_usuario ON TarifaUsuario(id_usuario);
CREATE INDEX idx_tarifausuario_tarifa ON TarifaUsuario(id_tarifa);
CREATE INDEX idx_tarifausuario_activa ON TarifaUsuario(activa);

-- =====================================================
-- TABLA: RECOMENDACION
-- =====================================================
CREATE TABLE Recomendacion (
    id_recomendacion BIGSERIAL PRIMARY KEY,
    id_vivienda BIGINT NOT NULL,
    id_electro BIGINT NOT NULL,
    fecha_generacion TIMESTAMP DEFAULT NOW(),
    fecha_propuesta DATE NOT NULL,
    hora_inicio_sugerida TIME NOT NULL,
    hora_fin_sugerida TIME NOT NULL,
    ahorro_estimado_eur DECIMAL(6,2),
    impacto_confort INTEGER,
    prioridad INTEGER,
    estado VARCHAR(20) DEFAULT 'pendiente',
    CONSTRAINT fk_recomendacion_vivienda FOREIGN KEY (id_vivienda) REFERENCES Vivienda(id_vivienda) ON DELETE CASCADE,
    CONSTRAINT fk_recomendacion_electro FOREIGN KEY (id_electro) REFERENCES Electrodomestico(id_electro),
    CONSTRAINT chk_impacto_confort CHECK (impacto_confort BETWEEN 1 AND 10),
    CONSTRAINT chk_prioridad CHECK (prioridad BETWEEN 1 AND 5),
    CONSTRAINT chk_estado CHECK (estado IN ('pendiente', 'aplicada', 'descartada'))
);

COMMENT ON TABLE Recomendacion IS 'Sugerencia de optimización para el usuario';
COMMENT ON COLUMN Recomendacion.impacto_confort IS '1-10: 1=mínimo impacto, 10=máximo';
COMMENT ON COLUMN Recomendacion.prioridad IS '1-5: 1=máxima prioridad';
COMMENT ON COLUMN Recomendacion.estado IS 'pendiente, aplicada, descartada';

CREATE INDEX idx_recomendacion_vivienda ON Recomendacion(id_vivienda);
CREATE INDEX idx_recomendacion_electro ON Recomendacion(id_electro);
CREATE INDEX idx_recomendacion_fecha ON Recomendacion(fecha_propuesta);
CREATE INDEX idx_recomendacion_estado ON Recomendacion(estado);

-- =====================================================
-- TABLA: DECISIONRECOMENDACION
-- =====================================================
CREATE TABLE DecisionRecomendacion (
    id_decision BIGSERIAL PRIMARY KEY,
    id_recomendacion BIGINT NOT NULL UNIQUE,
    decision VARCHAR(20) NOT NULL,
    fecha_decision TIMESTAMP DEFAULT NOW(),
    hora_ajustada TIME,
    feedback_usuario TEXT,
    calificacion INTEGER,
    CONSTRAINT fk_decision_recomendacion FOREIGN KEY (id_recomendacion) REFERENCES Recomendacion(id_recomendacion) ON DELETE CASCADE,
    CONSTRAINT chk_decision CHECK (decision IN ('aceptar', 'rechazar', 'ajustar')),
    CONSTRAINT chk_calificacion CHECK (calificacion BETWEEN 1 AND 5)
);

COMMENT ON TABLE DecisionRecomendacion IS 'Acción del usuario sobre una recomendación';
COMMENT ON COLUMN DecisionRecomendacion.decision IS 'aceptar, rechazar, ajustar';
COMMENT ON COLUMN DecisionRecomendacion.hora_ajustada IS 'si se ajustó, nueva hora';
COMMENT ON COLUMN DecisionRecomendacion.calificacion IS '1-5';

CREATE INDEX idx_decision_recomendacion ON DecisionRecomendacion(id_recomendacion);

-- =====================================================
-- TABLA: CONEXIONEXTERNA
-- =====================================================
CREATE TABLE ConexionExterna (
    id_conexion BIGSERIAL PRIMARY KEY,
    id_usuario VARCHAR(36) NOT NULL,
    tipo VARCHAR(30) NOT NULL,
    nombre_servicio VARCHAR(100),
    estado VARCHAR(20),
    fecha_conexion TIMESTAMP,
    ultima_sincronizacion TIMESTAMP,
    configuracion_json JSONB,
    activo BOOLEAN DEFAULT TRUE,
    CONSTRAINT chk_tipo CHECK (tipo IN ('comercializadora', 'contador')),
    CONSTRAINT chk_estado_conexion CHECK (estado IN ('activa', 'error', 'pendiente'))
);

COMMENT ON TABLE ConexionExterna IS 'Integración con APIs externas (comercializadoras, contadores)';
COMMENT ON COLUMN ConexionExterna.id_usuario IS 'UUID del usuario en Keycloak';
COMMENT ON COLUMN ConexionExterna.tipo IS 'comercializadora, contador';
COMMENT ON COLUMN ConexionExterna.estado IS 'activa, error, pendiente';
COMMENT ON COLUMN ConexionExterna.configuracion_json IS 'Configuración específica de la API';

CREATE INDEX idx_conexion_id_usuario ON ConexionExterna(id_usuario);
CREATE INDEX idx_conexion_tipo ON ConexionExterna(tipo);

-- =====================================================
-- TABLA: HISTORIALSINCRONIZACION
-- =====================================================
CREATE TABLE HistorialSincronizacion (
    id_sincronizacion BIGSERIAL PRIMARY KEY,
    id_conexion BIGINT NOT NULL,
    fecha_sincronizacion TIMESTAMP DEFAULT NOW(),
    estado VARCHAR(20) NOT NULL,
    registros_obtenidos INTEGER,
    mensaje_error TEXT,
    duracion_seg INTEGER,
    CONSTRAINT fk_historial_conexion FOREIGN KEY (id_conexion) REFERENCES ConexionExterna(id_conexion) ON DELETE CASCADE,
    CONSTRAINT chk_estado_sincronizacion CHECK (estado IN ('exito', 'error', 'parcial'))
);

COMMENT ON TABLE HistorialSincronizacion IS 'Log de sincronizaciones con servicios externos';
COMMENT ON COLUMN HistorialSincronizacion.estado IS 'exito, error, parcial';

CREATE INDEX idx_historial_conexion ON HistorialSincronizacion(id_conexion);
CREATE INDEX idx_historial_fecha ON HistorialSincronizacion(fecha_sincronizacion);

-- =====================================================
-- FUNCIÓN PARA ACTUALIZAR FECHA DE ACTUALIZACIÓN DE PREFERENCIAS
-- =====================================================
CREATE OR REPLACE FUNCTION actualizar_fecha_preferencias()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TRIGGER: Actualizar fecha cuando se modifican preferencias de confort
-- =====================================================
CREATE TRIGGER trigger_actualizar_fecha_preferencias
    BEFORE UPDATE ON PreferenciaConfort
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fecha_preferencias();

-- =====================================================
-- FUNCIÓN PARA VALIDAR QUE LA TARIFA ASIGNADA AL USUARIO ESTÉ VIGENTE
-- =====================================================
CREATE OR REPLACE FUNCTION validar_tarifa_vigente()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM Tarifa t
        WHERE t.id_tarifa = NEW.id_tarifa
          AND t.fecha_inicio <= NEW.fecha_asignacion
          AND (t.fecha_fin >= NEW.fecha_asignacion OR t.fecha_fin IS NULL)
          AND t.activa = TRUE
    ) THEN
        RAISE EXCEPTION 'La tarifa no está vigente en la fecha de asignación';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TRIGGER: Validar vigencia de tarifa al asignar a usuario
-- =====================================================
CREATE TRIGGER trigger_validar_tarifa_vigente
    BEFORE INSERT OR UPDATE ON TarifaUsuario
    FOR EACH ROW
    EXECUTE FUNCTION validar_tarifa_vigente();

-- =====================================================
-- VISTA: Tarifas activas con sus franjas
-- =====================================================
CREATE OR REPLACE VIEW v_tarifas_activas AS
SELECT 
    t.id_tarifa,
    t.id_comercializadora,
    c.nombre AS comercializadora,
    t.mercado,
    t.nivel_tension,
    t.tipo_tarifa,
    t.codigo_tarifa,
    t.nombre_tarifa,
    t.fecha_inicio,
    t.fecha_fin,
    t.resolucion_regulatoria,
    ft.codigo_franja,
    ft.valor,
    ft.definicion_horas,
    ft.orden
FROM Tarifa t
INNER JOIN Comercializadora c ON t.id_comercializadora = c.id_comercializadora
INNER JOIN FranjaTarifa ft ON t.id_tarifa = ft.id_tarifa
WHERE t.activa = TRUE
  AND t.fecha_inicio <= CURRENT_DATE
  AND (t.fecha_fin >= CURRENT_DATE OR t.fecha_fin IS NULL)
ORDER BY t.mercado, t.nivel_tension, ft.orden;

COMMENT ON VIEW v_tarifas_activas IS 'Vista de tarifas activas con sus franjas horarias';

-- =====================================================
-- VISTA: Usuarios con su tarifa activa actual
-- =====================================================
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
FROM Vivienda v
INNER JOIN TarifaUsuario tu ON v.id_usuario = tu.id_usuario AND tu.activa = TRUE
INNER JOIN Tarifa t ON tu.id_tarifa = t.id_tarifa;

COMMENT ON VIEW v_usuarios_tarifa_activa IS 'Viviendas con tarifa activa asignada al mismo usuario Keycloak';

-- =====================================================
-- VISTA: Recomendaciones pendientes por vivienda
-- =====================================================
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
FROM Recomendacion r
INNER JOIN Electrodomestico e ON r.id_electro = e.id_electro
INNER JOIN Vivienda v ON r.id_vivienda = v.id_vivienda
WHERE r.estado = 'pendiente'
  AND r.fecha_propuesta >= CURRENT_DATE
ORDER BY r.prioridad ASC, r.ahorro_estimado_eur DESC;

COMMENT ON VIEW v_recomendaciones_pendientes IS 'Recomendaciones pendientes por vivienda';

-- =====================================================
-- ÍNDICES ADICIONALES PARA RENDIMIENTO
-- =====================================================

-- Índices para búsquedas por fecha en tarifas
CREATE INDEX idx_tarifa_fechas_vigencia ON Tarifa(fecha_inicio, fecha_fin);

-- Índice compuesto para tarifas activas por mercado y nivel
CREATE INDEX idx_tarifa_mercado_nivel ON Tarifa(mercado, nivel_tension, activa);

-- Índice para recomendaciones por fecha y prioridad
CREATE INDEX idx_recomendacion_fecha_prioridad ON Recomendacion(fecha_propuesta, prioridad) WHERE estado = 'pendiente';

-- Índice para historial de sincronización por fecha
CREATE INDEX idx_historial_fecha_estado ON HistorialSincronizacion(fecha_sincronizacion, estado);

-- =====================================================
-- CONFIGURACIÓN DE ROW LEVEL SECURITY (RLS)
-- =====================================================

-- Habilitar RLS en tablas con datos sensibles
ALTER TABLE Vivienda ENABLE ROW LEVEL SECURITY;
ALTER TABLE Electrodomestico ENABLE ROW LEVEL SECURITY;
ALTER TABLE PreferenciaConfort ENABLE ROW LEVEL SECURITY;
ALTER TABLE HorarioNoInterrupcion ENABLE ROW LEVEL SECURITY;
ALTER TABLE TemperaturaPreferida ENABLE ROW LEVEL SECURITY;
ALTER TABLE DispositivoIoT ENABLE ROW LEVEL SECURITY;
-- ConsumoRegistro: habilitar RLS cuando exista la tabla (no definida en este script)
-- ALTER TABLE ConsumoRegistro ENABLE ROW LEVEL SECURITY;
ALTER TABLE Recomendacion ENABLE ROW LEVEL SECURITY;
ALTER TABLE DecisionRecomendacion ENABLE ROW LEVEL SECURITY;

-- Política: Usuario solo ve sus propios datos
-- (Descomentar cuando se implemente autenticación)
/*
CREATE POLICY vivienda_user_access ON Vivienda
    USING (id_usuario = current_setting('app.current_user_id', true));

CREATE POLICY electrodomestico_user_access ON Electrodomestico
    USING (id_vivienda IN (SELECT id_vivienda FROM Vivienda WHERE id_usuario = current_setting('app.current_user_id', true)));
*/

-- =====================================================
-- FIN DEL SCRIPT
-- =====================================================
