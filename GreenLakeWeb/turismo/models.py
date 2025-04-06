import requests
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class Hotel(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=500, default="No hay descripcion algo no va bien...")
    foto = models.CharField(max_length=200, default="Aún no hay foto")

    def __str__(self):
        return self.nombre
    
class DatosHotel(models.Model):
    nombre = models.ForeignKey(Hotel,  null=True, blank=True, on_delete=models.SET_NULL)
    fecha = models.DateField()
    reservas_confirmadas = models.IntegerField()
    precio_promedio = models.DecimalField(max_digits=10, decimal_places=2)
    tasa_ocupacion = models.DecimalField(max_digits=5, decimal_places=2)
    cancelaciones = models.IntegerField()
    consumo_energia_kwh = models.IntegerField()
    residuos_generados_kg = models.IntegerField()
    porcentaje_reciclaje = models.DecimalField(max_digits=5, decimal_places=2)
    uso_agua_m3 = models.IntegerField()

    def __str__(self):
        return f"{self.nombre} - {self.fecha}"
    
class Servicio(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Usuario(AbstractUser):  
    TIPO_USUARIO_CHOICES = [
        ('Turista', 'Turista'),
        ('Hotelero', 'Hotelero'),
        ('Empresario', 'Empresario')
    ]
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO_CHOICES, default='Turista')
    hotel_asignado = models.ForeignKey(Hotel, null=True, blank=True, on_delete=models.SET_NULL)
    servicio_asignado = models.ForeignKey(Servicio, null=True, blank=True, on_delete=models.SET_NULL) 
    verificado = models.BooleanField(default=False)
    cluster = models.IntegerField(default=999)
    
    def __str__(self):
        return f"{self.username} ({self.tipo_usuario})"

class Ruta(models.Model):
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)
    duracion_hr = models.DecimalField(max_digits=5, decimal_places=2)
    longitud_km = models.DecimalField(max_digits=5, decimal_places=2)
    popularidad = models.DecimalField(max_digits=3, decimal_places=2)

    def __str__(self):
        return self.nombre

class Transporte(models.Model):
    fecha = models.DateField()
    tipo_transporte = models.CharField(max_length=50)
    num_usuarios = models.IntegerField()
    tiempo_viaje_min = models.IntegerField()
    ruta_popular = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.tipo_transporte.nombre} - {self.fecha}"

class OpinionServicio(models.Model):
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)
    puntuacion = models.IntegerField()
    comentario = models.TextField()
    sentimiento = models.CharField(max_length=10, blank=True, null=True)  
    keywords = models.JSONField(null=True, blank=True)
    fecha = models.DateField(auto_now_add=True)  

    def __str__(self):
        return f"{self.servicio.nombre} - ({self.fecha})"
    
class OpinionHotel(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    puntuacion = models.IntegerField()
    comentario = models.TextField()
    sentimiento = models.CharField(max_length=10, blank=True, null=True) 
    keywords = models.JSONField(null=True, blank=True) 
    fecha = models.DateField(auto_now_add=True) 

    def __str__(self):
        return f"{self.hotel.nombre} -  ({self.fecha})"
    
class OpinionRuta(models.Model):
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE)
    puntuacion = models.IntegerField()
    comentario = models.TextField()
    sentimiento = models.CharField(max_length=10, blank=True, null=True)
    keywords = models.JSONField(null=True, blank=True) 
    fecha = models.DateField(auto_now_add=True) 

    def __str__(self):
        return f"{self.ruta.nombre} - ({self.fecha})"

class GreenPoints(models.Model):
    usuario = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.CASCADE)
    hotel = models.ForeignKey(Hotel, null=True, blank=True, on_delete=models.CASCADE)
    servicio = models.ForeignKey(Servicio, null=True, blank=True, on_delete=models.CASCADE)
    puntos = models.IntegerField(default=0)
    fecha = models.DateField(auto_now_add=True) 

    def __str__(self):
        return f"{self.puntos} GreenPoints"
    
class PreferenciasUsuario(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    experiencias = models.JSONField()  
    duracion_ruta = models.IntegerField()
    sostenibilidad = models.CharField(max_length=30)
    transporte = models.JSONField()  
    tiempo_transporte = models.CharField(max_length=50)
    nivel_actividad = models.CharField(max_length=20)
    compania = models.CharField(max_length=30)
    presupuesto = models.IntegerField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Preferencias de {self.usuario.username}"
    
class ReservaHotel(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    fecha_reserva = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, default="pendiente") 
    puede_opinar = models.BooleanField(default=False)

    def __str__(self):
        return f"Reserva: {self.usuario.username}: {self.hotel.nombre} ({self.fecha_reserva})"
    
class MarketingImage(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/marketing_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Marketing {self.hotel}"
    
class Recomendacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    cluster = models.IntegerField(default=999)
    recomendaciones = models.JSONField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recomendaciones de {self.usuario.username} (Cluster {self.cluster})"
    
    @staticmethod
    def agrupar_recomendaciones_por_categoria(recomendaciones_dict):
        rutas_por_categoria = {}
        for ruta, data in recomendaciones_dict.items():
            categoria = data["categoria"]
            if categoria not in rutas_por_categoria:
                rutas_por_categoria[categoria] = {}

            transportes_combinados = []
            for tipo, ida in data["transportes_ida"].items():
                vuelta = data["transportes_vuelta"].get(tipo, [])
                transportes_combinados.append({
                    "tipo": tipo,
                    "ida": ida,
                    "vuelta": vuelta
                })

            rutas_por_categoria[categoria][ruta] = {
                "tipo_ruta": data["tipo_ruta"],
                "transportes_combinados": transportes_combinados,
                "hoteles_recomendados": data["hoteles_recomendados"],
                "otros_hoteles": data["otros_hoteles"],
                "no_hay_hoteles": data["no_hay_hoteles"]
            }

        return rutas_por_categoria