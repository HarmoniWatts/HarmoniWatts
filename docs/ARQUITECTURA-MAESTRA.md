# 🏗️ Arquitectura Maestra - HarmoniWatts

**Documento unificado de arquitectura con diagramas C4, diagramas de secuencia, diccionario de datos y especificaciones de microservicios.**

---

## 📑 Índice Rápido

1. [Visión General](#visión-general)
2. [Diagramas C4 (Compilables)](#diagramas-c4-compilables)
3. [Microservicios Implementados](#microservicios-implementados)
4. [Diagramas de Secuencia](#diagramas-de-secuencia)
5. [Diccionario de Datos](#diccionario-de-datos)
6. [Infraestructura y Despliegue](#infraestructura-y-despliegue)
7. [Referencias](#referencias)

---

## Visión General

**HarmoniWatts** es un HEMS (Home Energy Management System) que optimiza el consumo eléctrico residencial mediante:

- **Ingesta de datos:** Lectura en tiempo real de medidores inteligentes IoT
- **Análisis:** Agregación, clustering de perfiles de usuario, detección de anomalías
- **Predicción:** Modelo IA que anticipa consumo mensual y oportunidades de ahorro
- **Recomendaciones:** Acciones personalizadas para reducir costos en franjas de mayor precio
- **Automatización:** Desplazamiento de cargas flexibles (lavadora, termo, EV) a franjas baratas

### Stack Técnico Implementado

```
Frontend:              Angular 21+ (SPA responsivo)
Identidad:            Keycloak (OIDC/OAuth2, Google SSO)
Registro de usuarios: harmoni-register (Node.js)
Backend:              Python (FastAPI), Node.js (Express), Java (Spring Boot)
Bases de datos:       PostgreSQL (negocio), MongoDB (series de tiempo)
Cache/Async:          Redis, Celery
Orquestación:         Docker Compose (dev)
```

---

## Diagramas C4 (Compilables)

### 📍 Ubicación

- **Archivo DSL:** [`docs/architecture/workspace.dsl`](architecture/workspace.dsl)
- **Formato:** Structurizr DSL (compilable en línea, Docker o CLI)
- **Diagra mas incluidos:**
  - C4 Level 1: System Context
  - C4 Level 2: Container Architecture
  - C4 Level 3: Component diagrams (5 microservicios)
  - Estilos y colores aplicados

### 🔧 Cómo Compilar

#### Opción 1: Online (Recomendado - Sin instalación)
```
1. Ir a https://structurizr.com/dsl
2. Copiar contenido de docs/architecture/workspace.dsl
3. Pegar en el editor (lado izquierdo)
4. Los diagramas se renderizan automáticamente (lado derecho)
5. Exportar como SVG/PNG desde el menú
```

#### Opción 2: Docker Local
```bash
# Requiere Docker
docker run -it --rm -p 8080:8080 -v ./docs/architecture:/workspace structurizr/lite:latest

# Luego abrir http://localhost:8080 en el navegador
# Navegar a workspace.dsl para ver los diagramas interactivos
```

#### Opción 3: Structurizr CLI
```bash
# Descargar desde https://github.com/structurizr/cli/releases

# Exportar a PlantUML
structurizr export -workspace workspace.dsl -format plantuml

# Exportar a Mermaid
structurizr export -workspace workspace.dsl -format mermaid
```

### 📊 Diagramas Disponibles en el DSL

#### Level 1: System Context
**Actores externos:**
- 👤 Usuario Residencial (propietario/arrendatario)
- ⚡ Empresa Energética (proveedor de tarifas)
- 📱 Dispositivo IoT (medidor inteligente)

**Sistema HarmoniWatts** como caja negra.

#### Level 2: Container Architecture
**7 contenedores principales:**
1. **Frontend Web** (Angular SPA)
2. **Consumption Service** (Python/FastAPI) - Ingesta IoT
3. **Insights Service** (Node.js/Express) - Dashboards
4. **Vivienda API** (Java/Spring Boot) - Gestión residencial
5. **Electrodomésticos API** (Java/Spring Boot) - Predicciones
6. **Prediction Service** (Python/FastAPI + ML) - IA [Planeado]
7. **Tariff Service** (Java/Spring Boot) - Gestión tarifas [Mockado]

**Infraestructura:**
- MongoDB (consumo de series de tiempo)
- PostgreSQL (datos transaccionales)
- Redis (cache + task queue)
- Keycloak (SSO)

#### Level 3: Component Diagrams
Desglose interno de cada microservicio:

**Consumption Service:**
- API Routes → Data Service → MongoDB Driver
- Celery Tasks → Redis queue

**Insights Service:**
- Dashboard Routes → Insights Service → Clients (Consumption, Prediction)

**Vivienda API:**
- Houses Controller → Houses Service → JPA Repository → PostgreSQL

**Electrodomésticos API:**
- Appliances Controller → Appliances Service → JPA Repository → PostgreSQL

**Prediction Service:**
- Prediction Routes → ML Model → Data Aggregator → Historical Data

---

## Microservicios Implementados

### 1. Consumption Service (Python/FastAPI)

**Ubicación:** `backend/consumption-service/`

**Responsabilidad:** Ingesta, almacenamiento y consulta de datos de consumo energético en tiempo real.

**Tecnologías:**
- FastAPI (framework async)
- Motor (MongoDB driver async)
- Celery (task queue)
- Pydantic (validación)
- structlog (logging estructurado)

**Endpoints:**
```
GET  /health                              → Health check
GET  /ready                               → Readiness (verifica BD)
GET  /api/v1/consumption/current/{id}    → Consumo actual en tiempo real
GET  /api/v1/consumption/daily-total/{id} → Total del día
POST /ingest                              → Recibir lecturas IoT (Celery async)
```

**Base de datos:**
- MongoDB collection: `consumption_readings`
- Índices: `{household_id: 1, timestamp: -1}`
- TTL: 90 días (políticas de retención)

**Dependencias externas:**
- Keycloak (validación JWT)
- Redis (Celery queue)
- MongoDB (persistencia)

---

### 2. Insights Service (Node.js/Express)

**Ubicación:** `backend/insights-service/`

**Responsabilidad:** Agregación, análisis y visualización de datos de consumo. Genera dashboards, gráficos y recomendaciones.

**Tecnologías:**
- Express.js (framework HTTP)
- Axios (cliente HTTP)
- Swagger/OpenAPI (documentación)
- moment-timezone (fechas/zonas)

**Endpoints:**
```
GET /health                           → Health check
GET /api/v1/dashboard/summary         → Resumen KPIs (consumo, predicción, ahorros)
GET /api/v1/dashboard/consumption-chart → Gráficos históricos
GET /api/v1/dashboard/recommendations → Recomendaciones IA
GET /api/v1/dashboard/appliances/top  → Top 5 electrodomésticos
POST /api/v1/recommendations/{id}/apply   → Aplicar recomendación
POST /api/v1/recommendations/{id}/dismiss → Descartar recomendación
```

**Dependencias externas:**
- Consumption Service (port 8000)
- Prediction Service (port 8003)
- Tariff Service (port 8004)

**Flujo de datos:**
1. Frontend solicita `/api/v1/dashboard/summary`
2. Insights consulta Consumption Service por datos actuales
3. Insights consulta Prediction Service por predicción mensual
4. Insights consulta Tariff Service por tarifas actuales
5. Agrega datos y retorna JSON con dashboard

---

### 3. Vivienda API (Java/Spring Boot)

**Ubicación:** `harmoniwatts-vivienda-api/`

**Responsabilidad:** Gestión de viviendas, usuarios y configuración residencial.

**Tecnologías:**
- Spring Boot 3+
- Spring Data JPA (Hibernate)
- Spring Security (OAuth2 resource server)
- PostgreSQL

**Endpoints:**
```
GET    /api/v1/households/{id}          → Obtener vivienda
POST   /api/v1/households               → Crear vivienda
PUT    /api/v1/households/{id}          → Actualizar vivienda
DELETE /api/v1/households/{id}          → Eliminar vivienda
GET    /api/v1/users/{id}/households    → Listar viviendas del usuario
```

**Base de datos:**
- PostgreSQL tables: `households`, `users`
- Relaciones: 1 user → N households

**Seguridad:**
- Keycloak integration (JWT validation)
- RLS (Row Level Security) en BD

---

### 4. Electrodomésticos API (Java/Spring Boot)

**Ubicación:** `harmoniwatts-electrodomesticos-api/`

**Responsabilidad:** Registro, clasificación y predicción de consumo por electrodoméstico individual.

**Tecnologías:**
- Spring Boot
- Spring Data JPA
- Feign Client (llamadas a Prediction Service)
- PostgreSQL

**Endpoints:**
```
GET    /api/v1/appliances/{household_id}       → Listar electrodomésticos
POST   /api/v1/appliances                      → Registrar nuevo
GET    /api/v1/appliances/{id}/consumption     → Consumo estimado
GET    /api/v1/appliances/top-consumers        → Top 5 por consumo
POST   /api/v1/appliances/{id}/predict-replacement → Beneficio de reemplazo
```

**Base de datos:**
- PostgreSQL tables: `appliances`, `appliance_predictions`
- Relaciones: household → N appliances

**Predicción:**
1. Usuario registra AC (5000W)
2. API envía datos a Prediction Service
3. Prediction Service retorna: "150kWh/mes si se usa 8h/día" (confidence: 0.92)
4. API almacena predicción y retorna al frontend

---

### ⏳ Prediction Service (Planeado - Python/FastAPI + ML)

**Ubicación:** `backend/prediction-service/` (a crear)

**Responsabilidad:** Modelo de Machine Learning que predice consumo mensual basado en:
- Histórico de consumo del hogar (últimos 12 meses)
- Característica de electrodomésticos
- Patrones de uso
- Factores climáticos

**Stack propuesto:**
- FastAPI (API REST)
- TensorFlow / scikit-learn (ML models)
- Pandas / NumPy (data processing)
- PyTorch (si se elige deep learning)

**Endpoints (a definir):**
```
POST /predict/monthly {appliance_data, historical_consumption}
     → {prediction: 250kWh, confidence: 0.92}

POST /predict/appliance {device_type, power_rating}
     → {estimated_monthly_kwh: 150}

GET /model/info
     → {model_version, accuracy, last_training}
```

**Especificación completa:** `docs/architecture/DATA_DICTIONARY.md`

---

### 🔄 Tariff Service (Mockado actualmente)

**Estado:** Implementación básica (stubs HTTP)

**Responsabilidad:** Gestión de tarifas eléctricas dinámicas por franja horaria.

**Endpoints (mockados):**
```
GET /api/v1/tariffs                    → Tarifas actuales
GET /api/v1/tariffs/{date}             → Tarifas para fecha específica
POST /api/v1/tariffs/update            → Actualizar tarifas
```

**Futuro:** Integración real con CREG (Comisión de Regulación de Energía) o comercializador.

---

## Diagramas de Secuencia

**Ubicación:** [`docs/architecture/sequence-diagrams.mmd`](architecture/sequence-diagrams.mmd)

**Formato:** Mermaid (compilable en GitHub, VS Code, online)

### Flujos Documentados

#### 1. Ingesta de Datos en Tiempo Real
```
IoT Device → Consumption API → Celery Task → MongoDB
Procesamiento asincrónico, 202 Accepted inmediato
```

#### 2. Visualización de Dashboards
```
Frontend → Insights API → Consumption Service
                       → Prediction Service
                       → Tariff Service
Agregación de datos, retorna JSON con dashboard
```

#### 3. Predicción de Electrodomésticos
```
Frontend → Appliances API → Prediction Service
                          → Consumption Service (histórico)
Predicción mensual, con confianza
```

#### 4. Autenticación con Keycloak
```
Frontend → Keycloak (OIDC) → Google OAuth (opcional)
Retorna access_token + refresh_token
```

#### 5. Recomendaciones de Ahorro (Futuro)
```
Insights → Consumption Service (patrones)
         → Appliances API (top consumers)
         → Prediction Service (análisis IA)
Genera recomendaciones personalizadas
```

#### 6. Integración con Proveedor Energía (Futuro)
```
Empresa Energética → Tariff Service (actualización)
                  → Insights (notificación cambio)
                  → Frontend (alerta usuario)
Sincronización en tiempo real
```

---

## Diccionario de Datos

**Ubicación:** [`docs/architecture/DATA_DICTIONARY.md`](architecture/DATA_DICTIONARY.md)

**Contenido:**

### MongoDB (Consumption Service)

**Colección: consumption_readings**
```json
{
  "_id": ObjectId,
  "household_id": "h_123",
  "timestamp": ISODate("2026-09-18T14:30:00Z"),
  "consumption_kwh": 5.2,
  "device_id": "meter_001",
  "metadata": {
    "temperature": 25.5,
    "humidity": 60,
    "grid_frequency": 60.0
  },
  "created_at": ISODate("2026-09-18T14:30:00Z")
}
```

**Índices:**
- `{household_id: 1, timestamp: -1}` (query principal)
- `{device_id: 1}` (filtros por dispositivo)
- TTL: 90 días

**Volumen:** ~14,400 documentos/día (con 1,000 hogares)

### PostgreSQL (Vivienda + Electrodomésticos API)

**Tabla: households**
```sql
CREATE TABLE households (
  household_id SERIAL PRIMARY KEY,
  user_id INT NOT NULL FK(users),
  address VARCHAR(255),
  city VARCHAR(100),
  square_meters FLOAT,
  tariff_type VARCHAR(50),
  created_at TIMESTAMP
);
```

**Tabla: appliances**
```sql
CREATE TABLE appliances (
  appliance_id SERIAL PRIMARY KEY,
  household_id INT NOT NULL FK(households),
  name VARCHAR(255),
  type VARCHAR(100),
  power_rating_w FLOAT,
  estimated_monthly_kwh FLOAT,
  created_at TIMESTAMP
);
```

**Tabla: appliance_predictions**
```sql
CREATE TABLE appliance_predictions (
  prediction_id SERIAL PRIMARY KEY,
  appliance_id INT FK(appliances),
  predicted_monthly_kwh FLOAT,
  confidence_score FLOAT (0-1),
  created_at TIMESTAMP
);
```

---

## Infraestructura y Despliegue

### Desarrollo Local (Docker Compose)

```yaml
# docker/docker-compose.yml
services:
  keycloak:
    image: keycloak/keycloak:latest
    ports: ["8080:8080"]
    
  postgres_keycloak:
    image: postgres:14
    ports: ["5432:5432"]
    
  mongodb:
    image: mongo:6
    ports: ["27017:27017"]
    
  redis:
    image: redis:7
    ports: ["6379:6379"]
    
  frontend:
    build: ./frontend
    ports: ["4200:4200"]
    
  consumption_api:
    build: ./backend/consumption-service
    ports: ["8000:8000"]
    
  insights_api:
    build: ./backend/insights-service
    ports: ["3000:3000"]
    
  vivienda_api:
    build: ./harmoniwatts-vivienda-api
    ports: ["8001:8080"]
    
  appliances_api:
    build: ./harmoniwatts-electrodomesticos-api
    ports: ["8002:8080"]
```

### Producción (Planeado)

**Tecnología:** Kubernetes / Azure Kubernetes Service (AKS)

**Componentes:**
- Ingress controller (nginx)
- Service mesh (optional: Istio)
- Persistent volumes (PostgreSQL, MongoDB)
- Horizontal Pod Autoscaler (HPA)
- Monitoring (Prometheus + Grafana)

**Especificación:** `docs/HarmoniWatts_ReleasePlan.md`

---

## Referencias

### Documentos Relacionados

| Documento | Tema |
|-----------|------|
| [`ARQUITECTURA-HarmoniWatts.md`](ARQUITECTURA-HarmoniWatts.md) | Diagramas Mermaid: contexto, contenedores, despliegue |
| [`HarmoniWatts_BPM.md`](HarmoniWatts_BPM.md) | Procesos de negocio (BPMN 2.0) |
| [`HarmoniWatts_ReleasePlan.md`](HarmoniWatts_ReleasePlan.md) | Plan de releases y entregas |
| [`AUTH-FLOW.md`](AUTH-FLOW.md) | Flujo de autenticación OIDC/OAuth2 |
| [`KEYCLOAK-REALM-CLIENT.md`](KEYCLOAK-REALM-CLIENT.md) | Configuración de realm y clientes |
| [`DOCKER-KEYCLOAK.md`](DOCKER-KEYCLOAK.md) | Despliegue de Keycloak |
| [`REGISTER-API.md`](REGISTER-API.md) | API de registro de usuarios |

### Recursos Externos

**Diagramas C4:**
- 📖 [C4 Model](https://c4model.com/)
- 📖 [Structurizr Documentation](https://structurizr.com/help/dsl)
- 🔧 [Structurizr CLI](https://github.com/structurizr/cli)

**Mermaid Diagrams:**
- 📖 [Mermaid Docs](https://mermaid.js.org/)
- 🔧 [Mermaid Live Editor](https://mermaid.live/)

**Confluencia:**
- 🔗 [HarmoniWatts - Documentación Técnica](https://giia.atlassian.net/wiki/spaces/HarmoniWatts)

---

**Última actualización:** 18 de Septiembre de 2026  
**Versión:** 2.0  
**Estado:** Documentación Completa y Unificada  
**Autores:** Christian Camilo Rosero Rodríguez / Carlos David Rojas Lozano + Claude AI
