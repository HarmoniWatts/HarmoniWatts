import numpy as np
import pandas as pd
import pickle

# Importar librería para Normalizar los datos
from sklearn.preprocessing import MinMaxScaler

# Importar librería para el Muestreo de datos
from sklearn.model_selection import train_test_split

# Importar librería de Random Forest
from sklearn.ensemble import RandomForestClassifier

# Importar librería de Reportes y métricas de evaluación
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Configurar cantidad de decimales
pd.set_option('display.precision', 2)
    
def cargarDatos():
    global df
    df = pd.read_csv("data/heart-disease-uci.csv")

    return df.shape, df.shape[0], df.shape[1]

def preprocesarDatos():
    global X_train, X_test, y_train, y_test
    
    # Separar las características (X) y la variable objetivo (y)
    X = df.drop(['target'], axis=1)
    y = df['target']

    # Escalar las características con MinMaxScaler
    scaler_X = MinMaxScaler()
    X = pd.DataFrame(scaler_X.fit_transform(X), columns=X.columns)

    # Muestreo de datos
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, shuffle=True, random_state=100)

# Función para cargar modelos utilizando la serialización de objetos en Python
def load_model(filename):
    global X_train, X_test, y_train, y_test
    
    with open(''+filename, 'rb') as f:
        RF_classifier = pickle.load(f)
    
    y_pred = RF_classifier.predict(X_test)
    
    return accuracy_score(y_test, y_pred), f1_score(y_test, y_pred)

def classifyNuevoEjemplo(edad, genero, dolorPecho, presArterial, colesterol, glicAyunas, resElctr,
                         frCardiaca, angInd, deprST, pendSeg, nVasos, thalassemia):
    
    datos = [
        [int(edad), int(genero), int(dolorPecho), int(presArterial), int(colesterol), glicAyunas, int(resElctr),
        int(frCardiaca), angInd, float(deprST), int(pendSeg), int(nVasos), int(thalassemia)],
    ]
    columnas = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal']
    nuevoEjemplo = pd.DataFrame(datos, columns=columnas)
    
    with open('model/modelo_random_forest.pkl', 'rb') as f:
        data = pickle.load(f)
        clf_tree = data['model']
        feature_names = data['feature_names']
    
    y_pred = clf_tree.predict(nuevoEjemplo)
    
    return y_pred

def randomForest():
    global X_train, X_test, y_train, y_test
    
    # Creación del clasificador
    RF_classifier = RandomForestClassifier(n_estimators=100, random_state=42)

    # Entrenamiento del clasificador
    RF_classifier.fit(X_train, y_train)

    # Predicciones en el conjunto de datos de prueba
    y_pred = RF_classifier.predict(X_test)

    with open('model/modelo_random_forest.pkl', 'wb') as f:
        pickle.dump({'model': RF_classifier, 'feature_names': X_train.columns.tolist()}, f)
    
    return accuracy_score(y_test, y_pred), f1_score(y_test, y_pred)

df = 0
X_train = 0
X_test = 0
y_train = 0
y_test = 0