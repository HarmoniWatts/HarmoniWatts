# Contrato REST — Tariff Service HarmoniWatts

Documento de referencia para la API del **tariff-service**: tarifas activas, extracción desde comercializadoras y administración de asignaciones. Complementa la visión de [ARQUITECTURA-HarmoniWatts.md](ARQUITECTURA-HarmoniWatts.md).

**Estado de cada endpoint** (columna *Estado* en el resumen de la sección 7):

| Estado | Significado |
|--------|-------------|
| **Implementado** | Existe en el código (`app/api/routes/`) y el contrato describe su comportamiento real. |
| **Planeado** | Parte del diseño objetivo; aún no existe en el código (o está comentado). |

---

## 1. Por qué varios endpoints (alineación con SOLID)

| Principio | Cómo ayuda este diseño |
|-----------|-------------------------|
| **S — Single Responsibility** | Cada recurso HTTP responde a **una razón de cambio**: tarifas activas (consultas del presente), extracción (ingesta desde fuentes externas), administración (CRUD y asignación). Evolucionan y se versionan por separado. |
| **O — Open/Closed** | Nuevos tipos de tarifas, comercializadoras o formatos de extracción se añaden como nuevos endpoints o nuevos campos, sin romper a los consumidores existentes. |
| **I — Interface Segregation** | El dashboard o orquestador consume solo `current`, `daily-bands`, `current-franja` y `high-franja`; el panel administrativo consume `extraction/*` y `admin/*`. |
| **D — Dependency Inversion** | Los routers son **finos**: delegan en servicios (`TarifaActivaService`, `FranjaService`, `AlertaTarifaService`, `ExtractionService`) que reciben repositorios y selectores por inyección (`Depends`). La lógica de negocio (selección de tipo de tarifa, resolución hora→franja, detección de franja alta) vive en los servicios, no en los controladores. |

La UI puede llamar los recursos de **activas** en paralelo; los de **históricas** solo cuando se abre el módulo de análisis; los de **extracción** solo desde el panel administrativo.

---

## 2. Convenciones generales

| Aspecto | Convención |
|---------|------------|
| **Prefijo** | `/api/v1` (versionado explícito; cambios incompatibles → `/api/v2`). Los routers declaran `/tariff/active` y `/tariff/extraction`; el prefijo `/api/v1` se aplica al montarlos en la app. |
| **Formato** | JSON; `Content-Type: application/json`. |
| **Autenticación** | Objetivo: `Authorization: Bearer <access_token>` (JWT del auth-service). El `id_cliente` de la ruta debe coincidir con el del token (`403` si no). **Estado actual:** la validación está comentada en `active.py` (dependencia `get_current_cliente`); hoy cualquier `id_cliente` puede consultarse sin token. Debe habilitarse antes de producción. |
| **Fecha de negocio** | Query `fecha` con formato **`YYYY-MM-DD`** en la zona horaria del cliente (`America/Bogota`). Si se omite, el backend interpreta **“hoy”** según esa TZ. |
| **Unidades** | Energía en **kWh** (decimal). Dinero en **COP** (decimal). Precio unitario en **COP/kWh**. |
| **Consumo mensual** | Todos los endpoints de tarifas activas aceptan el query opcional `consumo_mensual_kwh` (decimal, kWh). Se entrega al `TarifaSelector`, que lo usa para elegir la tarifa aplicable al cliente cuando depende del consumo. Si se omite, el selector aplica su criterio por defecto. |
| **Tipos de hora** | `tipo_hora` toma los valores `VALLE`, `MEDIA`, `PICO`. |
| **Franjas** | `codigo_franja` es `F1`…`F8` y **depende de la comercializadora**. |
| **Timezones** | Las fechas/horas en la respuesta se expresan en `America/Bogota`. |
| **Paginación** | Endpoints que devuelven listas largas usan `limit` y `offset`. Respuesta incluye `total`, `limit`, `offset`. |
| **Errores** | Cuerpo JSON común objetivo: `{ "code": "...", "message": "...", "details": {} }`. Códigos HTTP: `400` validación, `401` no autenticado, `403` sin acceso al recurso/cliente, `404` recurso no encontrado, `409` conflicto, `422` fecha u operación no aplicable, `500` error interno, `503` dependencia no disponible. **Estado actual:** FastAPI responde `{ "detail": "..." }` (y `422` para errores de validación de Pydantic); el formato común requiere un *exception handler* global. |

---

## 3. Endpoints — Tarifas Activas

Todos los endpoints de esta sección son `GET` y comparten estos query parameters opcionales, además de los propios de cada uno:

| Parámetro | Descripción |
|-----------|-------------|
| `consumo_mensual_kwh` | Consumo mensual del cliente en kWh (ver sección 2). |

### 3.1. Tarifa vigente completa del cliente — *Implementado*

**`GET /api/v1/tariff/active/current/{id_cliente}`**

Entrega la tarifa activa del cliente, incluyendo cabecera, período vigente, valor de monomía (si aplica), valores por hora y componentes del CU.

**Path parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|:-----------:|-------------|
| `id_cliente` | Sí | ID del cliente (debe coincidir con el del JWT). |

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|:-----------:|-------------|
| `fecha` | No | Día a consultar (`YYYY-MM-DD`). Default: hoy (TZ cliente). |
| `consumo_mensual_kwh` | No | Consumo mensual en kWh. |

**Respuesta `200 OK`** (`TarifaActivaResponse`)

```json
{
  "id_cliente": 4,
  "fecha_consulta": "2024-04-10",
  "tarifa": {
    "id_tarifa": 3,
    "codigo_tarifa": "CALI_N1_1_A_ENERTOTAL",
    "nombre_tarifa": "Tarifa CALI Nivel 1.1 - tipo A",
    "cod_comercializadora": "ENERTOTAL",
    "cod_mercado": "CALI",
    "cod_nivel": "N1_1",
    "cod_tipo_tarifa": "A",
    "resolucion_regulatoria": "CREG 119/2007, CREG 101/2023"
  },
  "periodo": {
    "id_periodo_tarifario": 3131,
    "anio": 2024,
    "mes": 4,
    "fecha_inicio": "2024-04-01",
    "fecha_fin": "2024-04-30",
    "numero_version": 1,
    "estado": "PUBLICADA",
    "fecha_publicacion": "2024-04-01"
  },
  "monomia": {
    "valor": 854.38,
    "unidad": "COP/kWh",
    "tipo": "CU"
  },
  "valores": [
    {
      "hora": 1,
      "codigo_franja": "F1",
      "tipo_hora": "VALLE",
      "valor": 854.38,
      "unidad": "COP/kWh"
    }
  ],
  "componentes": [
    { "cod_componente": "Cm",  "valor": 48.99 },
    { "cod_componente": "Dm",  "valor": 254.70 },
    { "cod_componente": "Gm",  "valor": 426.57 },
    { "cod_componente": "PRm", "valor": 76.17 },
    { "cod_componente": "Rm",  "valor": 7.10 },
    { "cod_componente": "Tm",  "valor": 54.27 },
    { "cod_componente": "Cfmj","valor": 8839.00 }
  ]
}
```

**Notas**

- `estado` del período: `BORRADOR`, `PUBLICADA`, `SUPERADA`, `ANULADA`.
- `monomia` es **opcional** (`null` cuando la tarifa no tiene valor único). Su `tipo` es `CU` (Costo Unitario) u otro concepto como `CU_BASE`, `CU_APLICADO`.
- `valores` y `componentes` son listas (vacías si no aplican). Un cliente con solo monomía recibe `valores: []` y `monomia` con el valor.
- El código de franja (`F1`…`F8`) depende de la comercializadora.

**Errores**

- `404`: el cliente no tiene tarifa vigente para la fecha.
- `403`: el `id_cliente` no coincide con el del JWT (cuando se habilite la autenticación).

---

### 3.2. Precios de las 24 horas del día — *Implementado*

**`GET /api/v1/tariff/active/daily-bands/{id_cliente}`**

Curva de precios de las 24 horas del día, con franja y tipo, para pintar el gráfico del dashboard.

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|:-----------:|-------------|
| `fecha` | No | Día (`YYYY-MM-DD`). Default: hoy. |
| `consumo_mensual_kwh` | No | Consumo mensual en kWh. |

**Respuesta `200 OK`** (`PreciosDiaResponse`)

```json
{
  "id_cliente": 4,
  "fecha": "2024-04-10",
  "precios": [
    { "hora": 1,  "codigo_franja": "F1", "tipo_hora": "VALLE", "precio": 854.38, "unidad": "COP/kWh" },
    { "hora": 2,  "codigo_franja": "F1", "tipo_hora": "VALLE", "precio": 854.38, "unidad": "COP/kWh" },
    { "hora": 24, "codigo_franja": "F1", "tipo_hora": "VALLE", "precio": 854.38, "unidad": "COP/kWh" }
  ],
  "monomia": {
    "valor": 867.79,
    "unidad": "COP/kWh",
    "tipo": "CU"
  }
}
```

**Notas**

- `precios` trae 24 elementos (hora 1..24) para tarifas con franjas horarias.
- `monomia` es opcional: valor único de referencia (CU sin desglose horario). Puede venir `null`.
- Hora 1 = 00:00–01:00; hora 24 = 23:00–24:00.
- **Comportamiento actual:** si `precios` viene vacío (cliente solo con monomía) el endpoint responde `404`. Pendiente decidir si debe responder `200` con `precios: []` y `monomia` poblada.

**Errores**

- `404`: no se encontraron precios para el cliente.

---

### 3.3. Franja horaria actual y su precio — *Implementado*

**`GET /api/v1/tariff/active/current-franja/{id_cliente}`**

Franja vigente en el instante de la consulta (o en la hora indicada).

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|:-----------:|-------------|
| `hora` | No | Hora específica (entero 1–24). Default: hora actual. Fuera de rango → `422`. |
| `consumo_mensual_kwh` | No | Consumo mensual en kWh. |

**Respuesta `200 OK`** (`FranjaActualResponse`)

```json
{
  "id_cliente": 4,
  "fecha": "2024-04-10",
  "hora_actual": 14,
  "codigo_franja": "F2",
  "tipo_hora": "MEDIA",
  "precio": 867.81,
  "unidad": "COP/kWh"
}
```

**Errores**

- `404`: no se encontró franja actual para el cliente.

---

### 3.4. Próxima ventana de alta tarifa — *Implementado*

**`GET /api/v1/tariff/active/high-franja/{id_cliente}`**

Detecta la próxima ventana horaria de alta tarifa dentro del horizonte (franja PICO o el tramo más caro del día).

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|:-----------:|-------------|
| `horizonte_horas` | No | Horas a futuro (1–24). Default: `12`. |
| `umbral_pico` | No | `true` = solo franjas de tipo `PICO`; `false` = tramo de mayor precio del horizonte. Default: `true`. |
| `consumo_mensual_kwh` | No | Consumo mensual en kWh. |

**Respuesta `200 OK`** (con franja alta detectada) (`ProximaFranjaAltaResponse`)

```json
{
  "id_cliente": 4,
  "fecha": "2024-04-10",
  "hora_actual": 14,
  "hay_franja_alta": true,
  "codigo_franja": "F4",
  "tipo_hora": "PICO",
  "hora_inicio": 19,
  "hora_fin": 21,
  "duracion_horas": 3,
  "precio_max": 877.99,
  "precio_valle_referencia": 854.38,
  "ahorro_potencial": 70.83,
  "unidad": "COP/kWh",
  "mensaje": "Franja de alta tarifa de 3 hora(s) desde las 19:00 hasta las 21:00."
}
```

**Respuesta `200 OK`** (sin franja alta)

```json
{
  "id_cliente": 4,
  "fecha": "2024-04-10",
  "hora_actual": 14,
  "hay_franja_alta": false,
  "mensaje": "No se detectó una franja de alta tarifa en el horizonte"
}
```

**Notas**

- `hora_inicio` y `hora_fin` son horas 1–24 con extremos inclusivos (19→21 = 3 horas).
- `precio_valle_referencia` es el precio mínimo del día.
- `ahorro_potencial` = `(precio_max - precio_valle_referencia) * duracion_horas`.
- Si `hay_franja_alta=false`, los campos de la ventana se omiten o van `null`; `mensaje` siempre está presente.

**Errores**

- `404`: no se pudo analizar las tarifas del cliente.

---

## 4. Endpoints — Extracción desde Comercializadora

Prefijo de ruta: `/api/v1/tariff/extraction`. La extracción es **asíncrona**: el `POST` registra la tarea y responde de inmediato; el cliente consulta el progreso por polling.

### 4.1. Extracción manual (por rango de fechas) — *Implementado*

**`POST /api/v1/tariff/extraction/manual`**

Descarga y procesa PDFs de tarifas de la comercializadora en un rango de fechas. Corre en segundo plano (`BackgroundTasks`).

**Body (JSON)** (`ExtraccionManualRequest`)

```json
{
  "comercializadora_cod": "ENERTOTAL",
  "fecha_inicio": "2024-01-01",
  "fecha_fin": "2024-01-31",
  "urls_pdf": null
}
```

| Campo | Obligatorio | Descripción |
|-------|:-----------:|-------------|
| `comercializadora_cod` | Sí | Código de la comercializadora. |
| `fecha_inicio` | Sí | Inicio del rango (`YYYY-MM-DD`). |
| `fecha_fin` | Sí | Fin del rango (`YYYY-MM-DD`); debe ser ≥ `fecha_inicio`. |
| `urls_pdf` | No | URLs específicas de PDFs. **Actualmente se acepta en el request pero el router no lo envía al servicio.** |

**Respuesta** (`ExtraccionResponse`)

```json
{
  "id_extraccion": "manual_a1b2c3d4",
  "estado": "pendiente",
  "modo": "manual",
  "tarifas_extraidas": 0,
  "tarifas_insertadas": 0,
  "errores": [],
  "fecha_inicio": "2024-01-01",
  "fecha_fin": "2024-01-31",
  "mensaje": "Extracción iniciada en segundo plano"
}
```

**Notas**

- `id_extraccion` = `manual_` + 8 caracteres hexadecimales.
- Código HTTP objetivo: `202 Accepted`. **Actualmente** el decorador no fija `status_code`, por lo que responde `200`.
- El estado se guarda en `ExtractionStateStore` bajo ese `id_extraccion`.

**Errores**

- `422`: `fecha_fin < fecha_inicio` (el validador de Pydantic rechaza el body; FastAPI responde `422`, no `400`).
- `404`: comercializadora no encontrada (objetivo; hoy el error se refleja en el estado `error` de la extracción).

---

### 4.2. Consultar estado de una extracción — *Implementado*

**`GET /api/v1/tariff/extraction/estado/{id_extraccion}`**

El cliente hace polling cada X segundos hasta que el estado sea `completado` o `error`.

**Respuesta `200 OK`** (`ExtraccionResponse`)

```json
{
  "id_extraccion": "manual_a1b2c3d4",
  "estado": "completado",
  "modo": "manual",
  "tarifas_extraidas": 6,
  "tarifas_insertadas": 6,
  "errores": [],
  "fecha_inicio": "2024-01-01",
  "fecha_fin": "2024-01-31",
  "mensaje": "Extracción completada"
}
```

**Estados posibles:** `pendiente`, `en_proceso`, `completado`, `error`.

- En `error`, `errores` contiene el mensaje de la excepción y `mensaje` = `Error: <detalle>`.
- `modo` es `manual` (el enum `ModoExtraccion` también define `automatica`, reservado).

**Errores**

- `404`: `Extracción no encontrada: {id_extraccion}`.

---

## 5. Endpoints — Administración (*Planeado*)

> Ningún endpoint de esta sección existe aún en el código.

### 5.1. Asignar tarifa a un cliente

**`POST /api/v1/tariff/admin/assign`**

Asigna manualmente una tarifa a un cliente.

**Body (JSON)**

```json
{
  "id_cliente": 4,
  "codigo_tarifa": "CALI_N1_1_A_ENERTOTAL",
  "fecha_asignacion": "2024-04-01"
}
```

**Respuesta `200 OK`**

```json
{
  "id_tarifa_usuario": 100,
  "id_cliente": 4,
  "codigo_tarifa": "CALI_N1_1_A_ENERTOTAL",
  "fecha_asignacion": "2024-04-01",
  "activa": true,
  "mensaje": "Tarifa asignada correctamente"
}
```

**Errores**

- `400`: la tarifa no está vigente para la fecha.
- `404`: cliente o tarifa no encontrados.
- `409`: tarifa ya asignada al cliente.

---

### 5.2. Listar comercializadoras

**`GET /api/v1/tariff/admin/comercializadoras`**

**Respuesta `200 OK`**

```json
{
  "total": 2,
  "items": [
    { "cod_comercializadora": "ENERTOTAL", "nombre": "ENERTOTAL S.A. E.S.P.", "nit": "900.039.901-5", "activo": true },
    { "cod_comercializadora": "VATIA",     "nombre": "VATIA S.A.S.",          "nit": "901.234.567-8", "activo": true }
  ]
}
```

---

### 5.3. Listar mercados

**`GET /api/v1/tariff/admin/mercados`**

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|:-----------:|-------------|
| `cod_comercializadora` | No | Filtrar por comercializadora. |

**Respuesta `200 OK`**

```json
{
  "total": 19,
  "items": [
    { "cod_mercado": "CALI", "nombre_mercado": "Mercado EMCALI Cali", "cod_or": "OR_EMCALI", "activo": true }
  ]
}
```

---

## 6. Códigos de error comunes

| Código | Significado | Ejemplo |
|--------|-------------|---------|
| `400` | Validación de entrada | Tarifa no vigente para la fecha de asignación |
| `401` | Token inválido o ausente | Falta `Authorization: Bearer` |
| `403` | Sin permisos | Consultar tarifa de otro cliente |
| `404` | Recurso no encontrado | Cliente/tarifa/extracción no existe |
| `409` | Conflicto | Tarifa ya asignada al cliente |
| `422` | Validación de parámetros o fecha no aplicable | `hora=25`, `fecha_fin < fecha_inicio` |
| `500` | Error interno | Fallo en el pipeline de extracción |
| `503` | Servicio no disponible | Comercializadora caída |

**Formato del error (objetivo):**

```json
{
  "code": "TARIFF_NOT_FOUND",
  "message": "No se encontró tarifa vigente para el cliente 4 en la fecha 2024-04-10",
  "details": {
    "id_cliente": 4,
    "fecha": "2024-04-10"
  }
}
```

**Formato actual (FastAPI por defecto):**

```json
{ "detail": "No se encontró tarifa vigente para el cliente 4" }
```

---

## 7. Resumen de rutas

| Método | Ruta | Responsabilidad | Estado |
|--------|------|-----------------|--------|
| `GET` | `/api/v1/tariff/active/current/{id_cliente}` | Tarifa vigente completa | Implementado |
| `GET` | `/api/v1/tariff/active/daily-bands/{id_cliente}` | Precios de 24 horas | Implementado |
| `GET` | `/api/v1/tariff/active/current-franja/{id_cliente}` | Franja actual y precio | Implementado |
| `GET` | `/api/v1/tariff/active/high-franja/{id_cliente}` | Próxima ventana de alta tarifa | Implementado |
| `POST` | `/api/v1/tariff/extraction/manual` | Extracción manual por rango | Implementado |
| `GET` | `/api/v1/tariff/extraction/estado/{id}` | Estado de una extracción | Implementado |
| `POST` | `/api/v1/tariff/admin/assign` | Asignar tarifa a cliente | Planeado |
| `GET` | `/api/v1/tariff/admin/comercializadoras` | Listar comercializadoras | Planeado |
| `GET` | `/api/v1/tariff/admin/mercados` | Listar mercados | Planeado |

---

## 8. Próximos pasos sugeridos

1. **Habilitar autenticación JWT** en los endpoints de activas (descomentar `get_current_cliente` y la validación `id_cliente`) y proteger `extraction/*` y `admin/*` con rol administrativo.
2. **Alinear códigos de respuesta**: `202 Accepted` en `POST /extraction/manual`; decidir si `daily-bands` devuelve `200` con `precios: []` para clientes solo-monomía en lugar de `404`.
3. **Handler global de errores** para emitir el formato común `{ code, message, details }`.
4. **Publicar OpenAPI 3** (YAML) con los mismos esquemas y enums (`VALLE`, `MEDIA`, `PICO`, `ModoExtraccion`, …). FastAPI ya lo genera en `/openapi.json`; exportarlo al repositorio.
5. **Definir caché** por recurso: `current`, `daily-bands` y `current-franja` pueden usar `Cache-Control: max-age=300` (5 min); `high-franja` depende de la hora actual, por lo que conviene un TTL corto.
6. **Rate limiting** en endpoints de escritura (`extraction/*`, `admin/assign`).
7. **Persistir el estado de extracciones** si `ExtractionStateStore` es en memoria, para que sobreviva a reinicios y a varios workers.
8. **Versionado de la lógica CREG**: cuando cambie la norma, publicar `/api/v2` para `active/current` manteniendo `/api/v1` en modo compatibilidad.
9. **Instrumentar métricas**: latencia por endpoint, tasa de error, frecuencia de extracciones fallidas.

---

*Última actualización: 2026-10-13 — contrato alineado con `active.py`, `extraction.py` y sus esquemas; sección de administración marcada como planeada.*