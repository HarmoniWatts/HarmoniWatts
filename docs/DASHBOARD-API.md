# Contrato REST — Dashboard HarmoniWatts (opción B)

Documento de referencia para proponer e implementar la API que alimenta la **pantalla de dashboard** (KPIs del día, gráfico consumo vs predicción, franjas horarias, recomendaciones IA y top de electrodomésticos). Complementa la visión de [ARQUITECTURA-HarmoniWatts.md](ARQUITECTURA-HarmoniWatts.md).

---

## 1. Por qué varios endpoints (alineación con SOLID)

| Principio | Cómo ayuda la opción B |
|-----------|-------------------------|
| **S — Single Responsibility** | Cada recurso HTTP responde a **una razón de cambio**: resumen de KPIs, serie temporal del gráfico, recomendaciones, ranking de aparatos. Evolucionan y se versionan por separado. |
| **O — Open/Closed** | Nuevos paneles del dashboard pueden añadir endpoints o campos sin inflar un único “mega-DTO” que obligue a redeployar todos los consumidores. |
| **I — Interface Segregation** | El cliente solo consume los contratos que necesita (p. ej. solo KPIs en un widget embebido; gráfico en otro). |
| **D — Dependency Inversion** | El dominio expone **casos de uso** acotados (puertos); cada adaptador REST implementa un corte estable. Los servicios internos (tarifas, medición, predictor) no se acoplan a un único agregado gigante. |

La UI puede seguir llamando los cuatro recursos **en paralelo** al cargar el dashboard para mantener buena experiencia.

---

## 2. Convenciones generales

| Aspecto | Convención |
|---------|------------|
| **Prefijo** | `/api/v1` (versionado explícito; cambios incompatibles → `/api/v2`). |
| **Formato** | JSON; `Content-Type: application/json`. |
| **Autenticación** | `Authorization: Bearer <access_token>` (p. ej. emitido por Keycloak). |
| **Ámbito vivienda** | Si el usuario tiene varias viviendas: `householdId` como query param **o** ruta `/api/v1/households/{householdId}/dashboard/...` (elegir una y documentarla igual en los cuatro recursos). |
| **Fecha de negocio** | Query `date` con formato **`YYYY-MM-DD`** en la zona horaria de la vivienda/usuario. Si se omite, el backend interpreta **“hoy”** según esa TZ. |
| **Unidades** | Energía en **kWh** (número decimal). Dinero en **COP** (entero salvo que se acuerde `string` para grandes montos). |
| **Errores** | Cuerpo JSON común recomendado: `{ "code": "...", "message": "...", "details": {} }`. Códigos HTTP: `400` validación, `401` no autenticado, `403` sin acceso al recurso/vivienda, `404` recurso no encontrado, `422` fecha u operación no aplicable, `503` dependencia no disponible (p. ej. predictor). |

---

## 3. Endpoints

### 3.1. Resumen del día (KPIs)

**`GET /api/v1/dashboard/summary`**

Entrega los indicadores de la franja superior del dashboard y la **próxima ventana de alta tarifa** relevante para la UI.

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `date` | No | Día a consultar (`YYYY-MM-DD`). Default: hoy (TZ vivienda). |
| `householdId` | Condicional | Obligatorio si el modelo multi-vivienda no va en la ruta. |

**Respuesta `200 OK`**

```json
{
  "date": "2026-03-30",
  "timezone": "America/Bogota",
  "consumptionTodayKwh": 12.4,
  "consumptionVsYesterdayPercent": -8.0,
  "estimatedCostTodayCop": 4230,
  "currentTariffSlot": {
    "type": "VALLE",
    "label": "Valle",
    "energyPriceCopPerKwh": 280
  },
  "savingsAccumulatedCop": 18900,
  "savingsPeriod": {
    "label": "Este mes",
    "from": "2026-03-01",
    "to": "2026-03-30"
  },
  "nextHighTariffWindow": {
    "type": "PUNTA",
    "label": "Punta",
    "startsAt": "2026-03-30T18:00:00-05:00",
    "endsAt": "2026-03-30T21:00:00-05:00",
    "displayHint": "Punta en 1h 20min"
  }
}
```

**Notas**

- `consumptionVsYesterdayPercent`: negativo = menos consumo que ayer (coherente con flecha “a la baja” en UI).
- `displayHint` es **texto ya formateado** opcional; el front puede ignorarlo y calcular desde `startsAt` si prefiere.
- `currentTariffSlot` refleja la franja vigente en el instante de la petición (o en el `date` si el negocio fija corte por día).

---

### 3.2. Gráfico consumo vs predicción

**`GET /api/v1/dashboard/consumption-chart`**

Entrega las series horarias del día y metadatos para pintar franjas de fondo y la hora actual.

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `date` | No | Día (`YYYY-MM-DD`). |
| `householdId` | Condicional | Igual que en 3.1. |

**Respuesta `200 OK`**

```json
{
  "date": "2026-03-30",
  "timezone": "America/Bogota",
  "granularity": "HOUR",
  "maxKwhScale": 15.0,
  "hours": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
  "actualKwh": [3.2, 2.8, 2.5, 2.3, 2.5, 3.0, 4.5, 6.8, 8.5, 9.2, 10.0, 10.8, 11.2, 10.5, 9.8, 9.0, 10.5, 12.0, 11.5, 10.0, 8.5, 7.0, 5.5, 4.0],
  "predictedKwh": [3.0, 2.7, 2.4, 2.3, 2.6, 3.2, 4.8, 7.0, 8.8, 9.5, 10.2, 11.0, 11.5, 10.8, 10.0, 9.2, 10.8, 12.2, 11.8, 10.2, 8.2, 6.8, 5.2, 3.8],
  "currentHourLocal": 13,
  "tariffBands": [
    {
      "type": "VALLE",
      "startHour": 0,
      "endHour": 6,
      "energyPriceCopPerKwh": 280
    },
    {
      "type": "MEDIA",
      "startHour": 6,
      "endHour": 10,
      "energyPriceCopPerKwh": 520
    },
    {
      "type": "PUNTA",
      "startHour": 10,
      "endHour": 13,
      "energyPriceCopPerKwh": 980
    }
  ]
}
```

**Notas**

- **Contrato de horas**: `startHour` inclusivo, `endHour` **exclusivo** (estilo `[start, end)`), salvo que el equipo acuerde lo contrario y lo documente aquí.
- Los arrays `actualKwh`, `predictedKwh` y `hours` deben tener la misma longitud (24 para un día horario).
- `maxKwhScale`: opcional; si no viene, el cliente puede autocalcular el máximo de las series.
- Si el **predictor** no está disponible: `503` o `200` con `predictedKwh: null` y `predictionUnavailable: true` (decidir una política y mantenerla estable).

---

### 3.3. Recomendaciones IA (lista acotada)

**`GET /api/v1/dashboard/recommendations`**

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `date` | No | Día de contexto (`YYYY-MM-DD`). |
| `limit` | No | Máximo de ítems (default recomendado: `3`, máximo acordado: p. ej. `10`). |
| `householdId` | Condicional | Igual que en 3.1. |

**Respuesta `200 OK`**

```json
{
  "date": "2026-03-30",
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Enciende la lavadora a las 22:30",
      "body": "Traslada el ciclo a franja Valle para reducir coste.",
      "suggestedStart": "2026-03-30T22:30:00-05:00",
      "estimatedSavingsCop": 1200,
      "priority": 1
    }
  ]
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
