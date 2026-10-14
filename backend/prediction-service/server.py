from flask import Flask, jsonify, render_template, request
import randomForestModelGlobal as rf_model_global, randomForestModelSegmented as rf_segment_model, randomForestModelIndividual as rf_individual_model

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/users/<nombre>/')
def helloWorld(nombre):
    return "Hola {}!".format(nombre)

# API para el acceso a los distintos modelos de aprendizaje supervisado

# =====================================================================
# 1. FASE 1: ENFOQUE GLOBAL (RUTA MACRO / OPERATIVA)
# =====================================================================
@app.route('/api/v1/predict/global', methods=['POST'])
def predict_global():
    data = request.get_json()
    
    # Extracción estricta del Payload Request solicitado
    month            = data.get('month')
    day_of_week      = data.get('day_of_week')
    hour             = data.get('hour')
    tipo_dia         = data.get('Tipo_dia')
    estrato          = data.get('Estrato')
    nivel_tension    = data.get('Nivel de Tension')
    ciudad           = data.get('Ciudad')
    tipo_tarifa      = data.get('Tipo_Tarifa')
    franja           = data.get('Franja')
    tarifa_aplicada  = data.get('Tarifa_aplicada')
    precipitacion    = data.get('Precipitacion')
    temperatura      = data.get('Temperatura')
    humedad_relativa = data.get('Humedad_Relativa')
    
    # Ejecución interna de ambos modelos para la fase macro
    pred_rf = rf_model_global.predict(month,day_of_week,hour,tipo_dia,estrato,nivel_tension,ciudad,tipo_tarifa,franja,tarifa_aplicada,precipitacion,temperatura,humedad_relativa)
    # pred_gb = gb_model.predict_global([temperatura, humidity_relativa, precipitacion, is_festivo])
    
    # prediccion_rf = 0.3125  # Simulación RF Baseline
    # prediccion_gb = 0.3210  # Simulación GB Baseline
    
    response = {
        "fase": "Consolidado General (Macro)",
        "modelos_evaluados": {
            "Random Forest Regressor": {
                "prediccion_kwh": pred_rf[0],
                "metrica_confianza_r2": 0.0805,
                "error_esperado_wmape": "88.83%"
            }
        },
        "nota_seleccion": "Random Forest seleccionado por mejor desempeño marginal en R²"
    }
    
    # response = {
    #     "fase": "Consolidado General (Macro)",
    #     "modelos_evaluados": {
    #         "Random Forest Regressor": {
    #             "prediccion_kwh": prediccion_rf,
    #             "metrica_confianza_r2": 0.0802,
    #             "error_esperado_wmape": "89.33%"
    #         },
    #         "Gradient Boosting Regressor": {
    #             "prediccion_kwh": prediccion_gb,
    #             "metrica_confianza_r2": 0.0765, # Ejemplo de métrica competitiva
    #             "error_esperado_wmape": "91.20%"
    #         }
    #     },
    #     "nota_seleccion": "Random Forest seleccionado por mejor desempeño marginal en R²"
    # }
    
    return jsonify(response), 200


# =====================================================================
# 2. FASE 2: ENFOQUE DE SEGMENTACIÓN (RUTA DE CLÚSTER / COMERCIAL)
# =====================================================================
@app.route('/api/v1/predict/segment', methods=['POST'])
def predict_segment():
    data = request.get_json()
    
    month            = data.get('month')
    day_of_week      = data.get('day_of_week')
    hour             = data.get('hour')
    tipo_dia         = data.get('Tipo_dia')
    estrato          = data.get('Estrato')
    ciudad           = data.get('Ciudad')
    tipo_tarifa      = data.get('Tipo_Tarifa')
    tarifa_aplicada  = data.get('Tarifa_aplicada')
    precipitacion    = data.get('Precipitacion')
    temperatura      = data.get('Temperatura')
    humedad_relativa = data.get('Humedad_Relativa')
    
    # FILTRO DE VALIDACIÓN: El modelo solo es válido para Estrato 3 y Tarifa A
    if estrato != 3 or tipo_tarifa != 'A':
        return jsonify({
            "error": "Modelo no disponible",
            "mensaje": f"El modelo de segmentación actual solo está entrenado para Estrato 3 y Tarifa A. Recibido: Estrato {estrato}, Tarifa {tipo_tarifa}."
        }), 400  # Código 400: Bad Request
        
    # Si pasa el filtro, se ejecuta la lógica del modelo con seguridad
    pred_rf = rf_segment_model.predict(month,day_of_week,hour,tipo_dia,ciudad,tarifa_aplicada,precipitacion,temperatura,humedad_relativa)
    # pred_gb = gb_model.predict_segmented([temperatura, humedad_relativa, precipitacion, tipo_dia])

    
    # prediccion_rf = 0.4281  # Simulación RF Segmentado
    # prediccion_gb = 0.4155  # Simulación GB Segmentado
    
    response = {
        "fase": "Segmentación de Socio-Económica",
        "cluster_evaluado": f"Estrato {estrato} - Tarifa Tipo {tipo_tarifa}",
        "modelos_evaluados": {
            "Random Forest Regressor": {
                "prediccion_kwh": pred_rf[0],
                "metrica_confianza_r2": 0.1818,
                "error_esperado_wmape": "48.31%"
            }
        },
        "nota_seleccion": "Modelo entrenado bajo parametros socio-economicos específicos"
    }
    
    # response = {
    #     "fase": "Segmentación de Mercado (Clúster)",
    #     "cluster_evaluado": f"Estrato {estrato} - Tarifa Tipo {tipo_tarifa}",
    #     "modelos_evaluados": {
    #         "Random Forest Regressor": {
    #             "prediccion_kwh": prediccion_rf,
    #             "metrica_confianza_r2": 0.1623,
    #             "error_esperado_wmape": "50.39%"
    #         },
    #         "Gradient Boosting Regressor": {
    #             "prediccion_kwh": prediccion_gb,
    #             "metrica_confianza_r2": 0.1580,
    #             "error_esperado_wmape": "52.11%"
    #         }
    #     },
    #     "nota_seleccion": "Ambos modelos entrenados bajo hiperparámetros específicos de la región geográfica."
    # }
    
    return jsonify(response), 200


# =====================================================================
# 3. FASE 3: FASE DE MICRO-ANALÍTICA (RUTA INDIVIDUAL / SMART GRID)
# =====================================================================
@app.route('/api/v1/predict/meter/<meter_id>', methods=['POST'])
def predict_meter(meter_id):
    data = request.get_json()
    
    # Payload Request
    month            = data.get('month')
    day_of_week      = data.get('day_of_week')
    hour             = data.get('hour')
    tipo_dia         = data.get('Tipo_dia')
    precipitacion    = data.get('Precipitacion')
    temperatura      = data.get('Temperatura')
    humedad_relativa = data.get('Humedad_Relativa')
    
    
    # -----------------------------------------------------------------
    # FILTRO DE VALIDACIÓN DINÁMICA (Simulación de Storage en la Nube)
    # -----------------------------------------------------------------
    # En producción, verificaríamos si existen los archivos en el bucket.
    # Para tu simulación/taller, si el cliente pide un medidor diferente al 
    # entrenado (ej. 'MN263C548245'), disparamos un error 404.
    medidores_entrenados = ['MN263C548245'] 
    
    if meter_id not in medidores_entrenados:
        return jsonify({
            "error": "Medidor no encontrado o no optimizado",
            "mensaje": f"No se encontraron modelos de alta fidelidad (GridSearch) en la nube para el medidor '{meter_id}'. Verifique el ID."
        }), 404  # Código 404: Not Found (No encontrado)
    
    # -----------------------------------------------------------------
    # Si pasa el filtro, se procede a la descarga y cálculo
    # -----------------------------------------------------------------
    pred_rf = rf_individual_model.predict(month,day_of_week,hour,tipo_dia,precipitacion,temperatura,humedad_relativa)
    # path_gb = storage_utils.download_model(meter_id, "gradient_boosting")
    
    # prediccion_rf = 0.8420  # Simulación de ultra alta fidelidad para MN263C548245
    # prediccion_gb = 0.8395  # Simulación de ultra alta fidelidad para MN263C548245
    
    
    response = {
        "fase": "Micro-Analítica Individual (Smart Grid)",
        "medidor_evaluado": meter_id,
        "modelos_evaluados": {
            "Random Forest Regressor": {
                "prediccion_kwh": pred_rf[0],
                "metrica_confianza_r2": 0.9508,
                "error_esperado_wmape": "3.91%",
                "hiperparametros_aplicados": {
                    "n_estimators": 150,
                    "max_depth": 15,
                    "min_samples_split": 2
                }
            }
        }
    }
    
    # response = {
    #     "fase": "Micro-Analítica Individual (Smart Grid)",
    #     "medidor_evaluado": meter_id,
    #     "modelos_evaluados": {
    #         "Random Forest Regressor": {
    #             "prediccion_kwh": prediccion_rf,
    #             "metrica_confianza_r2": 0.9241,
    #             "error_esperado_wmape": "8.91%",
    #             "hiperparametros_aplicados": {
    #                 "n_estimators": 150,
    #                 "max_depth": 15,
    #                 "min_samples_split": 2
    #             }
    #         },
    #         "Gradient Boosting Regressor": {
    #             "prediccion_kwh": prediccion_gb,
    #             "metrica_confianza_r2": 0.9115,
    #             "error_esperado_wmape": "9.45%",
    #             "hiperparametros_aplicados": {
    #                 "n_estimators": 200,
    #                 "learning_rate": 0.05,
    #                 "max_depth": 8
    #             }
    #         }
    #     },
    #     "estado_alerta_pico": "ALTA DEMANDA - CONFORT TÉRMICO"
    # }
    
    return jsonify(response), 200


# =====================================================================
# ENDPOINTS DE ENTRENAMIENTO Y AJUSTE DE MODELOS (PIPELINES)
# =====================================================================

@app.route('/train/global')
def train_global_model():
    # 1. Cargar el dataset consolidado macro
    dimen, regs, cols = rf_model_global.cargarDatos()
    print(f"[FASE 1] Datos cargados - Dimensión: {dimen}, Registros: {regs}, Columnas: {cols}")
    
    # 2. Aplicar One-Hot Encoding global y split
    rf_model_global.preprocesarDatos()
    
    # 3. Entrenar con los hiperparámetros base (n_estimators=150, max_depth=15)
    r2_score, mse = rf_model_global.randomForest()
    
    # 4. Enviar reporte de métricas continuas a la vista
    return render_template('resultados.html', 
                           model="Random Forest Regressor (Fase 1: Global)",
                           dimen=dimen, regs=regs, cols=cols, 
                           r2=f"{r2_score:.4f} (R² Score)", 
                           mse=f"{mse:.4f} (MSE)")

@app.route('/train/segment')
def train_segmented_model():
    # 1. Cargar dataset general
    dimen, regs, cols = rf_segment_model.cargarDatos()
    print(f"[FASE 2] Datos cargados - Dimensión: {dimen}")
    
    # 2. Filtrar por Estrato 3 + Tarifa A y codificar variables categóricas específicas
    rf_segment_model.preprocesarDatos()
    
    # 3. Entrenar el regresor del nicho (min_samples_split=2)
    r2_score, mse = rf_segment_model.randomForest()
    
    return render_template('resultados.html', 
                           model="Random Forest Regressor (Fase 2: Segmento Estrato 3-A)",
                           dimen=dimen, regs=regs, cols=cols, 
                           r2=f"{r2_score:.4f} (R² Score)", 
                           mse=f"{mse:.4f} (MSE)")


@app.route('/train/meter/MN263C548245')
def train_individual_model():
    # 1. Cargar dataset general
    dimen, regs, cols = rf_individual_model.cargarDatos()
    print(f"[FASE 3] Datos cargados para firma de medidor")
    
    # 2. Aislar al cliente específico y purgar variables con varianza cero (constantes)
    rf_individual_model.preprocesarDatos()
    
    # 3. Entrenar el modelo hiper-optimizado (GridSearch CV)
    r2_score, mse = rf_individual_model.randomForest()
    
    return render_template('resultados.html', 
                           model="Random Forest Regressor (Fase 3: Individual - Medidor: MN263C548245)",
                           dimen=dimen, regs=regs, cols=cols, 
                           r2=f"{r2_score:.4f} (R² Score)", 
                           mse=f"{mse:.4f} (MSE)")

# =====================================================================
# ARRANQUE DEL MICROSERVICIO UNIFICADO
# =====================================================================

# Ejecutar servidor de aplicaciones
if __name__ == '__main__':
    app.run(debug=True, port=8000)