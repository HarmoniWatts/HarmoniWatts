# 📊 Diagramas C4 - HarmoniWatts

**Diagramas de arquitectura compilados desde Structurizr DSL como imágenes PNG + diagrama de secuencia.**

---

## 📋 Índice de Diagramas

| Diagrama | Ubicación | Descripción |
|----------|-----------|-------------|
| **System Context** | `images/c4-context.png` | Nivel 1: Usuario, Sistema, Actores externos |
| **Container Architecture** | `images/c4-container.png` | Nivel 2: 10 contenedores principales |
| **Consumption Service Components** | `images/c4-component-consumption.png` | Level 3: Detalles internos |
| **Insights Service Components** | `images/c4-component-insights.png` | Level 3: Detalles internos |
| **Vivienda API Components** | `images/c4-component-vivienda.png` | Level 3: Detalles internos |
| **Electrodomésticos API Components** | `images/c4-component-appliances.png` | Level 3: Detalles internos |
| **Prediction Service Components** | `images/c4-component-prediction.png` | Level 3: Detalles internos |
| **Tariff Service Components** | `images/c4-component-tariff.png` | Level 3: Detalles internos |

---

## Level 1: System Context

![System Context Diagram](images/c4-context.png)

**Descripción:**
- **Usuario Residencial:** Propietario/arrendatario que monitorea su consumo
- **Dispositivo IoT:** Contador inteligente que envía las lecturas a la Empresa Energética
- **Empresa Energética:** Recibe las lecturas del contador y entrega los datos de consumo al Consumption Service
- **Comercializador de Tarifas:** Sistema externo que envía las tarifas al Tariff Service
- **HarmoniWatts:** Sistema centralizado de análisis y predicción

---

## Level 2: Container Architecture

![Container Architecture Diagram](images/c4-container.png)

**Contenedores principales:**

### 📱 Frontend
- **Frontend Web** (Angular SPA) - Dashboard interactivo

### 🔵 Microservicios Backend

**Consumption Service (Python/FastAPI)**
- Ingesta de datos IoT en tiempo real
- Almacenamiento en MongoDB
- Procesamiento asincrónico con Celery

**Insights Service (Node.js/Express)**
- Agregación y análisis de datos
- Generación de dashboards
- Consulta de predicciones

**Vivienda API (Java/Spring Boot)**
- Gestión de viviendas y usuarios
- Configuración residencial
- Autenticación con Keycloak

**Electrodomésticos API (Java/Spring Boot)**
- Registro de dispositivos
- Predicción por aparato individual
- Recomendaciones de reemplazo

**Prediction Service (Python/FastAPI + ML)** ⏳ Planeado
- Modelo de Machine Learning
- Predicción de consumo mensual
- API REST para consultas

**Tariff Service (Java/Spring Boot)** 🔄 Implementación actual mockeada
- Recibe las tarifas del Comercializador externo
- Persiste las tarifas por hora en PostgreSQL

### 🔐 Autenticación
- **Keycloak** - SSO, OIDC/OAuth2, gestión de identidades

### 🗄️ Infraestructura
- **MongoDB** - Series de tiempo (consumption_readings, daily_summaries)
- **PostgreSQL** - Datos transaccionales (users, households, appliances)
- **Redis** - Cache + Celery task queue

---

## Level 3: Component Diagrams

### 🔵 Consumption Service - Componentes Internos

![Consumption Service Components](images/c4-component-consumption.png)

**Componentes:**
- **API Routes:** Endpoints REST (`/ingest`, `/api/v1/consumption/*`)
- **Data Service:** Lógica de validación y transformación
- **MongoDB Driver:** Acceso asincrónico a MongoDB con Motor
- **Celery Tasks:** Procesamiento asincrónico de ingesta masiva

### 🟢 Insights Service - Componentes Internos

![Insights Service Components](images/c4-component-insights.png)

**Componentes:**
- **Dashboard Routes:** Endpoints `/api/v1/dashboard/*`
- **Insights Service:** Lógica de agregación y análisis
- **Consumption Client:** Cliente HTTP para Consumption Service
- **Prediction Client:** Cliente HTTP para Prediction Service

### 🟡 Vivienda API - Componentes Internos

![Vivienda API Components](images/c4-component-vivienda.png)

**Componentes:**
- **Houses Controller:** Endpoints REST para CRUD de viviendas
- **Houses Service:** Lógica de negocio y validaciones
- **Houses Repository:** Acceso a datos con Spring JPA
- PostgreSQL backend

### 🟠 Electrodomésticos API - Componentes Internos

![Electrodomésticos API Components](images/c4-component-appliances.png)

**Componentes:**
- **Appliances Controller:** Endpoints REST para dispositivos
- **Appliances Service:** Clasificación y cálculo de consumo
- **Appliances Repository:** Acceso a datos con Spring JPA
- Llamadas a Prediction Service
- PostgreSQL backend

### 🟣 Prediction Service - Componentes Internos (Planeado)

![Prediction Service Components](images/c4-component-prediction.png)

**Componentes:**
- **Prediction Routes:** Endpoints `/predict/monthly`, `/predict/appliance`
- **ML Model:** Modelo entrenado (TensorFlow/scikit-learn)
- **Data Aggregator:** Obtiene datos históricos de Consumption Service

---

### ⚙️ Tariff Service - Componentes Internos

![Tariff Service Components](images/c4-component-tariff.png)

**Componentes:**
- **Tariff Controller:** Endpoints de tarifas
- **Tariff Service:** Lógica de tarifas
- **Tariff Repository:** Persistencia de tarifas por hora en PostgreSQL (Spring JPA)

---

## 🔄 Diagramas de Secuencia

### Ingesta de datos IoT
![Ingesta](images/sequence-ingesta.png)

### Visualización de dashboards
![Dashboard](images/sequence-dashboard.png)

### Registro y predicción de electrodomésticos
![Predicción](images/sequence-prediccion.png)

### Autenticación con Keycloak
![Autenticación](images/sequence-autenticacion.png)

### Recomendaciones de ahorro (futuro)
![Recomendaciones](images/sequence-recomendaciones.png)

### Integración de tarifas
![Tarifas](images/sequence-tariffas.png)

---

## 🛠️ Regenerar los diagramas

Los C4 se generan desde [`workspace.dsl`](workspace.dsl) con Structurizr (playground online o `structurizr/lite` en Docker) y se exportan a `images/`. Los de secuencia tienen su fuente Mermaid en `sequence-*.mmd`, junto a `images/`.

---

## 📋 Leyenda de Colores

| Color | Significado |
|-------|------------|
| 🔵 Azul | Microservicios principales |
| 🟢 Verde | Servicios de análisis e insights |
| 🟡 Amarillo | APIs de dominio |
| 🟠 Naranja | APIs especializadas |
| 🟣 Púrpura | Servicios de predicción (planeados) |
| 🗄️ Gris | Bases de datos |
| 🔴 Rojo | Cache y queues |
| 🔐 Naranja | Identidad y autenticación |

---

## 📚 Referencias

- **Documento Maestro:** `docs/ARQUITECTURA-MAESTRA.md`
- **Diccionario de Datos:** `docs/architecture/DATA_DICTIONARY.md`
- **Archivo DSL:** `docs/architecture/workspace.dsl` (fuente de los C4)
- **C4 Model:** https://c4model.com/
- **Structurizr:** https://structurizr.com/

---

**Última actualización:** 18 de Septiembre de 2026  
**Estado:** Diagramas compilados como PNG  
**Sincronización:** Imágenes disponibles en GitHub y Confluence
