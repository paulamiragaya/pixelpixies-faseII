from fastapi import FastAPI
import pandas as pd
from clustering_predict import predecir_cluster
from sistema_recomendacion import GeneradorRecomendaciones

app = FastAPI()

from pydantic import BaseModel
from typing import List

class UsuarioDatos(BaseModel):
    experiencias: List[str]
    duracion_ruta: int
    sostenibilidad: str
    transporte: List[str]
    tiempo_transporte: str
    nivel_actividad: str
    compania: str
    presupuesto: int


@app.post("/predict_cluster/")
async def predict_cluster(data: dict):
    """Recibe datos de un usuario y devuelve el clúster predicho."""
    cluster = predecir_cluster(data)
    return {"cluster": cluster}

@app.post("/get_recomendaciones/")
async def get_recomendaciones(data: UsuarioDatos):
    generador = GeneradorRecomendaciones()
    recomendaciones = generador.generar_recomendaciones(data.dict())
    return recomendaciones
