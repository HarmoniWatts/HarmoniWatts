# Contrato REST — Tariff Service HarmoniWatts

Documento de referencia para proponer e implementar la API del **tariff-service** (tarifas activas, tarifas históricas, extracción desde comercializadoras y administración de asignaciones). Complementa la visión de [ARQUITECTURA-HarmoniWatts.md](ARQUITECTURA-HarmoniWatts.md).

---

## 1. Por qué varios endpoints (alineación con SOLID)

| Principio | Cómo ayuda este diseño |
|-----------|-------------------------|
| **S — Single Responsibility** | Cada recurso HTTP responde a **una razón de cambio**: tarifas activas (consultas del presente), históricas (análisis del pasado), extracción (ingesta desde fuentes externas), administración (CRUD y asignación). Evolucionan y se versionan por separado. |
| **O — Open/Closed** | Nuevos tipos de tarifas, comercializadoras o formatos de extracción se añaden como nuevos endpoints o nuevos campos, sin romper a los consumidores existentes. |
| **I — Interface Segregation** | El dashboard o orquestador consume solo `current`, `daily-bands` y `current-franja`; el módulo de análisis consume solo `historical/*`; el panel administrativo consume `assign` y `sync`. |
| **D — Dependency Inversion** | El dominio expone **casos de uso** acotados (repositorio + servicios). Los adaptadores REST implementan cortes estables. La lógica de negocio (selección de tipo de tarifa, detección de franja alta) vive en servicios, no en los controladores. |

La UI puede llamar los recursos de **activas** en paralelo; los de **históricas** solo cuando se abre el módulo de análisis; los de **extracción** solo desde el panel administrativo.

---

## 2. Convenciones generales

| Aspecto | Convención |
|---------|------------|
| **Prefijo** | `/api/v1` (versionado explícito; cambios incompatibles → `/api/v2`). |
| **Formato** | JSON; `Content-Type: application/json`. |
| **Fecha de negocio** | Query `fecha` con formato **`YYYY-MM-DD`** en la zona horaria del cliente (`America/Bogota`). Si se omite, el backend interpreta **“hoy”** según esa TZ. |
| **Unidades** | Energía en **kWh** (número decimal). Dinero en **COP** (número decimal). Precio unitario en **COP/kWh**. |
| **Timezones** | Todas las fechas/horas en la respuesta incluyen TZ (`America/Bogota`). |
| **Paginación** | Endpoints que devuelven listas usan `limit` y `offset`. Respuesta incluye `total`, `limit`, `offset`. |
| **Errores** | Cuerpo JSON común recomendado: `{ "code": "...", "message": "...", "details": {} }`. Códigos HTTP: `400` validación, `401` no autenticado, `403` sin acceso al recurso/cliente, `404` recurso no encontrado, `422` fecha u operación no aplicable, `500` error interno, `503` dependencia no disponible (p. ej. comercializadora caída). |

---

## 3. Endpoints — Tarifas Activas

### 3.1. Tarifa vigente completa del cliente

**`GET /api/v1/tariff/active/current/{id_cliente}`**

Entrega la tarifa activa del cliente, incluyendo cabecera, período vigente, valores por hora y componentes del CU.

**Path parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `id_cliente` | Sí | ID del cliente (debe coincidir con el del JWT). |

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `fecha` | No | Día a consultar (`YYYY-MM-DD`). Default: hoy (TZ cliente). |

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
  "monomia": 
  {
      "valor": 854.38,
      "unidad": "COP/kWh",
	  "tipo":"CU"
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
}```

**Notas**

- El código de franja `(F1...F8)` es dependiente del comercializador.

---

### 3.2. Precios de las 24 horas del día

**`GET /api/v1/tariff/active/daily-bands/{id_cliente}`**

Curva de precios de las 24 horas del día, con franja y tipo, para pintar el gráfico del dashboard.

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `fecha` | No | Día (`YYYY-MM-DD`). Default: hoy. |

**Respuesta `200 OK`**

```json
{
  "id_cliente": 4,
  "fecha": "2024-04-10",
  "modo_tarifa": "FRANJA_HORARIA",
  "precios": [
    { "hora": 1,  "codigo_franja": "F1", "tipo_hora": "VALLE", "precio": 854.38, "unidad": "COP/kWh" },
    { "hora": 2,  "codigo_franja": "F1", "tipo_hora": "VALLE", "precio": 854.38, "unidad": "COP/kWh" },
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

### 3.4. Top electrodomésticos por consumo

**`GET /api/v1/dashboard/appliances/top`**

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `date` | No | Día de agregación (`YYYY-MM-DD`) o periodo si el negocio lo extiende. |
| `limit` | No | Default recomendado: `5`. |
| `householdId` | Condicional | Igual que en 3.1. |

**Respuesta `200 OK`**

```json
{
  "date": "2026-03-30",
  "metric": "SHARE_OF_DAY",
  "items": [
    {
      "id": "appliance-heater-01",
      "name": "Calentador",
      "category": "WATER_HEATER",
      "sharePercent": 92,
      "consumptionKwh": 4.2
    },
    {
      "id": "appliance-washer-01",
      "name": "Lavadora",
      "category": "WASHER",
      "sharePercent": 76,
      "consumptionKwh": 3.5
    }
  ]
}
```

**Notas**

- `sharePercent`: valor relativo para barras en UI (0–100); puede ser **participación sobre el total del día** u otra métrica siempre que `metric` lo describa.
- `consumptionKwh` opcional si solo se expone ranking relativo.

---

## 4. Resumen de rutas

| Método | Ruta | Responsabilidad |
|--------|------|-----------------|
| `GET` | `/api/v1/insights/summary` | KPIs del día + próxima franja cara. |
| `GET` | `/api/v1/insights/consumption-chart` | Series horarias + franjas para el gráfico. |
| `GET` | `/api/v1/optimization/recommendations` | Lista corta de recomendaciones IA. |
| `GET` | `/api/v1/user/appliances/top` | Top N aparatos por consumo / participación. |

---

## 5. Próximos pasos sugeridos

1. Fijar **multi-vivienda**: query vs path y nombre del parámetro (`householdId` vs `homeId`).
2. Publicar **OpenAPI 3** (YAML) en el repo del API Java 21 con los mismos esquemas y enums (`VALLE`, `MEDIA`, `PUNTA`, …).
3. Definir **caché** (ETag / `Cache-Control`) por recurso: el gráfico y el top pueden cachearse unos minutos; el summary menos si incluye “ahora”.

---

*Última actualización: documento inicial para propuesta de contrato (dashboard, opción B).*
