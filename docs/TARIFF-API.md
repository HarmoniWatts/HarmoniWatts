# Contrato REST — Tariff Service HarmoniWatts

Documento de referencia para proponer e implementar la API del **tariff-service** (tarifas activas, históricas, extracción desde comercializadoras y administración de asignaciones). Complementa la visión de [ARQUITECTURA-HarmoniWatts.md](ARQUITECTURA-HarmoniWatts.md).

---

## 1. Por qué varios endpoints (alineación con SOLID)

| Principio | Cómo ayuda este diseño |
|-----------|-------------------------|
| **S — Single Responsibility** | Cada recurso HTTP responde a **una razón de cambio**: tarifas activas (consultas del presente), históricas (análisis del pasado), extracción (ingesta desde fuentes externas), administración (CRUD y asignación). Evolucionan y se versionan por separado. |
| **O — Open/Closed** | Nuevos tipos de tarifas, comercializadoras o formatos de extracción se añaden como nuevos endpoints o nuevos campos, sin romper a los consumidores existentes. |
| **I — Interface Segregation** | El dashboard o orquestador consume solo `current`, `daily-bands` y `current-franja`; el módulo de análisis consume solo `historical/*`; el panel administrativo consume `extraction/*`. |
| **D — Dependency Inversion** | El dominio expone **casos de uso** acotados (repositorio + servicios). Los adaptadores REST implementan cortes estables. La lógica de negocio (selección de tipo de tarifa con `TarifaSelector`, detección de franja alta con `AlertaTarifaService`) vive en servicios, no en los controladores. |

La UI puede llamar los recursos de **activas** en paralelo; los de **históricas** solo cuando se abre el módulo de análisis; los de **extracción** solo desde el panel administrativo.

### Dependencias internas del servicio

| Componente | Responsabilidad |
|------------|-----------------|
| `TarifaRepository` | Acceso a datos de tarifas, períodos, valores, componentes y configuraciones horarias. |
| `ClienteRepository` | Obtención de datos del cliente (comercializadora, mercado, nivel, estrato, CS). |
| `TarifaSelector` | Selección del tipo de tarifa (A, B, C, D) según reglas CREG 119/2007 y consumo del cliente. |
| `TarifaActivaService` | Lógica de tarifa vigente completa. |
| `FranjaService` | Lógica de precios por hora y franja actual. |
| `AlertaTarifaService` | Detección de ventanas de alta tarifa. |
| `ExtractionService` | Pipeline de extracción de PDFs y persistencia. |
| `ExtractionStateStore` | Seguimiento del estado de las extracciones en background. |

---

## 2. Convenciones generales

| Aspecto | Convención |
|---------|------------|
| **Prefijo** | `/api/v1` (versionado explícito; cambios incompatibles → `/api/v2`). |
| **Formato** | JSON; `Content-Type: application/json`. |
| **Autenticación** | `Authorization: Bearer <access_token>` (JWT emitido por el auth-service). **⚠️ Actualmente comentado en el código; pendiente de activar.** |
| **Ámbito cliente** | El `id_cliente` se deriva del JWT (`sub`). Los endpoints que reciben `id_cliente` en la ruta deben validar que coincida con el del token (403 si no). **⚠️ Validación pendiente de activar.** |
| **Fecha de negocio** | Query `fecha` con formato **`YYYY-MM-DD`** en la zona horaria del cliente (`America/Bogota`). Si se omite, el backend interpreta **“hoy”** según esa TZ. |
| **Consumo mensual** | Query `consumo_mensual_kwh` (opcional) para determinar el tipo de tarifa (A, B, C, D) según reglas CREG. Si se omite, se asume consumo = CS. |
| **Unidades** | Energía en **kWh** (número decimal). Dinero en **COP** (número decimal). Precio unitario en **COP/kWh**. |
| **Timezones** | Todas las fechas/horas en la respuesta incluyen TZ (`America/Bogota`). |
| **Paginación** | Endpoints que devuelven listas usan `limit` y `offset`. Respuesta incluye `total`, `limit`, `offset`. |
| **Errores** | Cuerpo JSON común recomendado: `{ "code": "...", "message": "...", "details": {} }`. Códigos HTTP: `400` validación, `401` no autenticado, `403` sin acceso al recurso/cliente, `404` recurso no encontrado, `422` fecha u operación no aplicable, `500` error interno, `503` dependencia no disponible. |

---

## 3. Endpoints — Tarifas Activas

### 3.1. Tarifa vigente completa del cliente

**`GET /api/v1/tariff/active/current/{id_cliente}`**

Entrega la tarifa activa del cliente, incluyendo cabecera, período vigente, valores por hora, monomia y componentes del CU.

**Path parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `id_cliente` | Sí | ID del cliente (debe coincidir con el del JWT). |

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `fecha` | No | Día a consultar (`YYYY-MM-DD`). Default: hoy (TZ cliente). |
| `consumo_mensual_kwh` | No | Consumo mensual en kWh. Se usa para determinar el tipo de tarifa (A, B, C, D) según reglas CREG. Si se omite, se asume consumo = CS. |

**Respuesta `200 OK`**

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
  "cod_configuracion_horaria": "CH00",
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
    { "cod_componente": "Gm",  "valor": 425.57 },
    { "cod_componente": "PRm", "valor": 75.17 },
    { "cod_componente": "Rm",  "valor": 7.10 },
    { "cod_componente": "Tm",  "valor": 54.27 },
    { "cod_componente": "Cfmj","valor": 8839.00 }
  ]
}```

**Notas**

- El código de franja `(F1...F8)` es dependiente del comercializador.

---

### 3.2. Precios de las 24 horas del día

**`GET /api/v1/tariff/active/daily-bands/{id_cliente}`**

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `fecha` | No | Día (`YYYY-MM-DD`). Default: hoy. |
| `consumo_mensual_kwh` | No | Consumo mensual en kWh (para determinar el tipo de tarifa). |

**Respuesta `200 OK`**

```json
{
  "id_cliente": 4,
  "fecha": "2024-04-10",
  "precios": [
    { "hora": 1, "codigo_franja": "F1", "tipo_hora": "VALLE", "precio": 854.38, "unidad": "COP/kWh" },
    { "hora": 2, "codigo_franja": "F1", "tipo_hora": "VALLE", "precio": 854.38, "unidad": "COP/kWh" },
    { "hora": 24, "codigo_franja": "F1", "tipo_hora": "VALLE", "precio": 854.38, "unidad": "COP/kWh" }
  ],
  "monomia": null
}
```

**Notas**

- Siempre devuelve 24 elementos (hora 1..24)
- Hora 1 = 00:00–01:00; hora 24 = 23:00–24:00

---

### 3.3. Franja horaria actual y su precio

**`GET /api/v1/tariff/active/current-franja/{id_cliente}`**

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `hora` | No | Hora específica (1-24). Default: hora actual. |

**Respuesta `200 OK`**

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

**Acciones sobre un ítem** (contrato opcional; puede vivir fuera de “dashboard” si se prefiere):

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/v1/recommendations/{id}/apply` | Registrar aceptación / orquestar acción. |
| `POST` | `/api/v1/recommendations/{id}/dismiss` | Descartar sin aplicar. |

Así el **listado** sigue siendo de solo lectura y las transiciones de estado tienen recursos propios (S de SOLID).

---

### 3.4. Próxima ventana de alta tarifa

**`GET /api/v1/tariff/active/high-franja/{id_cliente}`**

Detecta la próxima ventana horaria de alta tarifa en un horizonte dado.

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `horizonte_horas` | No | Horas a futuro (1-24). Default: 12. |
| `umbral_pico` | No | `true` = solo franjas PICO; `false` = mayor precio del horizonte. Default: true. |
| `consumo_mensual_kwh` | No | Consumo mensual en kWh. |

**Respuesta `200 OK`** (con franja detectada)

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

**Respuesta `200 OK`** (sin franja)

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

---

## 4. Endpoints — Extracción desde Comercializadora

### 4.1. Extracción manual (por rango de fechas)

**`POST /api/v1/tariff/extraction/manual`**

**Body (JSON)**

```json
{
  "comercializadora_cod": "ENERTOTAL",
  "fecha_inicio": "2024-01-01",
  "fecha_fin": "2024-01-31",
  "urls_pdf": null
}```

**Respuesta 200 OK**

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
}```

### 4.2. Consultar estado de una extracción

**`GET /api/v1/tariff/extraction/estado/{id_extraccion}`**


**Respuesta 200 OK**

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
}```

**Notas**
- Estados posibles: pendiente, en_proceso, completado, error
---

## 5. Endpoints — Tarifas Históricas

### 5.1. Tarifas de un mes

**`GET /api/v1/tariff/historical/{anio}/{mes}`**

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `comercializadora` | No | Filtrar por comercializadora. |
| `mercado` | No | Filtrar por mercado. |
| `nivel` | No | Filtrar por nivel de tensión. |
| `tipo_tarifa` | No | Filtrar por tipo de tarifa (A, B, C, D). |

**Respuesta `200 OK`**

```json
{
  "anio": 2025,
  "mes": 10,
  "total_tarifas": 1,
  "tarifas": [
    {
      "codigo": "CALI-N1_1-A",
      "nombre_tarifa": "CALI N1_1 tipo A",
      "cod_comercializadora": "ENERTOTAL",
      "cod_mercado": "CALI",
      "cod_nivel": "N1_1",
      "cod_tipo_tarifa": "A",
      "resolucion_regulatoria": null,
      "numero_version": 1,
      "fecha_inicio": "2025-10-01",
      "fecha_fin": "2025-10-31",
      "fecha_publicacion": null,
      "configuracion_horaria": "CH00",
      "monomia": { "valor": 888.43, "unidad": "COP/kWh", "tipo": "CU" },
      "valores": [
        { "codigo_franja": "F1", "tipo_hora": "VALLE", "valor": 874.09, "unidad": "COP/kWh", "horas": [1, 2, 3, 4, 24] }
      ],
      "componentes": [ { "cod_componente": "Gm", "valor": 387.07 } ]
    }
  ]
}
```

### 5.2. Tendencias de precios

**`GET /api/v1/tariff/historical/trends`**

**Query parameters**

| Parámetro          | Obligatorio | Descripción |
|--------------------|-------------|-------------|
| `mercado`          | Sí          | Código del mercado (ej. META). |
| `nivel`            | Sí          | Código del nivel de tensión (ej. N1_2_1_3). |
| `tipo_tarifa`      | No          | Tipo de tarifa (A, B, C, D). Default: A. |
| `comercializadora` | No          | Código de la comercializadora. |
| `desde`            | No          | Inicio del rango (se usa el mes). Default: 12 meses antes de hasta. |
| `hasta`            | No          | Fin del rango (se usa el mes). Default: último mes publicado. |


**Respuesta `200 OK`**

```json
{
  "cod_comercializadora": "ENERTOTAL",
  "mercado": "META",
  "nivel": "N1_2_1_3",
  "tipo_tarifa": "A",
  "desde": { "anio": 2025, "mes": 1 },
  "hasta": { "anio": 2025, "mes": 4 },
  "unidad": "COP/kWh",
  "serie": [
    { "anio": 2025, "mes": 1, "precio_promedio": 765.08, "precio_min": 745.2, "precio_max": 780.1, "variacion": null, "meses_omitidos": 0, "configuracion": "CH00" }
  ],
  "meses_faltantes": [],
  "tendencia_anual": 1.83,
  "precio_min_12m": 745.2,
  "precio_max_12m": 795.0,
  "advertencias": []
}
```

### 5.3. Comparar dos períodos

**`GET /api/v1/tariff/historical/compare`**

**Query parameters**

| Parámetro          | Obligatorio | Descripción |
|--------------------|-------------|-------------|
| `mercado`          | Sí          | Código del mercado (ej. META). |
| `nivel`            | Sí          | Código del nivel de tensión (ej. N1_2_1_3). |
| `periodo_a`        | Sí          | Formato YYYY-MM |
| `periodo_b`        | Sí          | Formato YYYY-MM |
| `tipo_tarifa`      | No          | Tipo de tarifa (A, B, C, D). Default: A. |
| `comercializadora` | No          | Código de la comercializadora. |


**Respuesta `200 OK`**

```json
{
  "cod_comercializadora": "ENERTOTAL",
  "mercado": "CALI",
  "nivel": "N1_1",
  "tipo_tarifa": "A",
  "periodo_a": { "anio": 2025, "mes": 9, "numero_version": 1 },
  "periodo_b": { "anio": 2025, "mes": 10, "numero_version": 1 },
  "configuracion_a": "CH00",
  "configuracion_b": "CH00",
  "configuracion_distinta": false,
  "unidad": "COP/kWh",
  "precio_promedio_a": 880.12,
  "precio_promedio_b": 888.43,
  "variacion_total": 0.94,
  "variacion_monomia": { "a": 880.0, "b": 888.43, "diferencia": 8.43, "porcentaje": 0.96 },
  "variacion_horas": [ ... ],
  "variacion_tipo_hora": [ ... ],
  "variacion_componentes": [ ... ],
  "advertencias": []
}
```

## 6. Resumen de rutas

| Método | Ruta | Responsabilidad |
|--------|------|-----------------|
| `GET` | `/api/v1/tariff/active/current/{id_cliente}` | Tarifa vigente completa. |
| `GET` | `/api/v1/tariff/active/daily-bands/{id_cliente}` | Precios de 24 horas. |
| `GET` | `/api/v1/tariff/active/current-franja/{id_cliente}` | Franja actual y precio. |
| `GET` | `/api/v1/tariff/active/high-franja/{id_cliente}` | Próxima ventana de alta tarifa. |
| `POST` | `/api/v1/tariff/extraction/manual` | Extracción manual por rango. |
| `GET` | `/api/v1/tariff/extraction/estado/{id}` | Estado de una extracción. |
| `GET` | `/api/v1/tariff/historical/{anio}/{mes}` | Tarifas de un mes. |
| `GET` | `/api/v1/tariff/historical/trends` | Tendencias de precios. |
| `GET` | `/api/v1/tariff/historical/compare` | Comparativa entre períodos. |

*Última actualización: contrato actualizado tras la implementación de active.py, extraction.py y historical.py.*
