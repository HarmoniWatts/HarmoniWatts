// =====================================================
// MONGODB - COLECCIONES
// =====================================================

// -----------------------------------------------------
// CONSUMOS - Datos de consumo eléctrico
// -----------------------------------------------------
// =====================================================
// MONGODB - COLECCIÓN: consumos (VERSIÓN COMPLETA)
// =====================================================

db.createCollection("consumos_enriquecidos", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: [
        "id_vivienda", 
        "timestamp", 
        "valor_kwh", 
        "fuente",
        "tarifa_aplicada"
      ],
      properties: {
        _id: { bsonType: "objectId" },
        
        id_vivienda: { 
          bsonType: "long", 
          description: "Referencia a Vivienda.id_vivienda en PostgreSQL" 
        },
		
		id_medidor: { 
          bsonType: "string", 
          description: "Referencia a la id o serie del contador en la Api externa" 
        },
        
        timestamp: { 
          bsonType: "date", 
          description: "Fecha y hora del registro" 
        },
		lectura_acumulada_kwh: { 
          bsonType: "double", 
          description: "Total kWh en el contador" 
        },
        valor_kwh: { 
          bsonType: "double", 
          description: "Consumo en kWh" 
        },
		
		valor_kvarh: { 
          bsonType: "double", 
          description: "Energía reactiva en kVArh" 
        },
		
		valor_export_kwh: {
		  bsonType: "double",
		  description: "Energía activa exportada a la red en kWh"
		},

		valor_export_kvarh: {
		  bsonType: "double",
		  description: "Energía reactiva exportada a la red en kVArh"
		},
        
        tarifa_aplicada: {
		  bsonType: "object",
		  required: [
			"id_tarifa",
			"cod_tipo_tarifa",
			"periodo",
			"configuracion_horaria",
			"franja_aplicada",
			"tipo_hora",
			"modo",
			"precio_kwh_franja",
			"precio_kwh_monomia",
			"costo_total_franja",
			"costo_total_monomia"
		  ],
		  properties: {
			id_tarifa: { bsonType: "long" },
			cod_tipo_tarifa: { bsonType: "string" },
			periodo: { bsonType: "int" },
			configuracion_horaria: { bsonType: "string" },
			franja_aplicada: { bsonType: "string" },
			tipo_hora: { bsonType: "string", enum: ["VALLE", "MEDIA", "PICO"] },
			modo: { bsonType: "string", enum: ["TOU", "RTP", "MONOMIA"] },
			precio_kwh_franja: { bsonType: "double" },
			precio_kwh_monomia: { bsonType: "double" },
			costo_total_franja: { bsonType: "double" },
			costo_total_monomia: { bsonType: "double" },
			moneda: { bsonType: "string" }
		  }
		},
        
        tarifas_alternativas: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              id_tarifa: { bsonType: "long" },
              cod_tipo_tarifa: { bsonType: "string" },
			  periodo: { bsonType: "int" },
			  modo: { bsonType: "string", enum: ["TOU", "RTP", "MONOMIA"] },
			  precio_kwh_franja: { bsonType: "double" },
			  precio_kwh_monomia: { bsonType: "double" },
			  costo_alternativo_franja: { bsonType: "double" },
              costo_alternativo_monomia: { bsonType: "double" },
              diferencia_con_real: { bsonType: "double" }
            }
          }
        },
        
        contexto_temporal: {
          bsonType: "object",
          properties: {
            dia_semana: { bsonType: "int" },
            es_festivo: { bsonType: "bool" },
            hora_del_dia: { bsonType: "int" },
            mes: { bsonType: "int" },
            anio: { bsonType: "int" },
            estacion: { bsonType: "string", enum: ["primavera", "verano", "otoño", "invierno", "N.A"] }
          }
        },
        
        condiciones_externas: {
          bsonType: "object",
          properties: {
            temperatura: { bsonType: "double" },
            humedad: { bsonType: "double" },
            precipitacion: { bsonType: "double" },
            nubosidad: { bsonType: "double" },
            fuente_clima: { bsonType: "string" }
          }
        },
        
        fuente: { 
          bsonType: "string", 
          enum: ["manual", "automatica", "estimado", "contador", "api_externa"]
        },
        calidad_dato: { 
          bsonType: "string", 
          enum: ["real", "estimado", "validado", "sospechoso", "interpolado"]
          // Sin default
        },
        
        fecha_registro: { 
          bsonType: "date"
          // Sin default
        },
        version_schema: { 
          bsonType: "string"
          // Sin default
        }
      }
    }
  }
})

// =====================================================
// ÍNDICES PARA RENDIMIENTO
// =====================================================

// En MongoDB, usar upsert con índice único
db.consumos_enriquecidos.create_index(
    [("id_medidor", 1), ("timestamp", 1)],
    unique=True,
    name="uq_medidor_timestamp"
)

// Upsert
db.consumos_enriquecidos.update_one(
    {"id_medidor": id_medidor, "timestamp": timestamp},
    {"$set": documento},
    upsert=True
)

// Índice principal para consultas por vivienda y rango de fechas
db.consumos_enriquecidos .createIndex(
  { id_vivienda: 1, timestamp: -1 },
  { name: "idx_vivienda_tiempo" }
)

// Índice para análisis temporales globales
db.consumos_enriquecidos .createIndex(
  { timestamp: -1 },
  { name: "idx_tiempo" }
)

// Índice para filtrar por tarifa aplicada
db.consumos_enriquecidos .createIndex(
  { "tarifa_aplicada.id_tarifa": 1, timestamp: -1 },
  { name: "idx_tarifa_tiempo" }
)

// Índice compuesto para análisis de contexto
db.consumos_enriquecidos .createIndex(
  { id_vivienda: 1, "contexto_temporal.mes": 1, "contexto_temporal.anio": 1 },
  { name: "idx_vivienda_mes_anio" }
)

// Índice para búsquedas por fuente
db.consumos_enriquecidos .createIndex(
  { fuente: 1, timestamp: -1 },
  { name: "idx_fuente_tiempo" }
)

// Índice para consultas por calidad de dato
db.consumos_enriquecidos .createIndex(
  { calidad_dato: 1, timestamp: -1 },
  { name: "idx_calidad_tiempo" }
)


// MONGODB - COLECCIÓN: consumos (VERSIÓN Simple)
// =====================================================

db.createCollection("consumos", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: [
        "id_vivienda", 
        "timestamp", 
        "valor_kwh"
      ],
      properties: {
        _id: { bsonType: "objectId" },
        
        // Referencias
        id_vivienda: { 
          bsonType: "long", 
          description: "Referencia a Vivienda.id_vivienda en PostgreSQL" 
        },
        id_tarifa_usuario: { 
          bsonType: "long", 
          description: "Referencia a TarifaUsuario.id_tarifa_usuario activa en el momento" 
        },
        
        // Datos temporales
        timestamp: { 
          bsonType: "date", 
          description: "Fecha y hora del registro" 
        },
        valor_kwh: { 
          bsonType: "double", 
          description: "Consumo en kWh" 
        },
        version_schema: { 
          bsonType: "string", 
          // Sin default "2.0",
          description: "Versión del esquema para compatibilidad" 
        }
      }
    }
  }
})

// =====================================================
// ÍNDICES PARA RENDIMIENTO
// =====================================================

// Índice principal para consultas por vivienda y rango de fechas
db.consumos.createIndex(
  { id_vivienda: 1, timestamp: -1 },
  { name: "idx_vivienda_tiempo" }
)

// Índice para análisis temporales globales
db.consumos.createIndex(
  { timestamp: -1 },
  { name: "idx_tiempo" }
)

// MONGODB - COLECCIÓN: consumos (VERSIÓN TIEMPO SERIE)
// =====================================================


db.createCollection("consumos_ts", {
  timeseries: {
    timeField: "timestamp",      // Campo que marca el tiempo de cada medición
    metaField: "id_vivienda",    // Campo que agrupa las mediciones por vivienda
    granularity: "hours"         // Intervalo típico de tus registros
  },
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: [
        "id_vivienda",
        "timestamp",
        "valor_kwh",
        "fuente",
        "tarifa_aplicada"
      ],
      properties: {
        _id: { bsonType: "objectId" },

        // Referencias
        id_vivienda: {
          bsonType: "long",
          description: "Referencia a Vivienda.id_vivienda en PostgreSQL"
        },
        id_tarifa_usuario: {
          bsonType: "long",
          description: "Referencia a TarifaUsuario.id_tarifa_usuario activa en el momento"
        },

        // Datos temporales
        timestamp: {
          bsonType: "date",
          description: "Fecha y hora del registro"
        },
        valor_kwh: {
          bsonType: "double",
          description: "Consumo en kWh"
        },

        // Información adicional
        fuente: {
          bsonType: "string",
          enum: ["manual", "automatica", "estimado", "contador", "api_externa"]
        },
        tarifa_aplicada: {
          bsonType: "object",
          required: ["id_tarifa", "nombre_tarifa", "precio_kwh", "costo_total", "franja_aplicada"],
          properties: {
            id_tarifa: { bsonType: "long" },
            nombre_tarifa: { bsonType: "string" },
            precio_kwh: { bsonType: "double" },
            costo_total: { bsonType: "double" },
            franja_aplicada: { bsonType: "string" }
          }
        },
        version_schema: {
          bsonType: "string",
          // Sin default "2.0",
          description: "Versión del esquema para compatibilidad"
        }
      }
    }
  }
})


// -----------------------------------------------------
// PREDICCIONES_CONSUMO - Predicciones generadas por IA
// -----------------------------------------------------
db.createCollection("predicciones_consumo", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["id_vivienda", "fecha_generacion", "predicciones"],
      properties: {
        _id: { bsonType: "objectId" },
        id_vivienda: { bsonType: "long" },
        fecha_generacion: { bsonType: "date" },
        horizonte_horas: { bsonType: "int" },
        predicciones: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              timestamp: { bsonType: "date" },
              consumo_estimado_kwh: { bsonType: "double" },
              intervalo_confianza_inf: { bsonType: "double" },
              intervalo_confianza_sup: { bsonType: "double" },
              version_modelo: { bsonType: "string" }
            }
          }
        },
        metadatos_prediccion: {
          bsonType: "object",
          properties: {
            modelo_utilizado: { bsonType: "string" },
            mape_estimado: { bsonType: "double" },
            factores_externos_incluidos: { bsonType: "array", items: { bsonType: "string" } }
          }
        }
      }
    }
  }
})

db.predicciones_consumo.createIndex({ id_vivienda: 1, fecha_generacion: -1 })

// -----------------------------------------------------
// EVENTOS_DISPOSITIVOS - Logs de dispositivos IoT
// -----------------------------------------------------
db.createCollection("eventos_dispositivos", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["id_dispositivo", "timestamp", "evento", "estado"],
      properties: {
        _id: { bsonType: "objectId" },
        id_dispositivo: { bsonType: "long" },
        timestamp: { bsonType: "date" },
        evento: { 
          bsonType: "string",
          enum: ["encendido", "apagado", "cambio_configuracion", "error", "conexion", "desconexion"]
        },
        estado: {
          bsonType: "object",
          properties: {
            encendido: { bsonType: "bool" },
            consumo_actual_w: { bsonType: "double" },
            modo_operacion: { bsonType: "string" }
          }
        },
        origen: { bsonType: "string", enum: ["manual", "automatico", "programado"] },
        id_recomendacion: { bsonType: "long" }
      }
    }
  }
})

db.eventos_dispositivos.createIndex({ id_dispositivo: 1, timestamp: -1 })
db.eventos_dispositivos.createIndex({ timestamp: -1 })

// -----------------------------------------------------
// AHORRO_REAL - Cálculos de ahorro efectivo
// -----------------------------------------------------
db.createCollection("ahorro_real", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["id_vivienda", "periodo_inicio", "periodo_fin"],
      properties: {
        _id: { bsonType: "objectId" },
        id_vivienda: { bsonType: "long" },
        periodo_inicio: { bsonType: "date" },
        periodo_fin: { bsonType: "date" },
        consumo_real_kwh: { bsonType: "double" },
        consumo_simulado_base_kwh: { bsonType: "double" },
        ahorro_eur: { bsonType: "double" },
        ahorro_porcentual: { bsonType: "double" },
        co2_evitado_kg: { bsonType: "double" },
        desglose_recomendaciones: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              id_recomendacion: { bsonType: "long" },
              electrodomestico: { bsonType: "string" },
              ahorro_estimado: { bsonType: "double" },
              ahorro_real: { bsonType: "double" },
              aceptada: { bsonType: "bool" }
            }
          }
        },
        fecha_calculo: { bsonType: "date" }
      }
    }
  }
})

db.ahorro_real.createIndex({ id_vivienda: 1, periodo_inicio: -1 })

// -----------------------------------------------------
// SIMULACIONES_TARIFARIAS - Resultados de simulaciones
// -----------------------------------------------------
db.createCollection("simulaciones_tarifarias", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["id_usuario", "fecha_simulacion", "tarifa_origen", "tarifa_destino"],
      properties: {
        _id: { bsonType: "objectId" },
        id_usuario: { bsonType: "long" },
        fecha_simulacion: { bsonType: "date" },
        tarifa_origen: {
          bsonType: "object",
          properties: {
            id_tarifa: { bsonType: "long" },
            nombre: { bsonType: "string" }
          }
        },
        tarifa_destino: {
          bsonType: "object",
          properties: {
            id_tarifa: { bsonType: "long" },
            nombre: { bsonType: "string" }
          }
        },
        periodo_inicio: { bsonType: "date" },
        periodo_fin: { bsonType: "date" },
        consumo_total_kwh: { bsonType: "double" },
        costo_origen: { bsonType: "double" },
        costo_destino: { bsonType: "double" },
        ahorro_estimado: { bsonType: "double" },
        ahorro_porcentual: { bsonType: "double" },
        desglose_horario: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              fecha: { bsonType: "date" },
              hora: { bsonType: "int" },
              consumo: { bsonType: "double" },
              precio_origen: { bsonType: "double" },
              precio_destino: { bsonType: "double" },
              costo_origen: { bsonType: "double" },
              costo_destino: { bsonType: "double" }
            }
          }
        },
        tipo_simulacion: { bsonType: "string", enum: ["cambio_tarifa", "cambio_habitos", "inversion_solar"] }
      }
    }
  }
})

db.simulaciones_tarifarias.createIndex({ id_usuario: 1, fecha_simulacion: -1 })

// -----------------------------------------------------
// TARIFAS_HISTORICAS_MENSUALES - Snapshots mensuales
// -----------------------------------------------------
db.createCollection("tarifas_historicas_mensuales", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["id_tarifa", "anio", "mes", "valores_completos"],
      properties: {
        _id: { bsonType: "objectId" },
        id_tarifa: { bsonType: "long", description: "Referencia a Tarifa.id_tarifa en PostgreSQL" },
        anio: { bsonType: "int" },
        mes: { bsonType: "int" },
        valores_completos: {
          bsonType: "object",
          properties: {
            valores_franja: {
              bsonType: "object",
              properties: {
                F1: { bsonType: "double" },
                F2: { bsonType: "double" },
                F3: { bsonType: "double" },
                F4: { bsonType: "double" },
                F5: { bsonType: "double" },
                F6: { bsonType: "double" },
                F7: { bsonType: "double" },
                F8: { bsonType: "double" }
              }
            },
            componentes: {
              bsonType: "object",
              properties: {
                cu_base: { bsonType: "double" },
                cu_aplicado: { bsonType: "double" },
                cargo_consumo: { bsonType: "double" }
              }
            },
            definicion_horas: {
              bsonType: "object",
              properties: {
                F1: { bsonType: "string" },
                F2: { bsonType: "string" },
                F3: { bsonType: "string" },
                F4: { bsonType: "string" },
                F5: { bsonType: "string" },
                F6: { bsonType: "string" },
                F7: { bsonType: "string" },
                F8: { bsonType: "string" }
              }
            }
          }
        },
        fecha_archivo: { bsonType: "date" }
      }
    }
  }
})

db.tarifas_historicas_mensuales.createIndex({ id_tarifa: 1, anio: -1, mes: -1 })

// -----------------------------------------------------
// COMPARATIVAS_ANONIMAS - Análisis comparativo
// -----------------------------------------------------
db.createCollection("comparativas_anonimas", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["id_vivienda", "periodo", "grupo_similar_id"],
      properties: {
        _id: { bsonType: "objectId" },
        id_vivienda: { bsonType: "long" },
        periodo: { bsonType: "date" },
        grupo_similar_id: { bsonType: "string" },
        consumo_promedio_grupo: { bsonType: "double" },
        ahorro_promedio_grupo: { bsonType: "double" },
        percentil_usuario: { bsonType: "int" },
        metadatos_grupo: {
          bsonType: "object",
          properties: {
            tamano_grupo: { bsonType: "int" },
            criterios_similitud: { bsonType: "array", items: { bsonType: "string" } }
          }
        },
        fecha_calculo: { bsonType: "date" }
      }
    }
  }
})

db.comparativas_anonimas.createIndex({ id_vivienda: 1, periodo: -1 })