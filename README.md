# HarmoniWatts ⚡🏠

**Sistema Inteligente de Gestión de Demanda Eléctrica Residencial basado en Franjas Horarias y Perfiles de Consumo**

[![Licencia](https://img.shields.io/badge/Licencia-MIT-green.svg)](LICENSE)
[![Versión](https://img.shields.io/badge/Versión-1.0.0-blue)]()
[![Estado](https://img.shields.io/badge/Estado-Prototipo%20Académico-orange)]()
[![Documentación](https://img.shields.io/badge/Documentación-Confluencia-blue)](https://giia.atlassian.net/wiki/spaces/HarmoniWatts)

---

## 📋 Descripción del Proyecto

**HarmoniWatts** es un sistema inteligente diseñado para optimizar el consumo eléctrico en hogares mediante la gestión automatizada de la demanda. El sistema analiza en tiempo real las tarifas eléctricas por franjas horarias (TOU, RTP) y los perfiles de consumo del usuario para generar recomendaciones personalizadas y, cuando es posible, automatizar el funcionamiento de electrodomésticos desplazables.

Este proyecto se desarrolla como **Trabajo Integrador de Maestría** y aborda la problemática de la ineficiencia energética residencial en contextos de tarifas dinámicas, contribuyendo tanto al ahorro económico del usuario como a la estabilidad de la red eléctrica.

### 🎯 Objetivos Principales

- **Predecir** el consumo eléctrico a corto plazo basado en patrones históricos.
- **Caracterizar** perfiles de usuario mediante técnicas de clustering no supervisado.
- **Optimizar** la programación de cargas flexibles para minimizar el costo energético.
- **Automatizar** o recomendar acciones de desplazamiento de consumo a franjas de menor precio.
- **Visualizar** el impacto económico y energético de las decisiones de gestión.

---

## 🧠 Arquitectura del Sistema

HarmoniWatts se organiza en dos capas funcionales:

### Capa de Gestión y Operación (Funcionalidades Base)
- Registro y perfilamiento de usuarios residenciales.
- Conexión a fuentes de datos externas (tarifas del comercializador, contador inteligente).
- Dashboard interactivo de visualización de consumo, costos y ahorros.
- Panel de control manual para dispositivos IoT.
- Gestión de enchufes inteligentes y termostatos compatibles.

### Capa de Procesamiento Inteligente (Núcleo de IA)
- **Módulo de Predicción de Consumo:** Anticipa la demanda energética del hogar en ventanas de 24-48 horas.
- **Módulo de Análisis de Oportunidad:** Fusiona perfiles de usuario con señales de precios dinámicos para identificar ventanas de ahorro.
- **Módulo de Optimización y Planificación:** Genera el plan horario óptimo para electrodomésticos desplazables (lavadora, termo, EV, ESS) y lo ejecuta o recomienda.

---

## 🔄 Flujo de Procesos (BPMN)

El sistema sigue un flujo de trabajo definido en notación BPMN 2.0 con tres actores principales:

1. **Usuario Residencial** – Interactúa con la aplicación y toma decisiones sobre recomendaciones.
2. **Sistema HarmoniWatts** – Ejecuta el análisis inteligente y la optimización.
3. **Proveedor de Energía** – Fuente de datos de tarifas y consumo histórico.

El diagrama BPMN 2.0 (draw.io) está en [`docs/HarmoniWatts_BPM.drawio`](docs/HarmoniWatts_BPM.drawio); un resumen en Mermaid en [`docs/HarmoniWatts_BPM.md`](docs/HarmoniWatts_BPM.md).

El flujo completo incluye:
- Registro y configuración inicial.
- Obtención de tarifas y consumo.
- Procesamiento inteligente (clustering, simulación, optimización).
- Generación y entrega de recomendaciones.
- Decisión del usuario (aceptar/rechazar/ajustar).
- Retroalimentación y actualización del modelo.
- Reporte consolidado de ahorros.

---

## 🛠️ Stack técnico

### Implementado hoy

| Capa | Tecnología | Detalles |
|------|-----------|----------|
| **Frontend** | **Angular 21+** | SPA con Keycloak-Angular, dashboard interactivo |
| **Identidad** | **Keycloak** (OIDC/OAuth2) | Realm `harmoniwatts`, soporte Google IdP, SMTP para emails |
| **Registro de usuarios** | **harmoni-register** (Node.js) | Admin API para crear usuarios sin exponer credenciales |
| **Base de datos (Identidad)** | **PostgreSQL** | Persistencia de Keycloak |
| **Despliegue** | **Docker Compose** | Stack local para desarrollo |

### En desarrollo / Próximas fases

| Capa | Tecnología | Estado |
|------|-----------|--------|
| **Backend de negocio** | **Java 21** + Spring Boot | 🔄 Parcialmente implementado (Vivienda, Electrodomésticos APIs) |
| **Consumption Service** | **Python/FastAPI** | ✅ Implementado (ingesta de datos IoT) |
| **Insights Service** | **Node.js/Express** | ✅ Implementado (dashboards, análisis) |
| **Prediction Service (IA)** | **Python/FastAPI** + TensorFlow/scikit-learn | ⏳ Planeado Q4 2026 |
| **Mensajería** | Kafka / Azure Event Hubs | 🔄 Planeado |
| **Orquestación** | Kubernetes / AKS | 🔄 Futuro |

---

## 📁 Estructura del Repositorio

```
HarmoniWatts/
├── frontend/                      # Angular SPA
├── backend/
│   ├── consumption-service/       # FastAPI - Ingesta IoT
│   └── insights-service/          # Express.js - Dashboards
├── harmoniwatts-vivienda-api/     # Spring Boot - Viviendas
├── harmoniwatts-electrodomesticos-api/  # Spring Boot - Dispositivos
├── harmoniwatts-api/              # Spring Boot - API Gateway (planeado)
├── harmoni-register/              # Node.js - Admin API
├── keycloak-realm/                # Configuración Keycloak predefin ido
├── docker/                        # Docker Compose configs
├── docs/                          # Documentación técnica
│   ├── architecture/              # Diagramas C4 y de secuencia (imágenes) + DSL
│   ├── imagenes/
│   │   ├── mockups/               # Maquetas de UI (login, dashboard, perfil, tarifas)
│   │   └── diagramas/             # BPM, mapa del sitio, flujos y ramas Git
│   ├── latex/                     # Fuentes .tex (arquitectura de información, investigación IA)
│   ├── ARQUITECTURA-MAESTRA.md
│   ├── AUTH-FLOW.md
│   ├── KEYCLOAK-*.md
│   ├── HarmoniWatts_BPM.md
│   └── HarmoniWatts_ReleasePlan.md
└── sql/                           # Scripts iniciales
```

---

## 📚 Documentación Técnica

### 🔗 Documentación de Arquitectura (Prioridad)

| Documento | Descripción | Ubicación |
|-----------|-------------|-----------|
| **Diagramas C4 y de secuencia** | Contexto, contenedores, componentes de cada servicio y 6 flujos, como imágenes | [`docs/architecture/C4-DIAGRAMAS.md`](docs/architecture/C4-DIAGRAMAS.md) |
| **Documento maestro de arquitectura** | Visión unificada de servicios, datos y flujos | [`docs/ARQUITECTURA-MAESTRA.md`](docs/ARQUITECTURA-MAESTRA.md) |
| **Diccionario de Datos** | Esquemas MongoDB + PostgreSQL, índices, políticas de retención | [`docs/architecture/DATA_DICTIONARY.md`](docs/architecture/DATA_DICTIONARY.md) |
| **Fuente de los diagramas C4** | Structurizr DSL para regenerar las imágenes | [`docs/architecture/workspace.dsl`](docs/architecture/workspace.dsl) |

### 📖 Documentación de Operación y Configuración

| Documento | Descripción |
|-----------|-------------|
| [KEYCLOAK-REALM-CLIENT.md](docs/KEYCLOAK-REALM-CLIENT.md) | Configuración del realm, cliente y IdP en Keycloak |
| [REGISTER-API.md](docs/REGISTER-API.md) | API de registro y olvidé contraseña (harmoni-register) |
| [KEYCLOAK-SMTP.md](docs/KEYCLOAK-SMTP.md) | Configuración SMTP para emails de verificación |
| [DOCKER-KEYCLOAK.md](docs/DOCKER-KEYCLOAK.md) | Despliegue de Keycloak y servicios con Docker |
| [AUTH-FLOW.md](docs/AUTH-FLOW.md) | Flujo de autenticación OIDC/OAuth2 |
| [HarmoniWatts_BPM.md](docs/HarmoniWatts_BPM.md) | Procesos de negocio (BPMN 2.0) |
| [HarmoniWatts_ReleasePlan.md](docs/HarmoniWatts_ReleasePlan.md) | Plan de releases y entregas |

### 🏗️ Confluencia (Documentación Interactiva)

**Toda la documentación técnica sincronizada también en Confluence:**  
🔗 **[HarmoniWatts - Documentación Técnica Completa](https://giia.atlassian.net/wiki/spaces/HarmoniWatts)**

- ✅ 11 páginas jerárquicas
- ✅ Especificación de cada microservicio
- ✅ Diagramas de secuencia rendibles
- ✅ Diccionario de datos completo
- ✅ Guía de setup paso a paso

---

## 🚀 Inicio Rápido

### Requisitos Previos

```bash
# Versiones recomendadas
- Docker & Docker Compose v20+
- Python 3.11+ (Consumption Service)
- Node.js 18+ (Insights Service, harmoni-register)
- Java 17+ (APIs Spring Boot)
- PostgreSQL 14+
- MongoDB 6+
```

### Iniciar Ambiente Local

```bash
# Clonar repositorio
git clone https://github.com/MayorChris/HarmoniWatts.git
cd HarmoniWatts

# Opción 1: Docker Compose (Recomendado)
docker-compose -f docker/docker-compose.yml up -d

# Opción 2: Servicios individuales
# Frontend
cd frontend && npm install && ng serve

# Consumption Service
cd backend/consumption-service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && uvicorn app.main:app --reload

# Insights Service
cd backend/insights-service
npm install && npm run dev
```

### Acceso a Servicios

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| **Frontend** | http://localhost:4200 | Registro o Google SSO |
| **Keycloak** | http://localhost:8080 | admin / (ver .env) |
| **Consumption API** | http://localhost:8000/docs | JWT Bearer token |
| **Insights API** | http://localhost:3000 | JWT Bearer token |
| **Vivienda API** | http://localhost:8001/swagger-ui.html | JWT Bearer token |
| **Electrodomésticos API** | http://localhost:8002/swagger-ui.html | JWT Bearer token |

---

## 📊 Microservicios

### ✅ Implementados

**Consumption Service (Python/FastAPI)**
- Ingesta de datos de consumo en tiempo real desde medidores IoT
- Almacenamiento en MongoDB con índices optimizados
- Procesamiento asincrónico con Celery + Redis
- Endpoints: `/api/v1/consumption/*`, `/health`, `/ready`

**Insights Service (Node.js/Express)**
- Dashboards interactivos: resumen, gráficos, recomendaciones
- Agregación de datos de Consumption Service
- Integración con Prediction Service
- Endpoints: `/api/v1/dashboard/*`

**Vivienda API (Java/Spring Boot)**
- CRUD de viviendas, usuarios y perfiles
- Autenticación integrada con Keycloak
- Persistencia en PostgreSQL
- Endpoints: `/api/v1/households/*`, `/api/v1/users/*`

**Electrodomésticos API (Java/Spring Boot)**
- Registro y clasificación de dispositivos
- Predicción de consumo por aparato
- Recomendaciones de reemplazo
- Endpoints: `/api/v1/appliances/*`, `/api/v1/appliances/top-consumers`

### ⏳ Planeados

**Prediction Service (Python/FastAPI + ML)**
- Modelo de Machine Learning para predicción de consumo mensual
- APIs REST para consultas desde otros servicios
- Especificación: `docs/architecture/DATA_DICTIONARY.md`

**Tariff Service (Java/Spring Boot)**
- Gestión de tarifas dinámicas por franja horaria
- Integración con proveedores de energía
- Actualmente mockado; especificación lista

---

## 📝 Convenciones de Desarrollo

### Commits

```bash
git commit -m "feat(auth): agregar 2FA con TOTP"
git commit -m "fix(dashboard): corregir cálculo de consumo pico"
git commit -m "docs: actualizar README de setup"
```

### Ramas

```
main              → producción (stable)
qa                → testing
feature/*         → nuevas características
fix/*             → correcciones
docs/*            → documentación
```

### Código

- **Backend Java:** Arquitectura hexagonal, inyección de dependencias
- **Backend Python:** FastAPI con Pydantic, logging estructurado
- **Frontend:** Angular best practices, components reutilizables
- **Bases de datos:** Índices documentados, políticas de retención claras

---

## 🔐 Seguridad

- **Autenticación:** Keycloak con OIDC/OAuth2
- **Autorización:** RLS en bases de datos, roles en Keycloak
- **Cifrado:** TLS en tránsito (HTTPS), secrets en variables de entorno
- **Tokens:** JWT con expiraciones, refresh tokens seguros
- **Validación:** Pydantic (backend), Angular validators (frontend)

---

## 📞 Contacto y Contribuciones

- **Estudiantes:** Christian Camilo Rosero Rodríguez / Carlos David Rojas Lozano
- **Profesor:** Javier Mauricio Reyes Vera PhD.
- **Instituciónón:** Pontificia Universidad Javeriana

---

## 📜 Licencia

Este proyecto se distribuye bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

**Última actualización:** 18 de Septiembre de 2026  
**Versión:** 1.0.0  
**Estado:** Prototipo Académico en Desarrollo Activo

