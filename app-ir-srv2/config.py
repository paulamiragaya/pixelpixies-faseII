# app/config.py
import pandas as pd

rutas_df = pd.read_csv("data/csv_originales/rutas_turisticas.csv")
transporte_df = pd.read_csv("data/csv_originales/uso_transporte.csv")
hoteles_df = pd.read_csv("data/csv_originales/ocupacion_hotelera.csv")
sostenibilidad_df = pd.read_csv("data/csv_originales/datos_sostenibilidad.csv")

