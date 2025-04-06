import joblib
import pandas as pd
import numpy as np

modelo_kmeans = joblib.load("modelos/kmeans_model.pkl")
mlb_experiencias = joblib.load("modelos/mlb_experiencias.pkl")
mlb_transporte = joblib.load("modelos/mlb_transporte.pkl")
ohe = joblib.load("modelos/ohe_categoricos.pkl")
scaler = joblib.load("modelos/scaler_numericos.pkl")

def predecir_cluster(nuevo_usuario):
    df_nuevo = pd.DataFrame([nuevo_usuario])

    experiencias_encoded = mlb_experiencias.transform([df_nuevo["experiencias"].values[0]])
    transporte_encoded = mlb_transporte.transform([df_nuevo["transporte"].values[0]])

    experiencias_df = pd.DataFrame(experiencias_encoded, columns=[f"exp_{x}" for x in mlb_experiencias.classes_])
    transporte_df = pd.DataFrame(transporte_encoded, columns=[f"transp_{x}" for x in mlb_transporte.classes_])

    categorical_cols = ['sostenibilidad', 'tiempo_transporte', 'nivel_actividad', 'compania']
    categorical_encoded = ohe.transform(df_nuevo[categorical_cols])
    categorical_df = pd.DataFrame(categorical_encoded, columns=ohe.get_feature_names_out(categorical_cols))

    numeric_cols = ['duracion_ruta', 'presupuesto']
    numeric_scaled = scaler.transform(df_nuevo[numeric_cols])
    numeric_df = pd.DataFrame(numeric_scaled, columns=numeric_cols)

    df_final = pd.concat([experiencias_df, transporte_df, categorical_df, numeric_df], axis=1)

    cluster_predicho = modelo_kmeans.predict(df_final)[0]

    return int(cluster_predicho)

if __name__ == "__main__":
    nuevo_usuario = {
        "experiencias": ["Cultural", "Ecológica"],
        "duracion_ruta": 3,
        "sostenibilidad": "Muy importante",
        "transporte": ["A pie", "Metro"],
        "tiempo_transporte": "Tengo prisa!",
        "nivel_actividad": "Moderado",
        "compania": "En pareja",
        "presupuesto": 120
    }

    cluster = predecir_cluster(nuevo_usuario)
