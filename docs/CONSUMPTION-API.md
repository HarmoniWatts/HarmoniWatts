# Contrato REST — Consumption Service HarmoniWatts

Documento de referencia para proponer e implementar la API del **consumption-service** (consumo eléctrico en tiempo real, series temporales y sincronización desde medidores inteligentes). Complementa la visión de [ARQUITECTURA-HarmoniWatts.md](ARQUITECTURA-HarmoniWatts.md).

---

## 1. Por qué varios endpoints (alineación con SOLID)

| Principio | Cómo ayuda este diseño |
|-----------|-------------------------|
| **S — Single Responsibility** | Cada recurso HTTP responde a **una razón de cambio**: consumo actual (última lectura), totales diarios (agregación), series temporales (gráficos) y sincronización (ingesta desde medidores externos). Evolucionan y se versionan por separado. |
| **O — Open/Closed** | Nuevas granularidades de series (semanal, trimestral) o nuevas fuentes (contador, API externa) se añaden como nuevos endpoints o nuevos query params, sin romper a los consumidores existentes. |
| **I — Interface Segregation** | El dashboard consume solo `current`, `daily-total` y `series/hourly`; el módulo de análisis consume `series/daily`, `series/monthly` y `series/yearly`; el panel administrativo consume `sync/*`. |
| **D — Dependency Inversion** | El dominio expone **casos de uso** acotados (`ConsumptionService`, `SyncService`). Los adaptadores REST implementan cortes estables. La lógica de negocio (agregación, transformación, sincronización) vive en servicios, no en los controladores. |

La UI puede llamar los recursos de **consumo** en paralelo; los de **series** solo cuando se abre el módulo de análisis; los de **sincronización** solo desde el panel administrativo o mediante cron.

### Dependencias internas del servicio

| Componente | Responsabilidad |
|------------|-----------------|
| `ConsumptionRepository` | Acceso a datos de consumo en MongoDB. |
| `SyncRepository` | Persistencia del estado e historial de sincronizaciones. |
| `ConsumptionService` | Lógica de consulta y agregación de consumo. |
| `SyncService` | Orquestación de sincronización desde INELCA. |
| `ViviendaResolverMock` | Resolución `meter_no → id_vivienda` (mock hasta tener user-service). |
| `TarifaResolverHTTP` | Consulta al `tariff-service` para enriquecer con tarifa aplicada. |
| `InelcaClient` | Cliente HTTP para la API de INELCA. |
| `MeterMapper` | Transformación de lecturas INELCA → documentos MongoDB. |

---

## 2. Convenciones generales

| Aspecto | Convención |
|---------|------------|
| **Prefijo** | `/api/v1/consumption` (versionado explícito; cambios incompatibles → `/api/v2`). |
| **Formato** | JSON; `Content-Type: application/json`. |
| **Autenticación** | `Authorization: Bearer <access_token>` (JWT emitido por el auth-service). **⚠️ Actualmente no se valida en el código; pendiente de activar.** |
| **Ámbito vivienda** | El `household_id` (o `id_vivienda`) identifica la vivienda. En el futuro debe validarse contra el JWT del cliente. |
| **Fecha de negocio** | Query `date` con formato **`YYYY-MM-DD`** en la zona horaria del cliente (`America/Bogota`). Si se omite, el backend interpreta **“hoy”** según esa TZ. |
| **Unidades** | Energía en **kWh** (número decimal). Potencia en **kW**. Dinero en **COP** (número decimal). |
| **Timezones** | Todas las fechas/horas en la respuesta incluyen TZ (`America/Bogota`). |
| **Paginación** | Endpoints de historial usan `limit` y `offset`. Respuesta incluye `total`, `limit`, `offset`. |
| **Errores** | Cuerpo JSON común recomendado: `{ "code": "...", "message": "...", "details": {} }`. Códigos HTTP: `400` validación, `401` no autenticado, `403` sin acceso a la vivienda, `404` recurso no encontrado, `422` fecha u operación no aplicable, `500` error interno, `503` dependencia no disponible (ej. INELCA caída). |

---

## 3. Endpoints — Consumo

### 3.1. Consumo actual

**`GET /api/v1/consumption/current/{household_id}`**

Obtiene el consumo actual en **kW** para una vivienda (último registro disponible).

**Path parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `household_id` | Sí | ID de la vivienda. Puede ser `int` o `str` según `HOUSEHOLD_ID_TYPE`. |

**Respuesta `200 OK`**

```json
{
  "id_vivienda": 4,
  "current_power_kw": 2.45,
  "last_update": "2026-11-02T14:30:00-05:00",
  "unit": "kW"
}
```

**Notas**

-`current_power_kw` se calcula a partir del último registro de consumo (o de la diferencia entre los dos últimos registros si la fuente es acumulada).
-`last_update` es el timestamp del último registro disponible.

**Errores**
Obtiene el consumo total acumulado del día en kWh y su costo en COP.
- `400`: `household_id` inválido para el tipo configurado.

- `404`: no hay registros de consumo para la vivienda.

---

### 3.2. Consumo acumulado del día

**`GET /api/v1/consumption/daily-total/{household_id`**
Obtiene el consumo total acumulado del día en kWh y su costo en COP.

**Path parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `household_id` | Sí | ID de la vivienda. |


**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `date` | No | Día a consultar (`YYYY-MM-DD`). Default: hoy (TZ cliente). |


**Respuesta `200 OK`**

```json
{
  "id_vivienda": 4,
  "date": "2026-11-02",
  "total_consumption_kwh": 12.4,
  "total_cost_cop": 4230.50,
  "average_power_kw": 0.52,
  "peak_power_kw": 3.20,
  "peak_hour": 19,
  "unit_kwh": "kWh"
}
```

**Notas**

- `total_consumption_kwh`: suma de `valor_kwh` de todos los registros del día.
- `total_cost_cop`: suma de `tarifa_aplicada.costo_total_franja` (o `costo_total_monomia`) de todos los registros del día.
- `peak_power_kw`: máximo `valor_kwh` del día (asumiendo intervalos de 1 hora).
- `peak_hour`: hora en que ocurrió el pico (1-24).

**Errores**

- `400`: `household_id` inválido.
- `404`: no hay registros para la fecha.

---

## 4. Endpoints — Series temporales

### 4.1. Serie horaria del día

**`GET /api/v1/consumption/series/hourly/{household_id}`**

Obtiene el consumo por hora para un día específico.

**Path parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `household_id` | Sí | ID de la vivienda. |


**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `date` | No | Día a consultar (`YYYY-MM-DD`). Default: hoy (TZ cliente). |


**Respuesta 200 OK**

```json
{
  "id_vivienda": 4,
  "granularity": "hour",
  "start_date": "2026-11-02",
  "end_date": "2026-11-02",
  "labels": ["00:00", "01:00", "...", "23:00"],
  "values_kwh": [0.3, 0.25, "...", 0.4],
  "values_cost": [274.50, 228.75, "...", 366.00],
  "unit": "kWh"
}```

**Notas**

- `labels`: 24 etiquetas (`00:00` a `23:00`).
- `values_kwh`: 24 valores (consumo por hora).
- `values_cost`: 24 valores (costo por hora).
- Horas sin datos se rellenan con `0.0`.

---

### 4.2. Serie diaria del mes

**`GET /api/v1/consumption/series/daily/{household_id}`**

Obtiene el consumo por día para un mes específico.

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `year` | Sí | Año (2020-2030). |
| `month` | Sí | Mes (1-12). |




**Respuesta 200 OK**

```json
{
  "id_vivienda": 4,
  "granularity": "day",
  "start_date": "2026-11-01",
  "end_date": "2026-11-30",
  "labels": ["01", "02", "...", "30"],
  "values_kwh": [12.4, 11.8, "...", 13.2],
  "values_cost": [4230.50, 4026.00, "...", 4505.10],
  "unit": "kWh"
}
```

**Notas**

- `labels`: días del mes (1..N).
- `values_kwh`: consumo diario.
- `values_cost`: costo diario.

---

### 4.3. Serie mensual del año

**`GET /api/v1/consumption/series/monthly/{household_id}`**

Obtiene el consumo por mes para un año específico.

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `year` | Sí | Año (2020-2030). |


**Respuesta 200 OK**

```json
{
  "id_vivienda": 4,
  "granularity": "month",
  "start_date": "2026-01-01",
  "end_date": "2026-12-31",
  "labels": ["Ene", "Feb", "...", "Dic"],
  "values_kwh": [320.5, 298.7, "...", 410.2],
  "values_cost": [109300.0, 101850.0, "...", 139800.0],
  "unit": "kWh"
}
```

**Notas**

- `labels`: nombres de meses abreviados en español.
- `values_kwh`: consumo mensual.
- `values_cost`: costo mensual.

---

### 4.4. Serie anual multi-año

**`GET /api/v1/consumption/series/yearly/{household_id}`**

Obtiene el consumo por año para un rango de años.

**Query parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `start_year` | Sí | Año inicial (2020-2030). |
| `end_year` | Sí | Año final (2020-2030). Debe ser ≥ `start_year` |


**Respuesta 200 OK**

```json
{
  "id_vivienda": 4,
  "granularity": "year",
  "start_date": "2024-01-01",
  "end_date": "2026-12-31",
  "labels": ["2024", "2025", "2026"],
  "values_kwh": [3840.5, 3920.8, 4105.2],
  "values_cost": [1310400.0, 1337700.0, 1399000.0],
  "unit": "kWh"
}
```

**Notas**

- `labels`: años.
- `values_kwh`: consumo anual.
- `values_cost`: costo anual.

**Errores**

- `400`: `start_year > end_year`.

---

## 5. Endpoints — Sincronización desde fuentes externas

La sincronización consulta la API EXTERNA  y persiste los registros en `consumos_enriquecidos` en MongoDB.

### 5.1. Sincronización por vivienda

**`POST /api/v1/consumption/sync/manual/vivienda/{id_vivienda}`**

Sincroniza todos los medidores de una vivienda en un rango de fechas.

**Path  parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `id_vivienda` | Sí | ID de la vivienda. |

**Body (JSON)`**

```json
{
  "fecha_inicio": "2026-07-01",
  "fecha_fin": "2026-07-20"
}
```

**Respuesta `202 Accepted`**

```json
{
  "id_sincronizacion": "sync_v4_a1b2c3",
  "estado": "completado",
  "id_vivienda": 4,
  "medidores": ["MNFFF016E250", "MNFFF016E251"],
  "total_medidores": 2,
  "fecha_inicio": "2026-07-01",
  "fecha_fin": "2026-07-20",
  "mensaje": "Sincronizados 2/2 medidores. 0 fallidos.",
  "detalles": [
    {
      "id_sincronizacion": "sync_v4_med1",
      "meter_no": "MNFFF016E250",
      "estado": "completado",
      "registros_obtenidos": 480,
      "registros_insertados": 475,
      "registros_duplicados": 5,
      "errores": []
    }
  ]
}
```

**Errores**

- `404`: la vivienda no tiene medidores asociados.
- `422`: fechas inválidas (`fecha_fin < fecha_inicio`).

---

### 5.2. Sincronización por cliente

**`POST /api/v1/consumption/sync/manual/cliente/{id_cliente}`**

**Path parameters**

| Parámetro          | Obligatorio | Descripción |
|--------------------|-------------|-------------|
| `id_cliente`       | Sí          | ID del cliente. |


**Body (JSON)`**

```json
{
  "fecha_inicio": "2026-07-01",
  "fecha_fin": "2026-07-20"
}
```


**Respuesta `202 Accepted`**

```json
{
  "id_sincronizacion": "sync_c4_d5e6f7",
  "estado": "completado",
  "id_cliente": 4,
  "medidores": ["MNFFF016E250", "MNFFF016E251", "MNFFF016E300"],
  "total_medidores": 3,
  "fecha_inicio": "2026-07-01",
  "fecha_fin": "2026-07-20",
  "mensaje": "Sincronizados 3/3 medidores. 0 fallidos.",
  "detalles": { ... }
}
```

---

### 5.3. Sincronización por medidor

**`POST /api/v1/consumption/sync/manual/medidor/{meter_no}`**

Sincroniza un medidor específico en un rango de fechas.

**Path  parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `meter_no` | Sí | Número de medidor. |

**Body (JSON)`**

```json
{
  "meter_no": "MNFFF016E250",
  "fecha_inicio": "2026-07-01",
  "fecha_fin": "2026-07-20"
}
```

**Respuesta `202 Accepted`**

```json
{
  "id_sincronizacion": "sync_m1b2c3d4",
  "estado": "completado",
  "meter_no": "MNFFF016E250",
  "fecha_inicio": "2026-07-01",
  "fecha_fin": "2026-07-20",
  "mensaje": "Sincronización completada"
}
```

**Errores**

- `400`: `meter_no` inválido.
- `404`: medidor no encontrado en INELCA.

---

### 5.4. Consultar estado de una sincronización

**`GET /api/v1/consumption/sync/estado/{id_sincronizacion}`**

Consulta el estado de una sincronización disparada previamente.

**Path  parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `id_sincronizacion` | Sí | ID devuelto por cualquier endpoint de sync. |


**Respuesta `200 OK**

```json
{
  "id_sincronizacion": "sync_v4_a1b2c3",
  "estado": "completado",
  "meter_no": null,
  "fecha_inicio": "2026-07-01",
  "fecha_fin": "2026-07-20",
  "registros_obtenidos": 480,
  "registros_insertados": 475,
  "registros_duplicados": 5,
  "errores": [],
  "duracion_seg": 45,
  "creada_en": "2026-11-02T03:36:23-05:00",
  "finalizada_en": "2026-11-02T03:37:08-05:00"
}
```

**Estados posibles:** `pendiente`, `en_proceso`, `completado`, `error`

**Errores**

- `404`: ID de sincronización no encontrado.

---

### 5.5. Historial de sincronizaciones

**`GET /api/v1/consumption/sync/historial`**

Lista las sincronizaciones ejecutadas.

**Query   parameters**

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `limit` | No | Máximo de ítems (1-200). Default: 50. |
| `offset` | No | Desplazamiento. Default: 0. |


**Respuesta `200 OK`**

```json
{
  "total": 24,
  "limit": 50,
  "offset": 0,
  "items": [
    {
      "id_sincronizacion": "sync_v4_a1b2c3",
      "meter_no": "MNFFF016E250",
      "estado": "completado",
      "registros_insertados": 475,
      "fecha_sincronizacion": "2026-11-02T03:36:23-05:00"
    }
  ]
}
```

**Errores**

- `400`: `meter_no` inválido.
- `404`: medidor no encontrado en INELCA.

---

## 6. Códigos de error comunes

| Código | Significado | Ejemplo |
|--------|-------------|---------|
| `400` | Validación de entrada | `household_id` inválido; `start_year > end_year` |
| `401` | Token inválido o ausente | Falta `Authorization: Bearer` (pendiente) |
| `403` | Sin permisos | Consultar consumo de otra vivienda (pendiente) |
| `404` | Recurso no encontrado | Vivienda sin consumo; sincronización inexistente |
| `422` | Fecha no aplicable | `fecha_fin < fecha_inicio` |
| `500` | Error interno | Fallo en el pipeline de sincronización |
| `503` | Servicio no disponible | API INELCA caída; `tariff-service` caído |

**Formato del error:**

```json
{
  "code": "CONSUMPTION_NOT_FOUND",
  "message": "No hay registros de consumo para la vivienda 4 en la fecha 2026-11-02",
  "details": {
    "id_vivienda": 4,
    "fecha": "2026-11-02"
  }
}
```


---

## 7. Resumen de rutas

| Método | Ruta | Responsabilidad |
|--------|------|-----------------|
| `GET` | `/api/v1/consumption/current/{household_id}` | Consumo actual (kW). |
| `GET` | `/api/v1/consumption/daily-total/{household_id}` | Consumo acumulado del día + costo. |
| `GET` | `/api/v1/consumption/series/hourly/{household_id}` | Serie horaria del día. |
| `GET` | `/api/v1/consumption/series/daily/{household_id}` | Serie diaria del mes. |
| `GET` | `/api/v1/consumption/series/monthly/{household_id}` | Serie mensual del año. |
| `GET` | `/api/v1/consumption/series/yearly/{household_id}` | Serie anual multi-año. |
| `POST` | `/api/v1/consumption/sync/manual/vivienda/{id_vivienda}` | Sincronización por vivienda. |
| `POST` | `/api/v1/consumption/sync/manual/cliente/{id_cliente}` | Sincronización por cliente. |
| `POST` | `/api/v1/consumption/sync/manual/medidor/{meter_no}` | Sincronización por medidor. |
| `GET` | `/api/v1/consumption/sync/estado/{id}` | Estado de una sincronización. |
| `GET` | `/api/v1/consumption/sync/historial` | Historial de sincronizaciones. |


## 8. Próximos pasos sugeridos

1. **Reemplazar** `ViviendaResolverMock` por `ViviendaResolverHTTP`: cuando el `user-service` esté disponible.

2. **Agregar** `ViviendaResolverHTTP`: implementar la llamada real al `user-service` para resolver `meter_no → id_vivienda`.

3. **Llamada** de tarea autmatica

4. **Agregar endpoint de anomalías**: `GET /consumption/anomalies/{household_id}` para detectar consumos atípicos.

5. **Agregar endpoint de desagregación**: `GET /consumption/disaggregation/{household_id}` para estimar consumo por electrodoméstico.

*Última actualización: contrato inicial para el `consumption-service`.