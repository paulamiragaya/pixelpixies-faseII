import random
import pandas as pd
import sys
from config import rutas_df, transporte_df, hoteles_df, sostenibilidad_df

class GeneradorRecomendaciones:
    def __init__(self):
        self.rutas_df = rutas_df
        self.uso_transporte_df = transporte_df
        self.ocupacion_hotelera_df = hoteles_df
        self.datos_sostenibilidad_df = sostenibilidad_df

        self.puntuaciones_dict = self.calcular_puntuacion_sostenibilidad(self.datos_sostenibilidad_df)
        self.rutas_df["categoria_ruta"] = self.rutas_df["longitud_km"].apply(self.clasificar_rutas)

    def cargar_csv(self, path):
        """Carga los archivos CSV y maneja errores"""
        try:
            return pd.read_csv(path)
        except Exception as e:
            return self.render_error(f"Error al cargar archivo CSV: {str(e)}")

    def clasificar_rutas(self, longitud_km):
        """Clasifica las rutas en cortas, medias y largas"""
        if longitud_km < 30:
            return "Corta"
        elif 30 <= longitud_km < 60:
            return "Media"
        else:
            return "Larga"

    def calcular_puntuacion_sostenibilidad(self, datos_sostenibilidad):
        """Calcula la puntuación de sostenibilidad para cada hotel"""
        puntuaciones_dict = {}
        for _, row in datos_sostenibilidad.iterrows():
            puntuacion = (
                (100 - row["consumo_energia_kwh"] / 50) +
                (100 - row["residuos_generados_kg"] / 20) +
                (row["porcentaje_reciclaje"] * 2) +
                (100 - row["uso_agua_m3"] / 50)
            ) / 4
            puntuaciones_dict[row["hotel_nombre"]] = puntuacion
        return puntuaciones_dict

    def clasificar_transportes_por_opciones(self, transportes, transportes_preferidos):
        """Clasifica los transportes según las opciones preferidas del usuario y agrega un grupo extra con opciones sostenibles."""
        
        transportes_clasificados = {tipo: [] for tipo in transportes_preferidos}
        
        opciones_sostenibles = ["Bicicleta", "Metro", "Tranvía"]
        transportes_sostenibles = pd.DataFrame()

        transportes_filtrados = transportes[transportes["tipo_transporte"].isin(transportes_preferidos)]

        transportes_agrupados = transportes_filtrados.groupby(["tipo_transporte", "ruta_popular", "origen", "destino"])["tiempo_viaje_promedio_min"].mean().reset_index()
        transportes_ordenados = transportes_agrupados.sort_values(["tipo_transporte", "tiempo_viaje_promedio_min"])

        top_transportes = transportes_ordenados.groupby("tipo_transporte").head(5)

        for tipo in transportes_clasificados:
            transportes_clasificados[tipo] = top_transportes[top_transportes["tipo_transporte"] == tipo].to_dict(orient="records")

        transportes_sostenibles = transportes[transportes["tipo_transporte"].isin(opciones_sostenibles)]
        transportes_sostenibles = transportes_sostenibles.sort_values(["tipo_transporte", "tiempo_viaje_promedio_min"])

        bicicletas = transportes_sostenibles[transportes_sostenibles["tipo_transporte"] == "Bicicleta"]
        bicicletas_agrupadas = bicicletas.groupby(["tipo_transporte", "ruta_popular", "origen", "destino"])["tiempo_viaje_promedio_min"].mean().reset_index()

        otros_transportes = transportes_sostenibles[transportes_sostenibles["tipo_transporte"] != "Bicicleta"]
        otros_transportes_agrupados = otros_transportes.groupby(["tipo_transporte", "ruta_popular", "origen", "destino"])["tiempo_viaje_promedio_min"].mean().reset_index()

        bicicletas_top = (bicicletas_agrupadas.groupby("tipo_transporte").head(10))
        otros_transportes_top = (otros_transportes_agrupados.groupby("tipo_transporte").head(5))

        transportes_finales = pd.concat([bicicletas_top, otros_transportes_top])
        transportes_finales = transportes_finales.sort_values(by=["tipo_transporte", "tiempo_viaje_promedio_min"])

        transportes_clasificados["Algunas opciones sostenibles!"] = transportes_finales.sample(n=min(5, len(transportes_finales))).to_dict(orient="records")
                
        return transportes_clasificados

    def obtener_transportes_para_ruta(self, ruta, transportes_preferidos):
        """Obtiene los transportes de ida y vuelta para cada ruta"""
        nombre_ruta, _ = ruta.split(" - ")
        self.uso_transporte_df[['origen', 'destino']] = self.uso_transporte_df['ruta_popular'].str.split(" - ", expand=True)

        transportes_ida = self.uso_transporte_df[self.uso_transporte_df['destino'].str.contains(nombre_ruta, case=False, na=False)]
        transportes_vuelta = self.uso_transporte_df[self.uso_transporte_df['origen'].str.contains(nombre_ruta, case=False, na=False)]

        transportes_ida = self.clasificar_transportes_por_opciones(transportes_ida, transportes_preferidos)
        transportes_vuelta = self.clasificar_transportes_por_opciones(transportes_vuelta, transportes_preferidos)
        
        return {"transportes_ida": transportes_ida,"transportes_vuelta": transportes_vuelta}

    def obtener_hoteles_categoria(self, ubicaciones_transporte, precio_promedio_usuario):
        """Obtiene los hoteles recomendados para las categorías de transporte (rápidos, tiempo medio, lentos)"""
        
        lugares_alojamiento = set()

        def agregar_transportes_y_hoteles(transporte, categoria):
            origen = transporte['origen']
            destino = transporte['destino']
            lugares_alojamiento.add(origen)
            lugares_alojamiento.add(destino)

        for tipo_categoria, transportes in ubicaciones_transporte['transportes_ida'].items():
            for transporte in transportes:
                agregar_transportes_y_hoteles(transporte, tipo_categoria)

        for tipo_categoria, transportes in ubicaciones_transporte['transportes_vuelta'].items():
            for transporte in transportes:
                agregar_transportes_y_hoteles(transporte, tipo_categoria)

        hoteles_finales = {}
        hoteles_asignados = set()
        otros_hoteles = {}
        for lugar in lugares_alojamiento:
            
            hoteles_lugar = self.ocupacion_hotelera_df[(self.ocupacion_hotelera_df["hotel_nombre"].str.split().str[0] == lugar.split()[0])]
            
            if not hoteles_lugar.empty:
                hoteles_agrupados = hoteles_lugar.groupby("hotel_nombre")["precio_promedio_noche"].mean().reset_index()
                hoteles_filtrados = hoteles_agrupados[(hoteles_agrupados["precio_promedio_noche"] >= precio_promedio_usuario - 10) & 
                                                  (hoteles_agrupados["precio_promedio_noche"] <= precio_promedio_usuario + 10)]
                hoteles_finales[lugar] = hoteles_filtrados.to_dict(orient='records')
                otros_hoteles[lugar] = hoteles_agrupados.to_dict(orient='records')

        no_hay_hoteles = False  
        for categoria, hoteles_categoria in hoteles_finales.items():
            if not hoteles_categoria:
                no_hay_hoteles = True
                continue
            for hotel in hoteles_categoria:
                hotel_nombre = hotel["hotel_nombre"]
                hotel["puntuacion_sostenibilidad"] = self.puntuaciones_dict.get(hotel_nombre, 0)
            
            hoteles_finales[categoria].sort(key=lambda x: x["puntuacion_sostenibilidad"], reverse=True)
        
        for categoria, hoteles_categoria in otros_hoteles.items():
            for hotel in hoteles_categoria:
                hotel_nombre = hotel["hotel_nombre"]
                hotel["puntuacion_sostenibilidad"] = self.puntuaciones_dict.get(hotel_nombre, 0)
            
            otros_hoteles[categoria].sort(key=lambda x: x["puntuacion_sostenibilidad"], reverse=True)

        return hoteles_finales, otros_hoteles, no_hay_hoteles

    def generar_recomendaciones(self, usuario):
        """Genera las recomendaciones de transportes y hoteles"""
        recomendaciones = {}
       
        interes_viaje = [t.strip() for t in usuario["experiencias"]] if usuario["experiencias"] else []
        if "Ecológica" not in interes_viaje: interes_viaje.append("Ecológica")
        if usuario["compania"] == "Con familia" or usuario["compania"] == "Grupo organizado":
            interes_viaje.append("Cultural")
            interes_viaje.append("Histórica")
        if usuario["compania"] == "Con amigos" or usuario["compania"] == "En pareja":
            interes_viaje.append("Aventura")

        precio_promedio_usuario = usuario["presupuesto"]

        rutas_interes = self.rutas_df[self.rutas_df["tipo_ruta"].isin(interes_viaje)]

        rutas_cortas = rutas_interes[rutas_interes["categoria_ruta"] == "Corta"].sort_values(by="popularidad", ascending=False).head(5)
        rutas_medias = rutas_interes[rutas_interes["categoria_ruta"] == "Media"].sort_values(by="popularidad", ascending=False).head(5)
        rutas_largas = rutas_interes[rutas_interes["categoria_ruta"] == "Larga"].sort_values(by="popularidad", ascending=False).head(5)

        transportes_preferidos = [t.strip() for t in usuario["transporte"]] if usuario["transporte"] else []
        for categoria, rutas in {"RUTAS CORTAS": rutas_cortas, "RUTAS MEDIAS": rutas_medias, "RUTAS LARGAS": rutas_largas}.items():
            for ruta in rutas.itertuples():
                transportes = self.obtener_transportes_para_ruta(ruta.ruta_nombre, transportes_preferidos)
                hoteles, otros_hoteles, no_hay_hoteles  = self.obtener_hoteles_categoria(transportes, precio_promedio_usuario)
                
                recomendaciones[str(ruta.ruta_nombre)] = {
                    "tipo_ruta": ruta.tipo_ruta,
                    "categoria": categoria,
                    "transportes_ida": transportes["transportes_ida"],
                    "transportes_vuelta": transportes["transportes_vuelta"],
                    "hoteles_recomendados": hoteles,
                    "otros_hoteles": otros_hoteles,
                    "no_hay_hoteles":no_hay_hoteles
                }
        
        return recomendaciones