# HarmoniWatts ⚡🏠

**Sistema Inteligente de Gestión de Demanda Eléctrica Residencial basado en Franjas Horarias y Perfiles de Consumo**

[![Licencia](https://img.shields.io/badge/Licencia-MIT-green.svg)](LICENSE)
[![Versión](https://img.shields.io/badge/Versión-1.0.0-blue)]()
[![Estado](https://img.shields.io/badge/Estado-Prototipo%20Académico-orange)]()

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

## 🛠️ Stack técnico (actual y objetivo)

| Capa | Implementado hoy | Objetivo / roadmap (release plan) |
|------|-------------------|-------------------------------------|
| **Frontend** | **Angular 21+**, Keycloak JS / keycloak-angular | Dashboard, gráficos (p. ej. librería de charts del ecosistema Angular) |
| **Identidad** | **Keycloak** (OIDC/OAuth2), realm `harmoniwatts` | Igual; endurecer SMTP y service accounts en producción |
| **Registro / acciones email** | **harmoni-register** (Node) — Admin API | Opcional migración a servicio Java si se unifica el backend |
| **Backend de negocio** | — | **Java 21** (API de dominio, hexagonal) |
| **IA / predicción** | — | Python **FastAPI** (SmartLoadPredictor), modelo STLF |
| **Base de datos** | **PostgreSQL** (Keycloak) | **PostgreSQL** para datos de negocio |
| **Mensajería** | — | Kafka / Azure Event Hubs (según decisión de arquitectura) |
| **Despliegue** | **Docker Compose** (dev) | Contenedores + orquestación (p. ej. AKS) según sprint |

---

## 📁 Estructura del Repositorio

*(En construcción.)*

---

## 📚 Documentación

La documentación del proyecto está en la carpeta **`docs/`**. Referencia principal:

| Documento | Descripción |
|-----------|-------------|
| [ARQUITECTURA-HarmoniWatts.md](docs/ARQUITECTURA-HarmoniWatts.md) | Arquitectura: contexto, contenedores, componentes, despliegue y flujos (Mermaid) |
| [KEYCLOAK-REALM-CLIENT.md](docs/KEYCLOAK-REALM-CLIENT.md) | Configuración del realm, cliente y IdP en Keycloak |
| [REGISTER-API.md](docs/REGISTER-API.md) | API de registro de usuarios y olvidé contraseña (harmoni-register) |
| [KEYCLOAK-SMTP.md](docs/KEYCLOAK-SMTP.md) | Configuración SMTP en Keycloak (correos de verificación y restablecimiento) |
| [DOCKER-KEYCLOAK.md](docs/DOCKER-KEYCLOAK.md) | Despliegue de Keycloak con Docker; realm preconfigurado vía `keycloak-realm/` |
| [AUTH-FLOW.md](docs/AUTH-FLOW.md) | Flujo de autenticación (OIDC/OAuth2) |
| [HarmoniWatts_BPM.md](docs/HarmoniWatts_BPM.md) | Procesos y modelo BPM del sistema |
| [HarmoniWatts_ReleasePlan.md](docs/HarmoniWatts_ReleasePlan.md) | Plan de releases y entregas |

Para arrancar el entorno (Keycloak, harmoni-register, etc.), ver también el `docker-compose.yml` en la raíz y las instrucciones en `docs/DOCKER-KEYCLOAK.md` y `harmoni-register/README.md`.

