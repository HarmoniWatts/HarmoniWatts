# Diccionario de Datos - HarmoniWatts

## 📚 Tablas por Servicio

### 1. CONSUMPTION SERVICE (MongoDB)

#### Colección: `consumption_readings`

**Descripción:** Almacena cada lectura individual de consumo energético en tiempo real.

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `_id` | ObjectId | Sí | Identificador único |
| `household_id` | String | Sí | ID de la vivienda (referencia a Vivienda API) |
| `timestamp` | DateTime | Sí | Momento exacto de la lectura |
| `consumption_kwh` | Float | Sí | Kilovatios consumidos en ese momento |
| `consumption_kw` | Float | No | Potencia instantánea |
| `device_id` | String | Sí | ID del medidor/sensor IoT |
| `metadata` | Object | No | Datos adicionales |
| `metadata.temperature` | Float | No | Temperatura ambiente (°C) |
| `metadata.humidity` | Float | No | Humedad relativa (%) |
| `metadata.grid_frequency` | Float | No | Frecuencia de la red (Hz) |
| `created_at` | DateTime | Sí | Timestamp de inserción |
| `updated_at` | DateTime | No | Última actualización |

**Índices:**
```javascript
db.consumption_readings.createIndex({ "household_id": 1, "timestamp": -1 })
db.consumption_readings.createIndex({ "device_id": 1 })
db.consumption_readings.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 7776000 }) // TTL: 90 días
```

**Ejemplo:**
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "household_id": "h_5f3a9c1e2b8d4a6c",
  "timestamp": ISODate("2026-09-18T14:30:00.000Z"),
  "consumption_kwh": 5.2,
  "consumption_kw": 5.2,
  "device_id": "meter_001_h5f3a9c1e",
  "metadata": {
    "temperature": 25.5,
    "humidity": 60.2,
    "grid_frequency": 60.0
  },
  "created_at": ISODate("2026-09-18T14:30:05.000Z")
}
```

---

#### Colección: `daily_summaries`

**Descripción:** Resúmenes agregados por día para cada vivienda (mejora performance de dashboards).

| Campo | Tipo | Descripción |
|-------|------|------------|
| `_id` | ObjectId | Identificador único |
| `household_id` | String | ID de la vivienda |
| `date` | Date | Fecha del resumen (YYYY-MM-DD) |
| `total_consumption_kwh` | Float | Total de consumo del día |
| `peak_hour` | Integer | Hora con mayor consumo (0-23) |
| `peak_consumption_kwh` | Float | Consumo máximo en una hora |
| `off_peak_consumption_kwh` | Float | Consumo en horas valle |
| `average_hourly_consumption_kw` | Float | Promedio horario |
| `readings_count` | Integer | Número de lecturas procesadas |
| `created_at` | DateTime | Timestamp de creación |

**Índices:**
```javascript
db.daily_summaries.createIndex({ "household_id": 1, "date": -1 })
db.daily_summaries.createIndex({ "date": 1 })
```

**Ejemplo:**
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439012"),
  "household_id": "h_5f3a9c1e2b8d4a6c",
  "date": ISODate("2026-09-18"),
  "total_consumption_kwh": 45.8,
  "peak_hour": 18,
  "peak_consumption_kwh": 8.5,
  "off_peak_consumption_kwh": 37.3,
  "average_hourly_consumption_kw": 1.91,
  "readings_count": 144,
  "created_at": ISODate("2026-09-19T01:00:00.000Z")
}
```

---

### 2. VIVIENDA API (PostgreSQL)

#### Tabla: `households`

**Descripción:** Información de cada vivienda registrada en el sistema.

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|------------|
| `household_id` | SERIAL | PK | Identificador único |
| `user_id` | INT | FK(users.id), NOT NULL | Usuario propietario |
| `name` | VARCHAR(255) | NOT NULL | Nombre/descripción de la vivienda |
| `address` | VARCHAR(255) | NOT NULL | Dirección completa |
| `city` | VARCHAR(100) | NOT NULL | Ciudad |
| `state` | VARCHAR(50) | NOT NULL | Departamento/Provincia |
| `postal_code` | VARCHAR(20) | | Código postal |
| `country` | VARCHAR(50) | | País |
| `square_meters` | FLOAT | | Metros cuadrados de la vivienda |
| `year_built` | INT | | Año de construcción |
| `tariff_type` | VARCHAR(50) | | Tipo de tarifa contratada (residencial, comercial) |
| `meter_id` | VARCHAR(100) | | Identificador del medidor IoT principal |
| `is_active` | BOOLEAN | DEFAULT TRUE | Estado de la vivienda |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Fecha de registro |
| `updated_at` | TIMESTAMP | | Última actualización |

**Índices:**
```sql
CREATE INDEX idx_households_user_id ON households(user_id);
CREATE UNIQUE INDEX idx_households_meter_id ON households(meter_id) WHERE meter_id IS NOT NULL;
```

**Ejemplo:**
```sql
INSERT INTO households (user_id, name, address, city, state, postal_code, square_meters, tariff_type, meter_id)
VALUES (1, 'Mi Apartamento', 'Cra 5 #20-30', 'Bogotá', 'Cundinamarca', '110111', 85.5, 'residencial', 'meter_001_h5f3a9c1e');
```

---

#### Tabla: `users`

**Descripción:** Información de usuarios (sincronizada con Keycloak).

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|------------|
| `id` | SERIAL | PK | Identificador único |
| `keycloak_id` | VARCHAR(255) | UNIQUE, NOT NULL | ID en Keycloak |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Email del usuario |
| `first_name` | VARCHAR(100) | | Nombre |
| `last_name` | VARCHAR(100) | | Apellido |
| `phone` | VARCHAR(20) | | Teléfono |
| `role` | VARCHAR(50) | DEFAULT 'user' | Rol (admin, user) |
| `preferences` | JSONB | | Preferencias del usuario |
| `is_active` | BOOLEAN | DEFAULT TRUE | Cuenta activa |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Fecha de registro |

**Ejemplo:**
```sql
INSERT INTO users (keycloak_id, email, first_name, last_name, role)
VALUES ('user-uuid-123', 'carlos@example.com', 'Carlos', 'Rosero', 'user');
```

---

### 3. ELECTRODOMÉSTICOS API (PostgreSQL)

#### Tabla: `appliances`

**Descripción:** Registro de todos los electrodomésticos por vivienda.

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|------------|
| `appliance_id` | SERIAL | PK | Identificador único |
| `household_id` | INT | FK(households.id), NOT NULL | Vivienda asociada |
| `name` | VARCHAR(255) | NOT NULL | Nombre del dispositivo (ej: "AC Sala") |
| `type` | VARCHAR(100) | NOT NULL | Categoría (AC, Refrigerador, Lavadora, etc) |
| `manufacturer` | VARCHAR(100) | | Fabricante |
| `model` | VARCHAR(100) | | Modelo |
| `power_rating_w` | FLOAT | NOT NULL | Potencia nominal en watts |
| `year_installed` | INT | | Año de instalación |
| `last_maintenance_date` | DATE | | Última revisión |
| `estimated_monthly_kwh` | FLOAT | | Consumo estimado mensual (generado por ML) |
| `estimated_monthly_cost_usd` | FLOAT | | Costo mensual estimado |
| `efficiency_rating` | VARCHAR(10) | | Clasificación energética (A, B, C, etc) |
| `is_active` | BOOLEAN | DEFAULT TRUE | Dispositivo en uso |
| `notes` | TEXT | | Notas adicionales |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Fecha de registro |
| `updated_at` | TIMESTAMP | | Última actualización |

**Índices:**
```sql
CREATE INDEX idx_appliances_household_id ON appliances(household_id);
CREATE INDEX idx_appliances_type ON appliances(type);
```

**Ejemplo:**
```sql
INSERT INTO appliances (household_id, name, type, power_rating_w, year_installed, estimated_monthly_kwh)
VALUES (1, 'AC Sala Principal', 'Aire Acondicionado', 5000, 2022, 150.0);
```

---

#### Tabla: `appliance_predictions`

**Descripción:** Histórico de predicciones generadas por el ML model.

| Campo | Tipo | Descripción |
|-------|------|------------|
| `prediction_id` | SERIAL | Identificador único |
| `appliance_id` | INT | FK(appliances.id) |
| `predicted_monthly_kwh` | FLOAT | Predicción de consumo mensual |
| `confidence_score` | FLOAT | Confianza de la predicción (0-1) |
| `factors` | JSONB | Factores considerados en la predicción |
| `created_at` | TIMESTAMP | Fecha de predicción |

---

### 4. INSIGHTS SERVICE (Cache en Redis)

**Claves en Redis:**

```
// Resumen de dashboard - TTL: 5 minutos
dashboard:summary:{household_id} -> JSON

// Gráficos de consumo - TTL: 10 minutos
charts:hourly:{household_id}:{date} -> JSON

// Recomendaciones - TTL: 1 día
recommendations:{household_id} -> JSON

// Top electrodomésticos - TTL: 1 hora
appliances:top_consumers:{household_id} -> JSON

// Predicción mensual - TTL: 1 día
prediction:monthly:{household_id} -> JSON
```

**Ejemplo:**
```json
// dashboard:summary:h_5f3a9c1e2b8d4a6c
{
  "current_consumption_kw": 5.2,
  "today_total_kwh": 45.8,
  "monthly_prediction_kwh": 250.0,
  "monthly_cost_usd": 35.50,
  "cost_comparison_vs_last_month": "+2.5%",
  "last_updated": "2026-09-18T14:35:00Z"
}
```

---

## 📊 DTOs de APIs

### Consumption Service - Input

```typescript
// POST /ingest
{
  "household_id": "h_5f3a9c1e2b8d4a6c",
  "consumption_kwh": 5.2,
  "device_id": "meter_001",
  "timestamp": "2026-09-18T14:30:00Z",
  "metadata": {
    "temperature": 25.5,
    "humidity": 60
  }
}
```

### Insights Service - Output (Dashboard Summary)

```typescript
{
  "current_consumption_kw": 5.2,
  "today_total_kwh": 45.8,
  "weekly_average_kwh": 320.5,
  "monthly_prediction_kwh": 250.0,
  "monthly_cost_usd": 35.50,
  "cost_comparison_vs_last_month": {
    "percentage": "+2.5%",
    "amount_usd": 0.86
  },
  "savings_potential": {
    "estimated_kwh": 15.0,
    "estimated_cost_usd": 2.13
  },
  "recommendations": [
    {
      "id": "rec_001",
      "text": "Reducir uso de aire acondicionado en horas pico",
      "potential_savings_kwh": 10.0,
      "potential_savings_usd": 1.42,
      "priority": "high"
    }
  ],
  "last_updated": "2026-09-18T14:35:00Z"
}
```

### Electrodomésticos API - Output (Appliance with Prediction)

```typescript
{
  "appliance_id": 1,
  "household_id": 1,
  "name": "AC Sala",
  "type": "Aire Acondicionado",
  "power_rating_w": 5000,
  "year_installed": 2022,
  "estimated_monthly_kwh": 150.0,
  "estimated_monthly_cost_usd": 21.30,
  "efficiency_rating": "A",
  "prediction": {
    "monthly_kwh": 150.0,
    "confidence": 0.92,
    "factors": [
      "Historical consumption pattern",
      "Temperature trends",
      "Usage frequency"
    ]
  }
}
```

---

## 🔐 Relaciones Between Tables

```
users (1) ──────→ (N) households
                      ├─→ (N) appliances
                      └─→ (N) consumption_readings [MongoDB]
                          └─→ (N) daily_summaries [MongoDB]

appliances ──────→ appliance_predictions
```

---

## 📈 Volúmenes de Datos Esperados

| Colección/Tabla | Registros/Día | Registros/Mes | Crecimiento |
|-----------------|--------------|--------------|-----------|
| consumption_readings | 14,400* | 432,000 | 12 lecturas/hora/hogar |
| daily_summaries | 1 | 30 | 1 por día/hogar |
| households | - | +50 | Nuevas viviendas |
| appliances | - | +100 | Nuevos dispositivos |
| users | - | +30 | Nuevos usuarios |

*Para 1,000 hogares con 12 lecturas/hora/hogar

---

## 🗄️ Políticas de Retención

| Datos | Retención | Política |
|-------|-----------|---------|
| consumption_readings | 90 días | TTL automático en MongoDB |
| daily_summaries | 2 años | Archivado |
| appliance_predictions | 6 meses | Eliminación automática |
| user_logs | 1 año | Archivado |

---

**Última actualización:** 18 de Septiembre de 2026
