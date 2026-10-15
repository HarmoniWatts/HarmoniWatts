import numpy as np
import pandas as pd
import pickle

# Importar librería para el Muestreo de datos
from sklearn.model_selection import train_test_split

# Importar librería de Random Forest para Regresión
from sklearn.ensemble import RandomForestRegressor

# Importar librerías de métricas de evaluación para Regresión
from sklearn.metrics import r2_score, mean_squared_error

# Configurar cantidad de decimales
pd.set_option('display.precision', 2)
    
def cargarDatos():
    global df
    # Se carga el dataset preconsolidado
    df = pd.read_csv("data/consumo_preconsolidado.csv")

    return df.shape, df.shape[0], df.shape[1]

def preprocesarDatos():
    global X_train, X_test, y_train, y_test
    
    # 1. Filtrar el dataset general por el nicho con mayor variabilidad (Estrato 3 - Tarifa A)
    df_nicho = df[
        (df['Estrato'] == 3) &
        (df['Tipo_Tarifa'] == 'A')
    ]

    # 2. Definir columnas predictoras y la columna objetivo para el segmento
    columnas_features = [
        'month', 'day_of_week', 'hour', 'Tipo_dia',          # Temporales
        'Ciudad',                                             # Técnicas y geográficas
        'Tarifa_aplicada',                                    # Económicas y negocio
        'Precipitacion', 'Temperatura', 'Humedad_Relativa'    # Climáticas
    ]

    X_crudo = df_nicho[columnas_features]
    y = df_nicho['Interval-LP Import kWh']

    # 3. Identificar variables categóricas que necesitan codificación (One-Hot Encoding)
    columnas_categoricas = ['Tipo_dia', 'Ciudad']

    # 4. Aplicar One-Hot Encoding
    X = pd.get_dummies(X_crudo, columns=columnas_categoricas, drop_first=True)

    # Convertir columnas booleanas resultantes del get_dummies a enteros (0 o 1)
    columnas_bool = X.select_dtypes(include=['bool']).columns
    X[columnas_bool] = X[columnas_bool].astype(int)

    # Muestreo de datos (30% para testeo / validación del segmento)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, shuffle=True, random_state=100)

def randomForest():
    global X_train, X_test, y_train, y_test
    
    # Creación del regresor configurado según los hiperparámetros del segmento solicitado
    RF_regressor = RandomForestRegressor(
        n_estimators=150, 
        max_depth=15, 
        min_samples_split=2, 
        random_state=100, 
        verbose=1,
        n_jobs=-1
    )

    # Entrenamiento del regresor con los datos del nicho
    print("Entrenando el modelo Random Forest Regressor (Fase Segmentada)...")  
    RF_regressor.fit(X_train, y_train)

    # Predicciones en el conjunto de datos de prueba del segmento
    y_pred = RF_regressor.predict(X_test)

    # Persistencia del modelo e historial de nombres de columnas codificadas
    with open('model/modelo_random_forest_segmento.pkl', 'wb') as f:
        pickle.dump({'model': RF_regressor, 'feature_names': X_train.columns.tolist()}, f)
        print("Modelo Random Forest Regressor (Fase Segmentada) guardado exitosamente.")
    
    # Cálculo de métricas
    r2 = r2_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    
    print(f"Métricas de evaluación del modelo Random Forest Regressor (Fase Segmentada): R² = {r2:.4f}, MSE = {mse:.4f}")  
    
    return r2, mse

def predict(month, day_of_week, hour, tipo_dia, ciudad, 
                         tarifa_aplicada, precipitacion, temperatura, humedad_relativa):
    
    # 1. Crear el DataFrame con las características correspondientes al segmento
    datos = [[
        month, day_of_week, hour, tipo_dia, ciudad, 
        tarifa_aplicada, precipitacion, temperatura, humedad_relativa
    ]]
    columnas_features = [
        'month', 'day_of_week', 'hour', 'Tipo_dia',
        'Ciudad',
        'Tarifa_aplicada',
        'Precipitacion', 'Temperatura', 'Humedad_Relativa'
    ]
    nuevo_ejemplo_crudo = pd.DataFrame(datos, columns=columnas_features)
    
    # 2. Cargar el modelo del segmento y sus nombres de columnas de entrenamiento
    with open('model/modelo_random_forest_segmento.pkl', 'rb') as f:
        data = pickle.load(f)
        reg_model = data['model']
        feature_names = data['feature_names']
    
    # 3. Aplicar One-Hot Encoding al registro entrante
    columnas_categoricas = ['Tipo_dia', 'Ciudad']
    nuevo_ejemplo_encoded = pd.get_dummies(nuevo_ejemplo_crudo, columns=columnas_categoricas, drop_first=True)
    
    # Convertir booleanos a enteros
    columnas_bool = nuevo_ejemplo_encoded.select_dtypes(include=['bool']).columns
    nuevo_ejemplo_encoded[columnas_bool] = nuevo_ejemplo_encoded[columnas_bool].astype(int)
    
    # 4. Alineación estructural con las columnas del entrenamiento
    for col in feature_names:
        if col not in nuevo_ejemplo_encoded.columns:
            nuevo_ejemplo_encoded[col] = 0
            
    nuevo_ejemplo_final = nuevo_ejemplo_encoded[feature_names]
    
    # 5. Calcular predicción continua (kWh)
    y_pred = reg_model.predict(nuevo_ejemplo_final)
    
    return y_pred

# Inicialización de estados globales
df = 0
X_train = 0
X_test = 0
y_train = 0
y_test = 0