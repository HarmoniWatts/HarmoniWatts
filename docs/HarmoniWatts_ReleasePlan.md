# Release Plan — HarmoniWatts (HEMS)
**Proyecto:** Sistema Inteligente de Gestión de Demanda Eléctrica  
**Metodología:** Scrum — 8 Sprints de 3 semanas  
**Equipo:** Christian Camilo Rosero Rodriguez / Carlos David Rojas Lozano  

---

## Calendario de Sprints

| Sprint | Período | Momento |
|--------|---------|---------|
| Sprint 0 | 13 feb – 06 mar 2026 | Trabajo Integrador I |
| Sprint 1 | 09 mar – 27 mar 2026 | Trabajo Integrador I |
| Sprint 2 | 30 mar – 11 abr 2026 | Trabajo Integrador I |
| **— TIEMPO LIBRE —** | **mediados abr – ago 2026** | — |
| Sprint 3 | 01 sep – 19 sep 2026 | Trabajo Integrador II |
| Sprint 4 | 22 sep – 10 oct 2026 | Trabajo Integrador II |
| Sprint 5 | 13 oct – 31 oct 2026 | Trabajo Integrador II |
| Sprint 6 | 03 nov – 21 nov 2026 | Trabajo Integrador III |
| Sprint 7 | 24 nov – 12 dic 2026 | Trabajo Integrador III |
| Sprint 8 | 15 dic – 31 dic 2026 | Trabajo Integrador III |

---

## Sprint 0 — Visión, Arquitectura y Product Backlog
**Fechas:** 13 feb – 06 mar 2026  
**Objetivo:** Establecer las bases del proyecto, definir la visión del producto, modelar el sistema y construir el Release Plan oficial.

### Épicas
- EP-01: Gestión del proyecto y configuración inicial
- EP-02: Diseño de arquitectura y modelado del sistema

### Historias de Usuario

#### HU-01 — Sesión de visión del producto
> **Como** equipo de desarrollo,  
> **quiero** realizar una sesión formal de Product Vision,  
> **para** alinear a todos los stakeholders sobre los objetivos y alcance de HarmoniWatts.

**Criterios de aceptación:**
- [ ] Se documenta el Product Vision Statement con objetivo, usuarios, problema y valor diferencial.
- [ ] Todos los integrantes del equipo validan y firman el documento de visión.
- [ ] Se identifican al menos 5 épicas del sistema.

---

#### HU-02 — Creación del Product Backlog en Jira
> **Como** Product Owner,  
> **quiero** tener el Product Backlog configurado en Jira,  
> **para** gestionar, priorizar y rastrear todas las historias de usuario del proyecto.

**Criterios de aceptación:**
- [ ] El proyecto está creado en Jira con tablero Scrum activo.
- [ ] Se registran al menos 20 historias de usuario con estimaciones en Story Points.
- [ ] Las historias están agrupadas por épicas y priorizadas en el backlog.
- [ ] Se definen la Definition of Ready (DoR) y Definition of Done (DoD).

---

#### HU-03 — Modelado BPM del proceso general HEMS
> **Como** arquitecto del sistema,  
> **quiero** un diagrama BPM del proceso principal del HEMS,  
> **para** tener una representación visual del flujo de negocio y sus actores.

**Criterios de aceptación:**
- [ ] El diagrama BPM incluye los flujos: registro de usuario, conexión a contador, recepción de tarifas, generación de recomendaciones y respuesta del usuario.
- [ ] El diagrama está modelado en notación BPMN 2.0.
- [ ] El diagrama es revisado y aprobado por ambos integrantes del equipo.

---

#### HU-04 — Diseño de arquitectura orientada a microservicios
> **Como** arquitecto del sistema,  
> **quiero** un documento de arquitectura preliminar,  
> **para** definir los componentes, tecnologías y sus interacciones antes de comenzar el desarrollo.

**Criterios de aceptación:**
- [ ] El documento incluye el diagrama de contexto con los 4 componentes principales (HarmoniWatts, HarmoniWattsService, SmartLoadPredictorService, HEMSCustomerEnergyDB).
- [ ] Se especifican las tecnologías: Angular, Spring WebFlux, FastAPI, Azure SQL, AKS, Kafka/EventHub.
- [ ] Se definen los contratos iniciales de las APIs REST entre microservicios.
- [ ] La arquitectura es validada con al menos una sesión de revisión técnica.

---

#### HU-05 — Prototipos de interfaz de usuario (Mockups Angular)
> **Como** usuario final,  
> **quiero** ver prototipos de las pantallas principales de la aplicación,  
> **para** validar el flujo de navegación y la experiencia de usuario antes del desarrollo.

**Criterios de aceptación:**
- [ ] Se entregan mockups de al menos 5 pantallas: Login, Registro, Dashboard, Tarifas TOU y Perfil de usuario.
- [ ] Los mockups son creados en una herramienta de prototipado (Figma o similar).
- [ ] Los prototipos son revisados y aprobados por el equipo.

---

#### HU-06 — Elaboración del Release Plan oficial
> **Como** Scrum Master,  
> **quiero** el Release Plan oficial documentado para los 8 sprints,  
> **para** tener visibilidad del calendario de entregas, historias de usuario y criterios de aceptación por iteración.

**Criterios de aceptación:**
- [ ] El Release Plan cubre los 8 sprints con fechas de inicio y fin.
- [ ] Cada sprint tiene su objetivo, historias de usuario y criterios de aceptación documentados.
- [ ] El documento está versionado y disponible en el repositorio del proyecto.

---

**Entregables Sprint 0:**
- BPM del sistema
- Product Backlog inicial en Jira
- Documento de arquitectura preliminar
- Mockups/UI iniciales en Angular
- Release Plan oficial (este documento)

---

## Sprint 1 — Microservicios Base y Primeras Pantallas
**Fechas:** 09 mar – 27 mar 2026  
**Objetivo:** Desarrollar el núcleo inicial del backend (registro, login, base de datos) y las primeras vistas funcionales en Angular.

### Historias de Usuario

#### HU-07 — Registro de usuario
> **Como** nuevo usuario de HarmoniWatts,  
> **quiero** poder registrarme en la aplicación,  
> **para** crear mi perfil y acceder a las funcionalidades del sistema.

**Criterios de aceptación:**
- [ ] El usuario puede registrarse con nombre, correo electrónico y contraseña.
- [ ] Se valida que el correo no esté previamente registrado.
- [ ] La contraseña debe cumplir políticas de seguridad mínimas (mínimo 8 caracteres, una mayúscula, un número).
- [ ] Los datos se persisten correctamente en HEMSCustomerEnergyDB (Azure SQL).
- [ ] El sistema retorna un mensaje de éxito o error apropiado.

---

#### HU-08 — Autenticación de usuario (Login)
> **Como** usuario registrado,  
> **quiero** iniciar sesión en la aplicación,  
> **para** acceder a mi panel personalizado y mis datos de consumo.

**Criterios de aceptación:**
- [ ] El usuario puede iniciar sesión con correo y contraseña.
- [ ] Se implementa autenticación con JWT (token de acceso y refresh token).
- [ ] Si las credenciales son incorrectas, se muestra un mensaje de error sin revelar qué campo es incorrecto.
- [ ] La sesión expira tras un período de inactividad configurable.
- [ ] Se implementa logout que invalida el token.

---

#### HU-09 — Perfil de vivienda y electrodomésticos
> **Como** usuario autenticado,  
> **quiero** registrar los datos de mi vivienda y mis electrodomésticos principales,  
> **para** que el sistema pueda personalizar las recomendaciones según mi hogar.

**Criterios de aceptación:**
- [ ] El usuario puede ingresar el tipo de vivienda, número de habitantes y ciudad.
- [ ] El usuario puede registrar al menos 5 tipos de electrodomésticos (lavadora, calentador, nevera, aire acondicionado, vehículo eléctrico) con potencia estimada en watts.
- [ ] Los datos del perfil se almacenan en la base de datos y son editables.
- [ ] La interfaz Angular muestra un formulario de perfil completo y funcional.

---

#### HU-10 — Integración básica con Azure SQL
> **Como** desarrollador backend,  
> **quiero** tener la conexión configurada entre el microservicio WebFlux y Azure SQL,  
> **para** garantizar la persistencia y consulta de datos de usuarios desde la nube.

**Criterios de aceptación:**
- [ ] La conexión a HEMSCustomerEnergyDB está configurada en el microservicio HarmoniWattsService.
- [ ] Se ejecutan correctamente operaciones CRUD para entidades: Usuario, Vivienda y Electrodoméstico.
- [ ] Las migraciones de base de datos están gestionadas con Flyway o Liquibase.
- [ ] Se incluyen pruebas unitarias para los repositorios con cobertura mínima del 70%.

---

#### HU-11 — Configuración de proyecto Angular y navegación base
> **Como** desarrollador frontend,  
> **quiero** el proyecto Angular configurado con estructura modular y rutas base,  
> **para** que el equipo pueda desarrollar pantallas de forma organizada y consistente.

**Criterios de aceptación:**
- [ ] El proyecto Angular está creado con Angular CLI, con módulos separados por funcionalidad (auth, dashboard, perfil, tarifas).
- [ ] Se implementa routing con guards de autenticación.
- [ ] Se integra una librería de componentes UI (Angular Material o PrimeNG).
- [ ] La aplicación compila y se ejecuta sin errores en entorno local.

---

**Entregables Sprint 1:**
- Microservicios base (registro, login, BD SQL Azure) funcionando
- Primeras pantallas en Angular (Login, Registro, Perfil)
- Historias de usuario de registro y acceso completadas
- Informe de Daily Scrum, Review y Retrospectiva

---

## Sprint 2 — Dashboard, Datos de Contador y Estructura IA
**Fechas:** 30 mar – 11 abr 2026  
**Objetivo:** Implementar el consumo de datos del contador (mock), desarrollar el dashboard inicial y construir la estructura base del microservicio de predicción.

### Historias de Usuario

#### HU-12 — Dashboard de consumo eléctrico
> **Como** usuario autenticado,  
> **quiero** ver un dashboard con gráficos de mi consumo eléctrico,  
> **para** tener visibilidad sobre mis patrones de gasto y las franjas horarias activas.

**Criterios de aceptación:**
- [ ] El dashboard muestra un gráfico de consumo diario/semanal/mensual.
- [ ] Se visualizan las franjas horarias TOU activas (punta, media, valle) con color diferenciado.
- [ ] Se muestra el costo estimado por franja horaria.
- [ ] Se muestra el ahorro acumulado respecto a una línea base.
- [ ] El dashboard se actualiza con datos del mock del contador cada 5 minutos.
- [ ] La interfaz es responsiva para web y móvil.

---

#### HU-13 — Conexión a mock de contador inteligente
> **Como** sistema HEMS,  
> **quiero** consumir datos de un mock del contador inteligente,  
> **para** simular la recepción de datos de consumo en tiempo real mientras se integra el contador real.

**Criterios de aceptación:**
- [ ] Se implementa un servicio mock que genera datos de consumo eléctrico por hora (kWh) de forma realista.
- [ ] El mock simula variaciones de consumo por tipo de electrodoméstico registrado en el perfil.
- [ ] Los datos del mock se almacenan en Azure SQL con timestamp, consumo (kWh) y costo estimado.
- [ ] El microservicio HarmoniWattsService expone un endpoint para consultar el historial de consumo.

---

#### HU-14 — Control y visualización de tarifas TOU/RTP (mock)
> **Como** usuario,  
> **quiero** ver las tarifas de electricidad vigentes por franja horaria,  
> **para** entender cómo varía el precio de la energía durante el día y tomar decisiones informadas.

**Criterios de aceptación:**
- [ ] Se integra un mock de proveedor de tarifas con valores TOU (punta, media, valle) expresados en $/kWh.
- [ ] Las tarifas se muestran en el dashboard con visualización de línea de tiempo del día.
- [ ] El sistema diferencia claramente las franjas de alto precio (punta) de las franjas económicas (valle).
- [ ] Los datos del mock de tarifas se actualizan al menos una vez por día.

---

#### HU-15 — Estructura base del microservicio SmartLoadPredictor
> **Como** desarrollador de IA,  
> **quiero** tener la estructura base del microservicio de predicción,  
> **para** establecer los cimientos sobre los que se entrenará y desplegará el modelo STLF.

**Criterios de aceptación:**
- [ ] El microservicio SmartLoadPredictorService está creado con FastAPI en Python.
- [ ] Se define la estructura de datos de entrada (historial de consumo, perfil del hogar, datos meteorológicos mock).
- [ ] Se expone un endpoint `/predict` que retorna una respuesta mock (predicción simulada) con el formato final esperado.
- [ ] El servicio se puede ejecutar localmente con Docker.
- [ ] Se incluye documentación Swagger/OpenAPI del servicio.

---

#### HU-16 — Indicadores de confort del usuario
> **Como** usuario,  
> **quiero** definir mis preferencias de confort (horarios de no-interrupción),  
> **para** que el sistema respete mis restricciones al generar recomendaciones de desplazamiento de carga.

**Criterios de aceptación:**
- [ ] El usuario puede definir franjas horarias donde no desea interrupciones (ej. 07:00–09:00 y 18:00–22:00).
- [ ] Las restricciones de confort se almacenan en el perfil del usuario en la base de datos.
- [ ] Se muestra visualmente en el dashboard qué franjas están marcadas como de no-interrupción.
- [ ] Las restricciones son editables en cualquier momento.

---

**Entregables Sprint 2:**
- Dashboard funcional en Angular con datos mock
- Mock de contador y tarifas integrado
- Estructura base del microservicio SmartLoadPredictor (FastAPI)
- Primera versión local de la aplicación completa (backend + frontend)
- Informe de pruebas iniciales

---

> ⏸️ **PAUSA — Tiempo Libre: mediados de abril a finales de agosto 2026**

---

## Sprint 3 — Modelo STLF y Predictor de Carga
**Fechas:** 01 sep – 19 sep 2026  
**Objetivo:** Entrenar el modelo de predicción de carga de corto plazo (STLF) con datos históricos y desplegarlo como microservicio contenedorizado.

### Historias de Usuario

#### HU-17 — Actualización de arquitectura post-pausa
> **Como** equipo de desarrollo,  
> **quiero** revisar y actualizar la arquitectura del sistema,  
> **para** incorporar aprendizajes de los sprints anteriores y asegurar la coherencia técnica antes de continuar.

**Criterios de aceptación:**
- [ ] Se revisa el documento de arquitectura y se actualizan los diagramas si hubo cambios.
- [ ] Se actualiza el Product Backlog en Jira con refinamiento de historias restantes.
- [ ] Se confirman las tecnologías definitivas para el módulo de IA (FastAPI + modelo LSTM/CNN-LSTM).
- [ ] Se documenta la decisión sobre mensajería asíncrona (Kafka vs Azure EventHub).

---

#### HU-18 — Entrenamiento del modelo STLF (predicción de carga)
> **Como** sistema de IA,  
> **quiero** un modelo entrenado de predicción de carga de corto plazo (STLF),  
> **para** anticipar el consumo energético del hogar para las próximas 24 horas.

**Criterios de aceptación:**
- [ ] El modelo es entrenado con datos históricos de consumo por hogar (dataset público o sintético de al menos 6 meses).
- [ ] Se implementa una arquitectura LSTM o CNN-LSTM en Python (TensorFlow/PyTorch).
- [ ] El modelo alcanza un MAPE (Mean Absolute Percentage Error) menor al 15% en el conjunto de validación.
- [ ] El modelo entrenado se serializa en formato ONNX o .pkl para su despliegue.
- [ ] Se genera un reporte de métricas de entrenamiento (loss, MAPE, MAE).

---

#### HU-19 — Microservicio de predicción contenedorizado
> **Como** arquitecto del sistema,  
> **quiero** el SmartLoadPredictorService contenedorizado con Docker,  
> **para** que pueda ser desplegado de forma reproducible en cualquier entorno.

**Criterios de aceptación:**
- [ ] El Dockerfile del servicio FastAPI está optimizado (imagen base ligera, sin dependencias innecesarias).
- [ ] El contenedor expone el endpoint `/predict` con el modelo STLF real (no mock).
- [ ] Se puede ejecutar con `docker-compose` en entorno local junto con HarmoniWattsService.
- [ ] El servicio responde en menos de 2 segundos para una predicción de 24 horas.
- [ ] Se incluyen pruebas de integración para el endpoint de predicción.

---

#### HU-20 — Integración del predictor en el dashboard
> **Como** usuario,  
> **quiero** ver en el dashboard la predicción de mi consumo para las próximas horas,  
> **para** poder planificar el uso de mis electrodomésticos de mayor consumo.

**Criterios de aceptación:**
- [ ] El dashboard muestra un gráfico de predicción de consumo para las próximas 24 horas.
- [ ] La predicción se diferencia visualmente del consumo histórico (real vs. predicho).
- [ ] Se muestra el costo estimado de la predicción según las tarifas TOU vigentes.
- [ ] La predicción se actualiza automáticamente cada hora.

---

#### HU-21 — Mejoras al dashboard: precio vs. consumo
> **Como** usuario,  
> **quiero** una vista mejorada que correlacione el precio de la tarifa con mi consumo en tiempo real,  
> **para** identificar visualmente cuándo estoy consumiendo energía en los momentos más caros.

**Criterios de aceptación:**
- [ ] El dashboard muestra una gráfica dual con el consumo (kWh) y el precio ($/kWh) superpuestos en el tiempo.
- [ ] Se resaltan visualmente los períodos donde el consumo coincide con tarifas de punta.
- [ ] Se calcula y muestra el "costo de oportunidad" de no desplazar cargas a horas valle.

---

**Entregables Sprint 3:**
- Modelo STLF entrenado localmente
- Microservicio de IA funcional en entorno local (contenedorizado)
- Dashboard mejorado con visualización de predicción
- Actualización del Product Backlog y modelos

---

## Sprint 4 — Tarifas Reales, Módulo de Análisis de Oportunidad y UX
**Fechas:** 22 sep – 10 oct 2026  
**Objetivo:** Integrar señales de precio reales de operadores colombianos y desarrollar el módulo de análisis de oportunidad.

### Historias de Usuario

#### HU-22 — Integración con tarifas reales colombianas (CREG/UPME)
> **Como** sistema HEMS,  
> **quiero** consumir datos de tarifas eléctricas reales de operadores colombianos,  
> **para** proporcionar recomendaciones basadas en precios reales y no en datos simulados.

**Criterios de aceptación:**
- [ ] Se integra al menos una fuente de datos real de tarifas horarias (EPM, Enel-Codensa, Celsia o API CREG/UPME si disponible).
- [ ] Si la API no está disponible, se implementa un scraper o ingesta periódica de la información publicada en los sitios oficiales.
- [ ] Los datos de tarifas reales se almacenan en la base de datos con vigencia temporal.
- [ ] El sistema actualiza las tarifas al menos una vez al día de forma automática.
- [ ] Se mantiene un historial de tarifas para análisis retrospectivo.

---

#### HU-23 — Módulo de análisis de oportunidad
> **Como** sistema de IA,  
> **quiero** identificar automáticamente las ventanas de oportunidad y períodos críticos para el usuario,  
> **para** generar recomendaciones personalizadas sobre cuándo consumir energía de forma más económica.

**Criterios de aceptación:**
- [ ] El módulo cruza el perfil de consumo del hogar con las señales de precio TOU/RTP.
- [ ] Se identifican y priorizan automáticamente las franjas valle (bajo precio) y punta (alto precio) del día.
- [ ] El módulo genera al menos 3 recomendaciones de oportunidad diarias por usuario.
- [ ] Las recomendaciones están personalizadas según los electrodomésticos y restricciones de confort del usuario.
- [ ] Las oportunidades identificadas se almacenan para trazabilidad y análisis de efectividad.

---

#### HU-24 — Sistema de alertas y notificaciones
> **Como** usuario,  
> **quiero** recibir alertas cuando se acerque un período de tarifa alta o una ventana de oportunidad,  
> **para** poder actuar a tiempo y desplazar el uso de mis electrodomésticos.

**Criterios de aceptación:**
- [ ] El sistema envía notificaciones push/web cuando comienza una franja de tarifa punta (con 30 min de anticipación).
- [ ] El sistema envía notificaciones cuando hay una ventana de oportunidad de tarifa valle.
- [ ] El usuario puede configurar qué tipos de alertas desea recibir y en qué horarios.
- [ ] Las notificaciones incluyen el ahorro potencial estimado si se actúa según la recomendación.

---

#### HU-25 — Mejoras de UX: visualización de horarios y franjas TOU
> **Como** usuario,  
> **quiero** una interfaz mejorada para ver y gestionar los horarios de mis electrodomésticos según las franjas TOU,  
> **para** poder planificar mi consumo de forma intuitiva y eficiente.

**Criterios de aceptación:**
- [ ] Se implementa una vista de calendario/timeline del día con franjas TOU coloreadas.
- [ ] El usuario puede visualizar qué electrodomésticos están programados en cada franja.
- [ ] La interfaz muestra el costo estimado por franja y el total del día.
- [ ] La UX es validada con al menos una sesión de prueba de usabilidad con un usuario externo.

---

#### HU-26 — Ampliación del backend WebFlux
> **Como** desarrollador backend,  
> **quiero** ampliar los endpoints del microservicio HarmoniWattsService,  
> **para** soportar las nuevas funcionalidades de tarifas, análisis de oportunidad y alertas.

**Criterios de aceptación:**
- [ ] Se implementan endpoints REST para: consulta de tarifas reales, consulta de oportunidades detectadas y gestión de alertas.
- [ ] Todos los endpoints están protegidos con autenticación JWT.
- [ ] Se implementa paginación para endpoints que devuelven colecciones de datos.
- [ ] La cobertura de pruebas unitarias e integración es del 75% o superior.

---

**Entregables Sprint 4:**
- Segunda versión local con tarifas reales, alertas y análisis de oportunidad
- Nuevas historias completadas (tarifas, alertas, análisis)

---

## Sprint 5 — Módulo de Optimización, CI/CD y Primer Despliegue en Cloud
**Fechas:** 13 oct – 31 oct 2026  
**Objetivo:** Desarrollar el módulo de optimización con restricciones de confort, configurar CI/CD y realizar el primer despliegue en Azure Kubernetes Service (AKS).

### Historias de Usuario

#### HU-27 — Módulo de optimización con restricciones de confort
> **Como** sistema de IA,  
> **quiero** un módulo de optimización que genere el plan horario óptimo para los electrodomésticos desplazables,  
> **para** minimizar el costo total de electricidad respetando las restricciones de confort del usuario.

**Criterios de aceptación:**
- [ ] El módulo toma como entrada: predicción de consumo, tarifas TOU/RTP del día, perfil de electrodomésticos y restricciones de confort.
- [ ] Se implementa un algoritmo de optimización (programación lineal, heurística o metaheurística) para la planificación de cargas desplazables.
- [ ] El plan generado respeta en un 100% las franjas de no-interrupción definidas por el usuario.
- [ ] El plan optimizado reduce el costo estimado del día al menos un 10% respecto al escenario sin optimización.
- [ ] El módulo genera un reporte de ahorro potencial con el plan sugerido.

---

#### HU-28 — Recomendaciones contextuales accionables
> **Como** usuario,  
> **quiero** recibir recomendaciones claras y accionables sobre cuándo usar mis electrodomésticos,  
> **para** implementar fácilmente el plan de optimización sin necesidad de entender la lógica interna.

**Criterios de aceptación:**
- [ ] El sistema genera al menos 3 recomendaciones diarias específicas por electrodoméstico (ej. "Encienda la lavadora a las 14:00 para ahorrar $X").
- [ ] Las recomendaciones muestran el ahorro estimado en pesos colombianos (COP).
- [ ] El usuario puede marcar una recomendación como "aplicada" o "ignorada" para retroalimentar el sistema.
- [ ] Las recomendaciones se persisten con su estado para análisis de efectividad.

---

#### HU-29 — Pipeline CI/CD con GitHub Actions o Azure DevOps
> **Como** equipo de desarrollo,  
> **quiero** un pipeline de integración y despliegue continuo,  
> **para** automatizar las pruebas, la construcción de imágenes Docker y el despliegue en AKS.

**Criterios de aceptación:**
- [ ] El pipeline ejecuta automáticamente las pruebas unitarias e integración en cada push a la rama principal.
- [ ] Si las pruebas pasan, el pipeline construye y publica las imágenes Docker en Azure Container Registry (ACR).
- [ ] El pipeline despliega automáticamente en el entorno de desarrollo de AKS si los pasos anteriores son exitosos.
- [ ] El pipeline notifica al equipo (Slack/correo/Teams) sobre el resultado de cada ejecución.

---

#### HU-30 — Empaquetado de servicios en contenedores Docker
> **Como** arquitecto del sistema,  
> **quiero** todos los microservicios empaquetados en contenedores Docker listos para producción,  
> **para** asegurar reproducibilidad, portabilidad y facilidad de despliegue en AKS.

**Criterios de aceptación:**
- [ ] Cada microservicio (HarmoniWatts frontend, HarmoniWattsService, SmartLoadPredictorService) tiene su propio Dockerfile optimizado.
- [ ] Se define un `docker-compose.yml` para ejecutar el sistema completo localmente.
- [ ] Las imágenes Docker no superan los 500MB cada una.
- [ ] Los contenedores incluyen health checks configurados.

---

#### HU-31 — Primer despliegue en AKS (Azure Kubernetes Service)
> **Como** equipo de desarrollo,  
> **quiero** desplegar la primera versión de la aplicación en AKS,  
> **para** validar que la arquitectura cloud funciona correctamente en un entorno real.

**Criterios de aceptación:**
- [ ] Los tres microservicios están desplegados y corriendo en AKS.
- [ ] Se configuran los Kubernetes manifests (Deployments, Services, Ingress, ConfigMaps, Secrets).
- [ ] La aplicación es accesible desde internet a través de una URL pública.
- [ ] Se ejecuta una prueba de humo (smoke test) que valida los flujos principales end-to-end.
- [ ] Se documenta el proceso de despliegue en AKS.

---

**Entregables Sprint 5:**
- Primera versión desplegada en la nube (AKS)
- Pipeline CI/CD configurado y funcional
- Informe de pruebas en AKS
- Microservicios WebFlux + IA funcionando en Azure

---

## Sprint 6 — Integración Completa de Módulos Inteligentes y Aprendizaje Continuo
**Fechas:** 03 nov – 21 nov 2026  
**Objetivo:** Integrar completamente los tres módulos de IA (predicción, análisis y optimización), implementar el aprendizaje continuo y ajustar el rendimiento del sistema.

### Historias de Usuario

#### HU-32 — Integración completa de módulos de IA
> **Como** sistema HEMS,  
> **quiero** que los tres módulos de IA (predicción, análisis de oportunidad y optimización) funcionen de forma integrada y coordinada,  
> **para** que el flujo completo desde la predicción hasta la recomendación sea automático y coherente.

**Criterios de aceptación:**
- [ ] El flujo completo funciona: consumo histórico → predicción STLF → análisis de oportunidad → plan de optimización → recomendaciones al usuario.
- [ ] Los tres módulos se comunican a través de la API de HarmoniWattsService sin acoplamiento directo.
- [ ] El tiempo de respuesta del flujo completo (desde solicitud hasta recomendación) es menor a 5 segundos.
- [ ] Se implementa manejo de errores y fallback si algún módulo de IA no está disponible.

---

#### HU-33 — Implementación de aprendizaje continuo
> **Como** sistema de IA,  
> **quiero** mejorar mis predicciones y recomendaciones conforme acumulo más datos de consumo y retroalimentación del usuario,  
> **para** ofrecer un servicio cada vez más preciso y personalizado.

**Criterios de aceptación:**
- [ ] El modelo STLF se re-entrena automáticamente con los nuevos datos de consumo acumulados (frecuencia semanal o por umbral de datos nuevos).
- [ ] Las respuestas del usuario a las recomendaciones (aplicada/ignorada) se utilizan para ajustar las futuras recomendaciones.
- [ ] Se implementa un mecanismo de versionado del modelo para evitar regresiones.
- [ ] El sistema registra las métricas de precisión del modelo después de cada re-entrenamiento.

---

#### HU-34 — Ajustes de rendimiento: caching y autoscaling
> **Como** arquitecto del sistema,  
> **quiero** implementar estrategias de caching y autoscaling en AKS,  
> **para** asegurar que la aplicación responde eficientemente bajo carga y optimiza el uso de recursos cloud.

**Criterios de aceptación:**
- [ ] Se implementa caching (Redis o cache en memoria) para las consultas de tarifas y predicciones frecuentes.
- [ ] Se configura el Horizontal Pod Autoscaler (HPA) en AKS para los microservicios críticos.
- [ ] Las respuestas de endpoints cacheados tienen un tiempo de respuesta menor a 200ms.
- [ ] Se prueba el autoscaling con una prueba de carga que simula al menos 100 usuarios concurrentes.

---

#### HU-35 — Validación funcional end-to-end
> **Como** equipo de QA,  
> **quiero** ejecutar pruebas de validación funcional end-to-end de toda la aplicación,  
> **para** confirmar que todos los flujos principales funcionan correctamente en el entorno cloud.

**Criterios de aceptación:**
- [ ] Se ejecutan pruebas E2E automatizadas para los flujos: registro → perfil → dashboard → recomendación → confirmación.
- [ ] Al menos el 90% de los casos de prueba definidos pasan exitosamente.
- [ ] Se documentan y priorizan los defectos encontrados.
- [ ] Los defectos críticos y de alta prioridad son resueltos dentro del sprint.

---

**Entregables Sprint 6:**
- Versión de la aplicación con todos los servicios inteligentes integrados
- Aprendizaje continuo implementado
- Validación funcional end-to-end completada

---

## Sprint 7 — Pruebas Avanzadas, Refactor y Despliegue Robusto
**Fechas:** 24 nov – 12 dic 2026  
**Objetivo:** Ejecutar pruebas avanzadas de rendimiento, carga y estrés; realizar refactoring final y asegurar un despliegue robusto en AKS.

### Historias de Usuario

#### HU-36 — Pruebas de rendimiento, carga y estrés
> **Como** equipo de calidad,  
> **quiero** ejecutar pruebas avanzadas de rendimiento, carga y estrés sobre la aplicación en AKS,  
> **para** identificar cuellos de botella, puntos de falla y garantizar la estabilidad bajo condiciones extremas.

**Criterios de aceptación:**
- [ ] Se ejecutan pruebas de carga con al menos 500 usuarios concurrentes usando JMeter, Gatling o k6.
- [ ] Los tiempos de respuesta del 95° percentil son menores a 3 segundos bajo carga normal.
- [ ] Se identifican y documentan los cuellos de botella encontrados.
- [ ] El sistema no presenta fallos ni pérdidas de datos bajo pruebas de estrés del 200% de la carga esperada.
- [ ] El informe de pruebas incluye gráficas de throughput, latencia y tasa de errores.

---

#### HU-37 — Refactoring y optimización final del código
> **Como** equipo de desarrollo,  
> **quiero** realizar un refactoring del código para mejorar legibilidad, mantenibilidad y rendimiento,  
> **para** entregar un producto final con calidad de código profesional.

**Criterios de aceptación:**
- [ ] Se elimina el código duplicado y se aplican principios SOLID en los microservicios.
- [ ] La cobertura de pruebas unitarias es del 80% o superior en todos los microservicios.
- [ ] Se resuelven todos los issues de deuda técnica crítica y alta identificados en SonarQube o herramienta similar.
- [ ] El código pasa revisión de código por ambos integrantes del equipo.

---

#### HU-38 — Despliegue robusto en AKS con alta disponibilidad
> **Como** arquitecto del sistema,  
> **quiero** un despliegue en AKS con configuración de alta disponibilidad,  
> **para** asegurar que la aplicación sea resiliente a fallos de nodos o pods.

**Criterios de aceptación:**
- [ ] Se configura al menos 2 réplicas de cada microservicio crítico en AKS.
- [ ] Se implementan liveness probes y readiness probes en todos los servicios.
- [ ] Se configura un proceso de rolling update para despliegues sin downtime.
- [ ] Se prueba la recuperación automática ante fallo de un pod (el sistema se recupera en menos de 60 segundos).
- [ ] Se configura monitoreo y alertas en Azure Monitor / Application Insights.

---

#### HU-39 — Revisión de artefactos técnicos
> **Como** equipo de desarrollo,  
> **quiero** revisar todos los artefactos técnicos del proyecto,  
> **para** asegurar que están completos, actualizados y listos para la entrega final.

**Criterios de aceptación:**
- [ ] El diagrama de arquitectura final refleja el estado real del sistema desplegado.
- [ ] Los diagramas BPM, de secuencia y de componentes están actualizados.
- [ ] El Product Backlog en Jira muestra el estado final de todas las historias (completadas/pendientes).
- [ ] Los repositorios de código tienen README completos y el historial de commits es limpio.

---

**Entregables Sprint 7:**
- Versión estable desplegada en la nube y probada
- Informe de pruebas avanzadas (rendimiento, carga, estrés)
- Ajustes finales a modelos de IA y backend
- Código refactorizado con alta cobertura de pruebas

---

## Sprint 8 — Documentación Final, Pruebas Finales y Entrega
**Fechas:** 15 dic – 31 dic 2026  
**Objetivo:** Generar toda la documentación final del proyecto, ejecutar pruebas finales de aceptación y preparar la versión definitiva para entrega y sustentación.

### Historias de Usuario

#### HU-40 — Manual de usuario
> **Como** usuario final de HarmoniWatts,  
> **quiero** un manual de usuario completo y comprensible,  
> **para** poder utilizar todas las funcionalidades de la aplicación de forma autónoma.

**Criterios de aceptación:**
- [ ] El manual cubre todos los módulos funcionales: registro, perfil, dashboard, tarifas, recomendaciones y alertas.
- [ ] Incluye capturas de pantalla reales de la aplicación desplegada.
- [ ] El manual está escrito en lenguaje no técnico, accesible para usuarios sin conocimientos de sistemas.
- [ ] Se entrega en formato PDF y versión online (GitHub Pages o similar).

---

#### HU-41 — Manual técnico y de arquitectura
> **Como** equipo técnico receptor del proyecto,  
> **quiero** un manual técnico detallado,  
> **para** entender la arquitectura, configurar, desplegar y mantener el sistema HarmoniWatts.

**Criterios de aceptación:**
- [ ] El manual incluye: descripción de la arquitectura, instrucciones de instalación y configuración, guía de despliegue en AKS, descripción de APIs (Swagger/OpenAPI), estructura de la base de datos y guía de los modelos de IA.
- [ ] Las instrucciones de despliegue han sido verificadas por un integrante diferente al que las escribió.
- [ ] El manual incluye un diagrama de arquitectura final actualizado.

---

#### HU-42 — Reporte de pruebas completo
> **Como** director del proyecto de grado,  
> **quiero** un reporte completo de todas las pruebas realizadas,  
> **para** evaluar la calidad y robustez del sistema entregado.

**Criterios de aceptación:**
- [ ] El reporte incluye: pruebas unitarias, de integración, end-to-end, de rendimiento, carga y estrés.
- [ ] Se documentan los resultados, hallazgos, defectos encontrados y cómo fueron resueltos.
- [ ] El reporte incluye las métricas de cobertura de pruebas por microservicio.
- [ ] Se incluye evidencia (capturas, logs) de las pruebas en entorno cloud.

---

#### HU-43 — Pruebas finales de aceptación (UAT)
> **Como** Product Owner,  
> **quiero** ejecutar pruebas finales de aceptación del usuario (UAT),  
> **para** confirmar que el sistema cumple con todos los criterios de aceptación y los objetivos del proyecto.

**Criterios de aceptación:**
- [ ] Se ejecuta el checklist completo de criterios de aceptación de todas las historias de usuario.
- [ ] El sistema cumple el 95% o más de los criterios de aceptación definidos.
- [ ] Los criterios no cumplidos están documentados con su justificación y plan de mitigación.
- [ ] El Product Owner firma el acta de aceptación del producto.

---

#### HU-44 — Retrospectiva global y lecciones aprendidas
> **Como** equipo de desarrollo,  
> **quiero** documentar las lecciones aprendidas de todo el proyecto,  
> **para** contribuir al conocimiento organizacional y mejorar futuros proyectos similares.

**Criterios de aceptación:**
- [ ] El documento incluye: qué salió bien, qué se puede mejorar y acciones concretas para futuros proyectos.
- [ ] Se registra el velocity promedio del equipo por sprint.
- [ ] Se documenta la evolución del Product Backlog y los cambios de alcance.

---

#### HU-45 — Preparación de entrega y sustentación
> **Como** equipo de desarrollo,  
> **quiero** preparar todos los materiales para la sustentación del proyecto de grado,  
> **para** presentar de forma clara y convincente los resultados, metodología y aportes de HarmoniWatts.

**Criterios de aceptación:**
- [ ] Se prepara una presentación de al menos 20 diapositivas que cubre: contexto, problema, solución, arquitectura, demo en vivo, resultados y conclusiones.
- [ ] Se ensaya la presentación al menos 2 veces con el equipo completo.
- [ ] La demo en vivo del sistema funciona correctamente en el entorno cloud.
- [ ] Todos los artefactos del proyecto están organizados y accesibles en el repositorio final.

---

**Entregables Sprint 8:**
- Versión final desplegada en la nube
- Manual de usuario
- Manual técnico y de arquitectura
- Reporte final de pruebas completo
- Retrospectiva global y lecciones aprendidas
- Presentación para sustentación

---

## Resumen de Historias de Usuario por Sprint

| Sprint | HU | Título | Story Points |
|--------|----|--------|-------------|
| S0 | HU-01 | Sesión de visión del producto | 3 |
| S0 | HU-02 | Product Backlog en Jira | 5 |
| S0 | HU-03 | Modelado BPM | 5 |
| S0 | HU-04 | Diseño de arquitectura | 8 |
| S0 | HU-05 | Prototipos de UI (mockups) | 5 |
| S0 | HU-06 | Release Plan oficial | 3 |
| S1 | HU-07 | Registro de usuario | 5 |
| S1 | HU-08 | Autenticación (Login/JWT) | 8 |
| S1 | HU-09 | Perfil de vivienda y electrodomésticos | 5 |
| S1 | HU-10 | Integración Azure SQL | 8 |
| S1 | HU-11 | Proyecto Angular y navegación | 5 |
| S2 | HU-12 | Dashboard de consumo | 8 |
| S2 | HU-13 | Mock de contador inteligente | 5 |
| S2 | HU-14 | Visualización de tarifas TOU/RTP (mock) | 5 |
| S2 | HU-15 | Estructura base SmartLoadPredictor | 8 |
| S2 | HU-16 | Indicadores de confort | 3 |
| S3 | HU-17 | Actualización de arquitectura post-pausa | 3 |
| S3 | HU-18 | Entrenamiento modelo STLF | 13 |
| S3 | HU-19 | Microservicio predictor contenedorizado | 8 |
| S3 | HU-20 | Integración predictor en dashboard | 5 |
| S3 | HU-21 | Dashboard mejorado: precio vs. consumo | 5 |
| S4 | HU-22 | Tarifas reales colombianas | 8 |
| S4 | HU-23 | Módulo de análisis de oportunidad | 13 |
| S4 | HU-24 | Sistema de alertas y notificaciones | 8 |
| S4 | HU-25 | Mejoras UX: franjas TOU | 5 |
| S4 | HU-26 | Ampliación backend WebFlux | 8 |
| S5 | HU-27 | Módulo de optimización con confort | 13 |
| S5 | HU-28 | Recomendaciones accionables | 8 |
| S5 | HU-29 | Pipeline CI/CD | 8 |
| S5 | HU-30 | Empaquetado Docker | 5 |
| S5 | HU-31 | Primer despliegue en AKS | 8 |
| S6 | HU-32 | Integración completa módulos IA | 13 |
| S6 | HU-33 | Aprendizaje continuo | 8 |
| S6 | HU-34 | Caching y autoscaling | 8 |
| S6 | HU-35 | Validación funcional E2E | 8 |
| S7 | HU-36 | Pruebas de rendimiento y carga | 8 |
| S7 | HU-37 | Refactoring y optimización | 8 |
| S7 | HU-38 | Despliegue robusto AKS | 8 |
| S7 | HU-39 | Revisión de artefactos técnicos | 5 |
| S8 | HU-40 | Manual de usuario | 5 |
| S8 | HU-41 | Manual técnico y arquitectura | 8 |
| S8 | HU-42 | Reporte de pruebas completo | 5 |
| S8 | HU-43 | Pruebas finales de aceptación (UAT) | 8 |
| S8 | HU-44 | Retrospectiva global | 3 |
| S8 | HU-45 | Preparación para sustentación | 5 |

**Total Story Points estimados: ~330 SP**

---

## Definition of Done (DoD) — Global del Proyecto

Para que una historia de usuario sea considerada **terminada (Done)**, debe cumplir:

- [ ] El código está revisado por al menos un integrante del equipo (code review).
- [ ] Las pruebas unitarias pasan con cobertura mínima del 70%.
- [ ] Los criterios de aceptación de la historia están todos verificados.
- [ ] El código está integrado en la rama principal (main/master).
- [ ] El pipeline CI/CD pasa sin errores (desde Sprint 5 en adelante).
- [ ] La funcionalidad es demostrable en la Sprint Review.
- [ ] No hay defectos abiertos de severidad crítica o alta asociados a la historia.

## Definition of Ready (DoR) — Global del Proyecto

Para que una historia de usuario pueda entrar al sprint, debe:

- [ ] Estar estimada en Story Points por el equipo.
- [ ] Tener criterios de aceptación claros y verificables.
- [ ] No tener dependencias bloqueantes sin resolver.
- [ ] Ser lo suficientemente pequeña para completarse en un sprint.
