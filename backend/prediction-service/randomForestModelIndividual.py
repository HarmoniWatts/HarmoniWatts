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
    # Se carga el dataset preconsolidado general
    df = pd.read_csv("data/consumo_preconsolidado.csv")

    return df.shape, df.shape[0], df.shape[1]

def preprocesarDatos():
    global X_train, X_test, y_train, y_test
    
    # 1. Filtrar primero por el segmento de mercado (Estrato 3 y Tarifa A)
    df_segmento = df[
        (df['Estrato'] == 3) &
        (df['Tipo_Tarifa'] == 'A')
    ]

    medidor_seleccionado = 'MN263C548245' 

    # 2. Crear el DataFrame definitivo para este usuario específico
    df_usuario_individual = df_segmento[df_segmento['METER_NO'] == medidor_seleccionado].copy()

    # 3. CRÍTICO: Eliminar columnas que ahora son CONSTANTES (Varianza Cero)
    columnas_a_excluir = ['METER_NO', 'Estrato', 'Tipo_Tarifa', 'Ciudad', 'Nivel de Tension']
    df_modelo_individual = df_usuario_individual.drop(columns=[col for col in columnas_a_excluir if col in df_usuario_individual.columns])

    # 4. Definir columnas predictoras y la columna objetivo de micro-analítica
    columnas_features = [
        'month', 'day_of_week', 'hour', 'Tipo_dia',          # Temporales
        'Precipitacion', 'Temperatura', 'Humedad_Relativa'    # Climáticas
    ]

    X_crudo = df_modelo_individual[columnas_features]
    y = df_modelo_individual['Interval-LP Import kWh']

    # 5. Identificar variables categóricas que necesitan codificación
    columnas_categoricas = ['Tipo_dia']

    # 6. Aplicar One-Hot Encoding
    X = pd.get_dummies(X_crudo, columns=columnas_categoricas, drop_first=True)

    # Convertir columnas booleanas resultantes del get_dummies a enteros (0 o 1)
    columnas_bool = X.select_dtypes(include=['bool']).columns
    X[columnas_bool] = X[columnas_bool].astype(int)

    # Muestreo de datos (30% para testeo adaptado a la firma del cliente)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, shuffle=True, random_state=100)

def randomForest():
    global X_train, X_test, y_train, y_test
    
    # Creación del regresor optimizado para el medidor individual mediante los parámetros de Grid Search
    RF_regressor = RandomForestRegressor(
        n_estimators=150, 
        max_depth=15, 
        min_samples_split=2, 
        random_state=100, 
        verbose=1,
        n_jobs=-1
    )

    # Entrenamiento del regresor (Ajuste de la firma de carga del cliente)
    print("Entrenando el modelo Random Forest Regressor (Fase Individual)...")
    RF_regressor.fit(X_train, y_train)

    # Predicciones de validación
    y_pred = RF_regressor.predict(X_test)

    # Guardar modelo binario personalizado para este medidor en particular
    with open('model/modelo_random_forest_MN263C548245.pkl', 'wb') as f:
        pickle.dump({'model': RF_regressor, 'feature_names': X_train.columns.tolist()}, f)
        print("Modelo Random Forest Regressor (Fase Individual) guardado exitosamente.")
    
    # Cálculo de métricas de alta fidelidad (R² esperado ~ 92.41%)
    r2 = r2_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    
    print(f"Métricas de evaluación del modelo Random Forest Regressor (Fase Individual): R² = {r2:.4f}, MSE = {mse:.4f}")
    
    return r2, mse

def predict(month, day_of_week, hour, tipo_dia, 
                         precipitacion, temperatura, humedad_relativa):
    
    # 1. Crear el DataFrame con los features reducidos e individuales
    datos = [[
        month, day_of_week, hour, tipo_dia, 
        precipitacion, temperatura, humedad_relativa
    ]]
    columnas_features = [
        'month', 'day_of_week', 'hour', 'Tipo_dia',
        'Precipitacion', 'Temperatura', 'Humedad_Relativa'
    ]
    nuevo_ejemplo_crudo = pd.DataFrame(datos, columns=columnas_features)
    
    # 2. Cargar el modelo del medidor específico desde el almacenamiento local/nube
    with open('model/modelo_random_forest_MN263C548245.pkl', 'rb') as f:
        data = pickle.load(f)
        reg_model = data['model']
        feature_names = data['feature_names']
    
    # 3. Aplicar One-Hot Encoding a la variable 'Tipo_dia'
    columnas_categoricas = ['Tipo_dia']
    nuevo_ejemplo_encoded = pd.get_dummies(nuevo_ejemplo_crudo, columns=columnas_categoricas, drop_first=True)
    
    # Convertir booleanos a enteros
    columnas_bool = nuevo_ejemplo_encoded.select_dtypes(include=['bool']).columns
    nuevo_ejemplo_encoded[columnas_bool] = nuevo_ejemplo_encoded[columnas_bool].astype(int)
    
    # 4. Alineación de columnas con la firma matemática guardada
    for col in feature_names:
        if col not in nuevo_ejemplo_encoded.columns:
            nuevo_ejemplo_encoded[col] = 0
            
    nuevo_ejemplo_final = nuevo_ejemplo_encoded[feature_names]
    
    # 5. Resolver predicción del medidor inteligente en kWh
    y_pred = reg_model.predict(nuevo_ejemplo_final)
    
    return y_pred

# Inicialización de estados globales
df = 0
X_train = 0
X_test = 0
y_train = 0
y_test = 0