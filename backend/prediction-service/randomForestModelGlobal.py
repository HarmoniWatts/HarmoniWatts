import numpy as np
import pandas as pd
import pickle

# Importar librería para el Muestreo de datos
from sklearn.model_selection import train_test_split

# Importar librería de Random Forest para REGRESIÓN (Fase Global)
from sklearn.ensemble import RandomForestRegressor

# Importar librerías de métricas de evaluación para Regresión
from sklearn.metrics import r2_score, mean_squared_error

# Configurar cantidad de decimales
pd.set_option('display.precision', 2)
    
def cargarDatos():
    global df
    # Se asume que el archivo consolidado de consumo se encuentra en esta ruta
    df = pd.read_csv("data/consumo_consolidado.csv")

    return df.shape, df.shape[0], df.shape[1]

def preprocesarDatos():
    global X_train, X_test, y_train, y_test
    
    # 1. Definir columnas predictoras y la columna objetivo
    columnas_features = [
        'month', 'day_of_week', 'hour', 'Tipo_dia',          # Temporales
        'Estrato', 'Nivel de Tension', 'Ciudad',              # Técnicas y geográficas
        'Tipo_Tarifa', 'Tarifa_aplicada',                     # Económicas y negocio
        'Precipitacion', 'Temperatura', 'Humedad_Relativa'    # Climáticas
    ]

    X_crudo = df[columnas_features]
    y = df['Interval-LP Import kWh']

    # 2. Identificar variables categóricas que necesitan codificación (One-Hot Encoding)
    columnas_categoricas = ['Tipo_dia', 'Nivel de Tension', 'Ciudad', 'Tipo_Tarifa']

    # 3. Aplicar One-Hot Encoding
    X = pd.get_dummies(X_crudo, columns=columnas_categoricas, drop_first=True)

    # Convertir columnas booleanas resultantes del get_dummies a enteros (0 o 1)
    columnas_bool = X.select_dtypes(include=['bool']).columns
    X[columnas_bool] = X[columnas_bool].astype(int)

    # Muestreo de datos para validación del modelo global (30% para testeo)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, shuffle=True, random_state=100)

def randomForest():
    global X_train, X_test, y_train, y_test
    
    # Creación del regresor base con los hiperparámetros especificados
    RF_regressor = RandomForestRegressor(
        n_estimators=150, 
        max_depth=15, 
        min_samples_split=5, 
        random_state=100,
        verbose=1,
        n_jobs=-1
    )

    # Entrenamiento del regresor
    print("Entrenando el modelo Random Forest Regressor (Fase Global)...")
    RF_regressor.fit(X_train, y_train)

    # Predicciones en el conjunto de datos de prueba
    y_pred = RF_regressor.predict(X_test)

    # Persistencia del modelo entrenado y la estructura de columnas (indispensable para nuevas predicciones)
    with open('model/modelo_random_forest_global.pkl', 'wb') as f:
        pickle.dump({'model': RF_regressor, 'feature_names': X_train.columns.tolist()}, f)
        print("Modelo Random Forest Regressor (Fase Global) guardado exitosamente.")
    
    # Cálculo de métricas de regresión (R² y MSE)
    r2 = r2_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    
    print(f"Métricas de evaluación del modelo Random Forest Regressor (Fase Global): R² = {r2:.4f}, MSE = {mse:.4f}")
    
    return r2, mse

def predict(month,day_of_week,hour,tipo_dia,estrato,nivel_tension,
            ciudad,tipo_tarifa,franja,tarifa_aplicada,
            precipitacion,temperatura,humedad_relativa):
    
    # 1. Crear el DataFrame del nuevo registro crudo
    datos = [[
        month, day_of_week, hour, tipo_dia, estrato, nivel_tension, ciudad, 
        tipo_tarifa, tarifa_aplicada, precipitacion, temperatura, humedad_relativa
    ]]
    columnas_features = [
        'month', 'day_of_week', 'hour', 'Tipo_dia',
        'Estrato', 'Nivel de Tension', 'Ciudad',
        'Tipo_Tarifa', 'Tarifa_aplicada',
        'Precipitacion', 'Temperatura', 'Humedad_Relativa'
    ]
    nuevo_ejemplo_crudo = pd.DataFrame(datos, columns=columnas_features)
    
    # 2. Cargar el modelo entrenado y los nombres exactos de las columnas tras One-Hot Encoding
    with open('model/modelo_random_forest_global.pkl', 'rb') as f:
        data = pickle.load(f)
        reg_model = data['model']
        feature_names = data['feature_names']
    
    # 3. Aplicar One-Hot Encoding al nuevo ejemplo crudo de la misma manera
    columnas_categoricas = ['Tipo_dia', 'Nivel de Tension', 'Ciudad', 'Tipo_Tarifa']
    nuevo_ejemplo_encoded = pd.get_dummies(nuevo_ejemplo_crudo, columns=columnas_categoricas, drop_first=True)
    
    # Convertir booleanos a enteros
    columnas_bool = nuevo_ejemplo_encoded.select_dtypes(include=['bool']).columns
    nuevo_ejemplo_encoded[columnas_bool] = nuevo_ejemplo_encoded[columnas_bool].astype(int)
    
    # 4. ALINEACIÓN DE COLUMNAS: Asegurar que el nuevo ejemplo tenga exactamente el mismo orden y columnas
    # que vio el modelo durante el fit (creando las columnas faltantes con valor 0)
    for col in feature_names:
        if col not in nuevo_ejemplo_encoded.columns:
            nuevo_ejemplo_encoded[col] = 0
            
    nuevo_ejemplo_final = nuevo_ejemplo_encoded[feature_names]
    
    # 5. Ejecutar y retornar la predicción continua (kWh)
    y_pred = reg_model.predict(nuevo_ejemplo_final)
    
    return y_pred

# Inicialización de estados
df = 0
X_train = 0
X_test = 0
y_train = 0
y_test = 0