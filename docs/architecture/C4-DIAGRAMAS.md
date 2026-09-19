# 📊 Diagramas C4 - HarmoniWatts

**Diagramas de arquitectura compilados desde Structurizr DSL con visualización completa.**

---

## 🔧 Compilar Diagramas Interactivos

Para obtener diagramas interactivos y explorables:

### Opción 1: Online (Recomendado - Sin instalación)
```
1. Ir a https://structurizr.com/dsl
2. Copiar contenido de docs/architecture/workspace.dsl
3. Pegar en el editor (lado izquierdo)
4. Los diagramas se renderizan automáticamente (lado derecho)
5. Puedes hacer zoom, arrastrar, exportar como PNG/SVG
```

### Opción 2: Docker Local
```bash
docker run -it --rm -p 8080:8080 -v ./docs/architecture:/workspace structurizr/lite:latest
# Luego abrir http://localhost:8080
```

---

## Level 1: System Context - C4

**¿Qué es?** Visión de alto nivel del sistema y sus actores externos.

```mermaid
graph TB
    subgraph externos["🌍 Actores Externos"]
        U["👤 Usuario Residencial"]
        E["⚡ Empresa Energética"]
        I["📱 Dispositivo IoT"]
    end
    
    subgraph sistema["🏠 Sistema HarmoniWatts"]
        HW["HarmoniWatts<br/>(Sistema inteligente)"]
    end
    
    U -->|"Usa navegador"| HW
    U -->|"Paga servicios"| E
    I -->|"Envía lecturas<br/>consumo"| HW
    E -->|"Proporciona tarifas<br/>y datos"| HW
```

**Componentes:**
- **Usuario Residencial:** Propietario/arrendatario que interactúa con el sistema
- **Empresa Energética:** Proveedor de tarifas, datos de consumo histórico
- **Dispositivo IoT:** Medidor inteligente que envía datos de consumo en tiempo real
- **HarmoniWatts:** Sistema centralizado que orquesta todo

---

## Level 2: Container Architecture - C4

**¿Qué es?** Principales contenedores (aplicaciones, servicios, BDs) que componen el sistema.

```mermaid
graph TB
    subgraph usuario["👤 Usuario"]
        Browser["🌐 Navegador"]
    end
    
    subgraph harmoniwatts["🏠 HarmoniWatts"]
        FE["📱 Frontend<br/>(Angular SPA)"]
        
        CS["🔵 Consumption Service<br/>(Python/FastAPI)"]
        IS["🟢 Insights Service<br/>(Node.js/Express)"]
        HA["🟡 Vivienda API<br/>(Java/Spring Boot)"]
        EA["🟠 Electrodomésticos API<br/>(Java/Spring Boot)"]
        PS["🟣 Prediction Service<br/>(Python/FastAPI + ML)"]
        TS["⚙️ Tariff Service<br/>(Java/Spring Boot)"]
        
        KC["🔐 Keycloak<br/>(SSO/Identity)"]
        
        MG["🗄️ MongoDB<br/>(Series de tiempo)"]
        PG["🗄️ PostgreSQL<br/>(Datos transaccionales)"]
        RD["🔴 Redis<br/>(Cache + Queue)"]
    end
    
    subgraph externos["🌍 Externos"]
        IoT["📱 Medidor IoT"]
        Util["⚡ Empresa Energía"]
    end
    
    Browser -->|"OIDC/OAuth2"| FE
    FE -->|"GET /api/v1/..."| CS
    FE -->|"GET /api/v1/..."| IS
    FE -->|"API REST"| HA
    FE -->|"API REST"| EA
    FE -->|"Autentica"| KC
    
    IS -->|"Consulta datos"| CS
    IS -->|"Solicita predicciones"| PS
    EA -->|"Predicciones"| PS
    EA -->|"Datos históricos"| CS
    
    CS -->|"Valida JWT"| KC
    HA -->|"Valida JWT"| KC
    
    CS -->|"Lee/escribe"| MG
    CS -->|"Async tasks"| RD
    HA -->|"Lee/escribe"| PG
    EA -->|"Lee/escribe"| PG
    
    IoT -->|"POST /ingest"| CS
    Util -->|"Tarifas"| TS
```

**Contenedores principales:**

| Contenedor | Tech | Responsabilidad |
|-----------|------|-----------------|
| **Frontend Web** | Angular 21+ | SPA responsivo, dashboards, controles |
| **Consumption Service** | Python/FastAPI | Ingesta IoT, almacenamiento, query consumo |
| **Insights Service** | Node.js/Express | Agregación datos, dashboards, análisis |
| **Vivienda API** | Java/Spring Boot | Gestión viviendas, usuarios, perfiles |
| **Electrodomésticos API** | Java/Spring Boot | Registro dispositivos, predicciones |
| **Prediction Service** | Python/FastAPI + ML | IA para predicción de consumo (⏳ Planeado) |
| **Tariff Service** | Java/Spring Boot | Gestión tarifas energéticas (🔄 Mockado) |
| **Keycloak** | Keycloak | SSO, OIDC/OAuth2, gestión identidades |
| **MongoDB** | NoSQL | Series de tiempo, consumo real-time |
| **PostgreSQL** | SQL Relacional | Datos transaccionales (usuarios, dispositivos) |
| **Redis** | Cache/Queue | Cache, Celery tasks |

---

## Level 3: Component Diagrams - C4

### Consumption Service - Componentes

```mermaid
graph TB
    subgraph api["🔵 Consumption Service"]
        AR["📍 API Routes<br/>(FastAPI Router)"]
        DS["💼 Data Service<br/>(FastAPI Service)"]
        MG["🗄️ MongoDB Driver<br/>(Motor)"]
        CT["⏱️ Celery Tasks<br/>(Async)"]
    end
    
    subgraph external["Externos"]
        RD["🔴 Redis"]
        DB["🗄️ MongoDB"]
    end
    
    AR -->|"Procesa requests"| DS
    DS -->|"Accede datos"| MG
    DS -->|"Enqueue"| CT
    CT -->|"Lee tasks"| RD
    MG -->|"Lee/escribe"| DB
```

**Responsabilidades:**
- **API Routes:** Endpoints REST (`/ingest`, `/api/v1/consumption/*`)
- **Data Service:** Lógica de validación, transformación, procesamiento
- **MongoDB Driver:** Acceso asincrónico a MongoDB
- **Celery Tasks:** Procesamiento asincrónico de ingesta masiva

### Insights Service - Componentes

```mermaid
graph TB
    subgraph api["🟢 Insights Service"]
        DR["📍 Dashboard Routes<br/>(Express Router)"]
        IS["💼 Insights Service<br/>(Express Service)"]
        CC["📡 Consumption Client<br/>(Axios)"]
        PC["📡 Prediction Client<br/>(Axios)"]
    end
    
    subgraph external["Externos"]
        CS["🔵 Consumption Service"]
        PS["🟣 Prediction Service"]
    end
    
    DR -->|"Procesa requests"| IS
    IS -->|"Consulta"| CC
    IS -->|"Solicita"| PC
    CC -->|"HTTP GET"| CS
    PC -->|"HTTP POST"| PS
```

**Responsabilidades:**
- **Dashboard Routes:** Endpoints `/api/v1/dashboard/*`, `/api/v1/recommendations/*`
- **Insights Service:** Agregación, análisis, lógica de negocio
- **Clients:** Clientes HTTP para consultar otros servicios

### Vivienda API - Componentes

```mermaid
graph TB
    subgraph api["🟡 Vivienda API"]
        HC["🌐 Houses Controller<br/>(Spring MVC)"]
        HS["💼 Houses Service<br/>(Service Layer)"]
        HR["🗄️ Houses Repository<br/>(Spring JPA)"]
    end
    
    subgraph external["Externos"]
        DB["🗄️ PostgreSQL"]
    end
    
    HC -->|"Delegua"| HS
    HS -->|"Accede datos"| HR
    HR -->|"Lee/escribe"| DB
```

**Responsabilidades:**
- **Controller:** Endpoints REST para CRUD de viviendas
- **Service:** Lógica de negocio, validaciones
- **Repository:** Persistencia en PostgreSQL

### Electrodomésticos API - Componentes

```mermaid
graph TB
    subgraph api["🟠 Electrodomésticos API"]
        AC["🌐 Appliances Controller<br/>(Spring MVC)"]
        AS["💼 Appliances Service<br/>(Service Layer)"]
        AR["🗄️ Appliances Repository<br/>(Spring JPA)"]
    end
    
    subgraph external["Externos"]
        DB["🗄️ PostgreSQL"]
        PS["🟣 Prediction Service"]
    end
    
    AC -->|"Delegua"| AS
    AS -->|"Accede datos"| AR
    AS -->|"Solicita predicciones"| PS
    AR -->|"Lee/escribe"| DB
```

**Responsabilidades:**
- **Controller:** Endpoints REST para dispositivos, predicciones
- **Service:** Clasificación, cálculo de consumo estimado
- **Repository:** Persistencia en PostgreSQL

### Prediction Service - Componentes (Planeado)

```mermaid
graph TB
    subgraph api["🟣 Prediction Service"]
        PR["📍 Prediction Routes<br/>(FastAPI Router)"]
        ML["🤖 ML Model<br/>(TensorFlow/scikit-learn)"]
        DA["📊 Data Aggregator<br/>(Python Service)"]
    end
    
    subgraph external["Externos"]
        CS["🔵 Consumption Service"]
    end
    
    PR -->|"Procesa requests"| ML
    ML -->|"Requiere datos"| DA
    DA -->|"Obtiene histórico"| CS
```

**Responsabilidades:**
- **Prediction Routes:** Endpoints `/predict/monthly`, `/predict/appliance`
- **ML Model:** Modelo entrenado (TensorFlow/scikit-learn)
- **Data Aggregator:** Obtiene datos históricos y los prepara para ML

---

## Relaciones Entre Servicios

### Flujos de Datos Principales

```mermaid
graph LR
    IoT["📱 IoT Device<br/>(Medidor)"]
    CS["🔵 Consumption<br/>Service"]
    IS["🟢 Insights<br/>Service"]
    EA["🟠 Electrodomésticos<br/>API"]
    PS["🟣 Prediction<br/>Service"]
    FE["📱 Frontend<br/>(Angular)"]
    
    IoT -->|"1. POST /ingest"| CS
    CS -->|"2. Almacena en MongoDB"| CS
    IS -->|"3. Consulta /consumption"| CS
    EA -->|"4. Solicita histórico"| CS
    IS -->|"5. Solicita /predict"| PS
    EA -->|"6. Solicita /predict"| PS
    IS -->|"7. Retorna dashboard"| FE
    FE -->|"8. Solicita /dashboard"| IS
```

### Orquestación Asincrónica

```mermaid
graph TB
    CS["🔵 Consumption Service"]
    CT["⏱️ Celery Task"]
    RD["🔴 Redis Queue"]
    MG["🗄️ MongoDB"]
    
    CS -->|"1. Queue task"| RD
    CS -->|"2. Retorna 202 Accepted"| User["👤 Usuario"]
    RD -->|"3. Consume task"| CT
    CT -->|"4. Procesa datos"| CT
    CT -->|"5. Almacena"| MG
    
    style CS fill:#438dd5,stroke:#fff,color:#fff
    style CT fill:#85BBF0,stroke:#000
    style RD fill:#ff6b35,stroke:#fff,color:#fff
    style MG fill:#438dd5,stroke:#fff,color:#fff
```

---

## Exportar Diagramas

Desde Structurizr Playground puedes exportar cada diagrama como:
- **SVG** (Escalable, ideal para web)
- **PNG** (Raster, más compatible)
- **PDF** (Para presentaciones)

**Pasos:**
1. Compilar el DSL en https://structurizr.com/dsl
2. Seleccionar el diagrama que quieres exportar
3. Hacer clic en el icono de "Export" (en la barra de herramientas)
4. Seleccionar formato
5. Descargar

---

## Referencias

- **Archivo DSL:** `docs/architecture/workspace.dsl`
- **Documento Maestro:** `docs/ARQUITECTURA-MAESTRA.md`
- **C4 Model:** https://c4model.com/
- **Structurizr:** https://structurizr.com/help/dsl

---

**Última actualización:** 18 de Septiembre de 2026  
**Formato:** Mermaid (compilable en GitHub) + Structurizr DSL (compilable online/Docker)
