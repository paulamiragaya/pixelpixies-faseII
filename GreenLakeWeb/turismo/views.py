import pandas as pd
import json
import requests
import plotly.express as px
import os
from django.conf import settings
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.db.models import Count, Q
from .forms import  CambiarRolForm
from .models import PreferenciasUsuario  
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from turismo.models import OpinionServicio, OpinionHotel, OpinionRuta, Hotel, Servicio, Usuario, Ruta, DatosHotel, ReservaHotel, MarketingImage, GreenPoints, Recomendacion
from datetime import date 
import random
import replicate
from django.db.models.functions import Length
from collections import Counter
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from dotenv import load_dotenv
from pydub import AudioSegment
from django.http import JsonResponse
from transformers import pipeline
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import tempfile
from django.db.models import Sum, Avg
import plotly.express as pxs

load_dotenv()

class CustomLoginView(LoginView):
    template_name = "login.html"

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        if user.is_superuser:
            return redirect("admin_home")
        elif user.tipo_usuario == "Hotelero" and not user.hotel_asignado:
            return redirect("asignar_hotel")
        elif user.tipo_usuario == "Hotelero":
            return redirect(reverse_lazy("dashboard_hotelero"))
        elif user.tipo_usuario == "Empresario" and not user.servicio_asignado:
            return redirect("asignar_servicio")
        elif user.tipo_usuario == "Empresario":
            return redirect("dashboard_servicio")
        return redirect(reverse_lazy("dashboard_turista"))
    
    def form_invalid(self, form):
         return self.render_to_response(
            self.get_context_data(form=form, error="Usuario o contraseña incorrectos.")
        )

def cerrar_sesion(request):
    logout(request)
    return redirect('home')

def registro(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "").strip()
        password2 = request.POST.get("password2", "").strip()
        tipo_usuario = request.POST.get("tipo_usuario", "").strip()
   
        if not username or not email or not password1 or not password2 or not tipo_usuario:
            return render(request, "registro.html", {"error": "Todos los campos son obligatorios."})

        if password1 != password2:
            return render(request, "registro.html", {"error": "Las contraseñas no coinciden."})

        if Usuario.objects.filter(username=username).exists():
            return render(request, "registro.html", {"error": "Este usuario ya está registrado."})

        usuario = Usuario.objects.create_user(username=username, email=email, password=password1, tipo_usuario=tipo_usuario)
        user = authenticate(request, username=username, password=password1)
        if user is not None:
            login(request, user)

        if tipo_usuario == "Empresario":
            return redirect("asignar_servicio")
        elif tipo_usuario == "Hotelero":
            return redirect("asignar_hotel")
        return redirect("home")  

    return render(request, "registro.html")

@login_required
def verificar_empresas(request):
    if not request.user.is_superuser:
        return render(request, "error.html", {"mensaje": "Acceso denegado"})

    hoteles_existentes = Usuario.objects.filter(hotel_asignado__isnull=False, verificado=False, hotel_asignado__id__isnull=False).select_related("hotel_asignado")
    servicios_pendientes = Usuario.objects.filter(servicio_asignado__isnull=False, verificado=False).select_related("servicio_asignado")

    return render(request, "admin_verificaciones.html", {
        "hoteles_existentes": hoteles_existentes,
        "servicios_pendientes": servicios_pendientes
    })

@login_required
def espera_verificacion(request):
    return render(request, "espera_verificacion.html")

@login_required
def aprobar_asignacion(request, id, tipo):
    if not request.user.is_superuser:
        return render(request, "error.html", {"mensaje": "Acceso denegado"})

    if tipo == "hotel":
        hotel = get_object_or_404(Hotel, id=id)
        usuario = Usuario.objects.filter(hotel_asignado=hotel, verificado=False).first()

        if usuario:
            usuario.verificado = True
            usuario.save()

    elif tipo == "servicio":
        servicio = get_object_or_404(Servicio, id=id)
        usuario = Usuario.objects.filter(servicio_asignado=servicio, verificado=False).first()

        if usuario:
            usuario.verificado = True
            usuario.save()

    return redirect("verificaciones")

@login_required
def rechazar_asignacion(request, id, tipo):
    if not request.user.is_superuser:
        return render(request, "error.html", {"mensaje": "Acceso denegado"})

    if tipo == "hotel":
        hotel = get_object_or_404(Hotel, id=id)
        usuario = Usuario.objects.filter(hotel_asignado=hotel, verificado=False).first()

        if usuario:
            usuario.hotel_asignado = None 
            usuario.save()

    elif tipo == "servicio":
        servicio = get_object_or_404(Servicio, id=id)
        usuario = Usuario.objects.filter(servicio_asignado=servicio, verificado=False).first()

        if usuario:
            usuario.servicio_asignado = None
            usuario.save()

    return redirect("verificaciones")

@login_required
def asignar_hotel(request):
    hoteles = Hotel.objects.values("id", "nombre").distinct()  
    if request.method == "POST":
        hotel_id = request.POST.get("hotel_id")

        hotel = get_object_or_404(Hotel, id=hotel_id)

        request.user.hotel_asignado = hotel
        request.user.verificado = False 
        request.user.tipo_usuario = "Hotelero"
        request.user.save()

        return redirect("espera_verificacion") 

    return render(request, "asignar_hotel.html", {"hoteles": hoteles})

@login_required
def asignar_servicio(request):
    servicios = Servicio.objects.filter().distinct() 
    if request.method == "POST":
        servicio_id = request.POST.get("servicio_id")
        
        servicio = Servicio.objects.get(id=servicio_id)
        request.user.servicio_asignado = servicio
        request.user.save()
        return redirect("dashboard_servicio")

    return render(request, "asignar_servicio.html", {"servicios": servicios})

@login_required
def perfil(request):
    usuario = request.user
    if request.method == "POST":
        nueva_password = request.POST.get("nueva_password", "").strip()
        confirmar_password = request.POST.get("confirmar_password", "").strip()

        if nueva_password and nueva_password == confirmar_password:
            usuario.set_password(nueva_password)
            usuario.save()
            update_session_auth_hash(request, usuario)  
            return render(request, "perfil.html", {"usuario": usuario, "mensaje": "Contraseña actualizada correctamente."})
        else:
            return render(request, "perfil.html", {"usuario": usuario, "error": "Las contraseñas no coinciden."})

    return render(request, "perfil.html", {"usuario": usuario})

@login_required
def dashboard_servicio(request):
    usuario = request.user

    if not usuario.servicio_asignado:
        return redirect("asignar_servicio")
    elif not usuario.verificado:
        return redirect("espera_verificacion")

    servicio = usuario.servicio_asignado
    opiniones = OpinionServicio.objects.filter(servicio__nombre=servicio.nombre)

    sentimientos_validos = ['positivo', 'neutral', 'felicidad', 'enfado', 'disgusto', 'tristeza', 'sorpresa']

    conteo_sentimientos = (
        opiniones.values("sentimiento")
        .annotate(total=Count("sentimiento"))
        .order_by()
    )

    datos_sentimientos = {entry["sentimiento"]: entry["total"] for entry in conteo_sentimientos}

    for sentimiento in sentimientos_validos:
        if sentimiento not in datos_sentimientos:
            datos_sentimientos[sentimiento] = 0
 
    opiniones_recientes = opiniones.order_by("-fecha")

    palabras_positivas = []
    palabras_negativas = []

    for opinion in opiniones:
        if isinstance(opinion.keywords, list):  
            palabras = opinion.keywords
        elif isinstance(opinion.keywords, str):
            palabras = opinion.keywords.split(",")
        else:
            palabras = []

        palabras = [palabra.strip().lower() for palabra in palabras]

        if opinion.sentimiento in ["felicidad", "positivo"]:
            palabras_positivas.extend(palabras)
        else:
            palabras_negativas.extend(palabras)

    top_palabras_positivas = dict(Counter(palabras_positivas).most_common(3))
    top_palabras_negativas = dict(Counter(palabras_negativas).most_common(3))

    return render(request, "dashboard_servicio.html", {
        "hotel": servicio,
        "conteo_sentimientos": datos_sentimientos,
        "opiniones_recientes": opiniones_recientes,
        "palabras_positivas": top_palabras_positivas,
        "palabras_negativas": top_palabras_negativas
    })

@login_required
def dashboard_hotelero(request):
    usuario = request.user

    if not usuario.hotel_asignado:
        return redirect("asignar_hotel")
    elif not usuario.verificado:
        return redirect("espera_verificacion")

    hotel = usuario.hotel_asignado
    opiniones = OpinionHotel.objects.filter(hotel__nombre=hotel.nombre)

    sentimientos_validos = ['positivo', 'neutral', 'felicidad', 'enfado', 'disgusto', 'tristeza', 'sorpresa']

    conteo_sentimientos = (
        opiniones.values("sentimiento")
        .annotate(total=Count("sentimiento"))
        .order_by()
    )

    datos_sentimientos = {entry["sentimiento"]: entry["total"] for entry in conteo_sentimientos}

    for sentimiento in sentimientos_validos:
        if sentimiento not in datos_sentimientos:
            datos_sentimientos[sentimiento] = 0
 
    opiniones_recientes = opiniones.order_by("-fecha")

    palabras_positivas = []
    palabras_negativas = []

    for opinion in opiniones:
        if isinstance(opinion.keywords, list):  
            palabras = opinion.keywords
        elif isinstance(opinion.keywords, str):
            palabras = opinion.keywords.split(",")
        else:
            palabras = []

        palabras = [palabra.strip().lower() for palabra in palabras]

        if opinion.sentimiento in ["felicidad", "positivo"]:
            palabras_positivas.extend(palabras)
        else:
            palabras_negativas.extend(palabras)

    top_palabras_positivas = dict(Counter(palabras_positivas).most_common(3))
    top_palabras_negativas = dict(Counter(palabras_negativas).most_common(3))

    return render(request, "dashboard_hotelero.html", {
        "hotel": hotel,
        "conteo_sentimientos": datos_sentimientos,
        "opiniones_recientes": opiniones_recientes,
        "palabras_positivas": top_palabras_positivas,
        "palabras_negativas": top_palabras_negativas
    })

def home(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("admin_home")
        elif request.user.tipo_usuario == "Turista" and not request.user.is_superuser:
            return redirect("dashboard_turista")
        elif request.user.tipo_usuario == "Hotelero":
            return redirect("dashboard_hotelero")
        elif request.user.tipo_usuario == "Empresario":
            return redirect("dashboard_servicio")

    opiniones_positivas = OpinionHotel.objects.filter(sentimiento__icontains="felicidad").annotate(longitud_comentario=Length('comentario')).filter(longitud_comentario__lt=400)[:10]
    return render(request, 'home.html', {'reseñas': opiniones_positivas})

def hoteles(request):
    hotel_list = Hotel.objects.annotate(
        precio_promedio=Avg('datoshotel__precio_promedio'),
        tasa_ocupacion_promedio=Avg('datoshotel__tasa_ocupacion')
    ).order_by('nombre').distinct()

    paginator = Paginator(hotel_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'hoteles.html', {'page_obj': page_obj})

@login_required
def reservar_hotel(request, hotel_id):
    user = request.user
    ya_existe = ReservaHotel.objects.filter(
                usuario=user,
                hotel_id=hotel_id,
                fecha_reserva=date.today()
            ).exists()

    if ya_existe:
        messages.error(request, "Ya has realizado una reserva para este hotel hoy.")

    elif request.method == "POST":
        today = date.today()
        user = request.user
        ultimo_dia = DatosHotel.objects.filter(nombre_id=hotel_id).order_by('-fecha').first()

        if ultimo_dia:
            reservas_base = ultimo_dia.reservas_confirmadas
            precio_base = ultimo_dia.precio_promedio
            ocupacion_base = ultimo_dia.tasa_ocupacion
            cancelaciones_base = ultimo_dia.cancelaciones
            energia_base = ultimo_dia.consumo_energia_kwh
            residuos_base = ultimo_dia.residuos_generados_kg
            reciclaje_base = ultimo_dia.porcentaje_reciclaje
            agua_base = ultimo_dia.uso_agua_m3
        else:
            reservas_base = 100
            precio_base = 100
            ocupacion_base = 50.0
            cancelaciones_base = 5
            energia_base = 1000
            residuos_base = 1000
            reciclaje_base = 50
            agua_base = 2000

        datos, created = DatosHotel.objects.get_or_create(
            nombre_id=hotel_id,
            fecha=today,
            defaults={
                'reservas_confirmadas': reservas_base + random.randint(4, 6), 
                'precio_promedio': precio_base + random.randint(4, 6),
                'tasa_ocupacion': ocupacion_base + random.randint(0, 2),
                'cancelaciones': cancelaciones_base + random.randint(0, 2),
                'consumo_energia_kwh': energia_base + random.randint(0, 2),
                'residuos_generados_kg': residuos_base + random.randint(0, 2),
                'porcentaje_reciclaje': reciclaje_base + random.randint(0, 2),
                'uso_agua_m3': agua_base + random.randint(0, 2),
            }
        )

        if not created:
            datos.reservas_confirmadas += random.randint(0, 1)
            datos.save()

        ReservaHotel.objects.create(
            usuario=user,
            hotel_id=hotel_id,
            estado="pendiente",
            puede_opinar=False
        )

        messages.success(request, "¡Reserva realizada! El hotel confirmará tu estancia.")
    return redirect("dashboard_turista")

@login_required
def reservas_turista(request):
    reservas = ReservaHotel.objects.filter(usuario=request.user).select_related("hotel").order_by("-fecha_reserva")
    return render(request, "reservas_turista.html", {"reservas": reservas})

@login_required
def reservas_hotelero(request):
    user = request.user
    if not user.hotel_asignado:
        return render(request, "error.html", {"mensaje": "Todavía no tienes un hotel asignado!"})

    reservas = ReservaHotel.objects.filter(hotel=user.hotel_asignado).select_related("usuario").order_by("-fecha_reserva")
    return render(request, "reservas_hotelero.html", {"reservas": reservas})

@login_required
def confirmar_reserva(request, reserva_id):
    reserva = get_object_or_404(ReservaHotel, id=reserva_id, hotel=request.user.hotel_asignado)
    if request.method == "POST":
        reserva.estado = "confirmada"
        reserva.puede_opinar = True
        reserva.save()
        messages.success(request, f"Reserva de {reserva.usuario.username} confirmada correctamente.")
    return redirect("reservas_hotelero")

@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(ReservaHotel, id=reserva_id, hotel=request.user.hotel_asignado)
    if request.method == "POST":
        reserva.estado = "cancelada"
        reserva.puede_opinar = False
        reserva.save()
        messages.success(request, f"Reserva de {reserva.usuario.username} cancelada correctamente.")
    return redirect("reservas_hotelero")

def rutas(request):
    rutas = Ruta.objects.values("id", "nombre", "tipo", "duracion_hr", "longitud_km", "popularidad").distinct()

    return render(request, 'rutas.html' , {"rutas": rutas})

@login_required
def marketing_view(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    error = False
    if request.method == "POST":
        prompts = [
            f"Create a minimalist and innovative logo for a mug with no background. The design should focus on sustainability, green, and efficient themes. The letters should be detailed and clear. The logo should be unique and modern, symbolizing eco-friendliness and efficiency. The name of the hotel is {hotel.nombre} and i want to see the mug.",
            f"Create a minimalist and innovative logo for a white t-shirt with no sleeves. The design should be centered on the chest area with the logo visible and clear. The logo should represent sustainability, green, and efficient themes, with detailed letters. The name of the hotel is {hotel.nombre} i don't want people, arms, face"
        ]
        model = "black-forest-labs/flux-schnell"

        marketing_images_dir = os.path.join(settings.MEDIA_ROOT, 'images', 'marketing_images')
        os.makedirs(marketing_images_dir, exist_ok=True)

        for idx, prompt in enumerate(prompts, start=1):
            try:
                output = replicate.run(model, input={"prompt": prompt})
                image_url = output[0]
                image_filename = f"{hotel.nombre.replace(' ', '_')}_marketing_{timezone.now().strftime('%Y%m%d%H%M%S')}_{idx}.jpg"
                image_path = os.path.join(marketing_images_dir, image_filename)

                response = requests.get(image_url)
                if response.status_code == 200:
                    with open(image_path, 'wb') as f:
                        f.write(response.content)

                    MarketingImage.objects.create(
                        hotel=hotel,
                        image=f"images/marketing_images/{image_filename}"
                    )
            except Exception as e:
                print(f"Error generando imagen {idx}: {e}")
                error = True 

    images = MarketingImage.objects.filter(hotel=hotel).order_by('-created_at')[:2]
    
    return render(request, "marketing.html", {
        "images": images,
        "hotel": hotel,
        "MEDIA_URL": settings.MEDIA_URL,
        "error": error
    })

def opiniones(request):
    error = False
    if request.user.is_authenticated and hasattr(request.user, 'tipo_usuario') and request.user.tipo_usuario == "Turista" and request.method == "POST":
        hotel_id = request.POST.get("hotel_id")
        comentario = request.POST.get("comentario")
        puntuacion = request.POST.get("puntuacion")

        try:
            response_sent = requests.post(
                "http://snt-kwv1:8001/analyze/", 
                json={"text": comentario},  
                headers={"Content-Type": "application/json"} 
            )
            response_sent.raise_for_status()
            sentimiento = response_sent.json().get("analyzed", "")

            response_kw = requests.post(
                "http://snt-kwv1:8001/keywords/", 
                json={"text": comentario},  
                headers={"Content-Type": "application/json"} 
            )
            response_kw.raise_for_status()
            keywords = response_kw.json().get("keywords", [])
        except Exception as e:
            sentimiento = "desconocido"
            keywords = []
            print("Error llamando a la API:", e)
            error = True 

        if hotel_id and comentario and puntuacion:
            hotel = get_object_or_404(Hotel, id=hotel_id)

            OpinionHotel.objects.create(
                hotel=hotel,
                comentario=comentario,
                puntuacion=int(puntuacion),
                sentimiento=sentimiento,
                keywords=keywords
            )
            greenpoints = 10

            hotel_gp = GreenPoints.objects.filter(hotel=hotel).order_by("-fecha").first()
            if hotel_gp and hotel_gp.puntos >= 80:
                greenpoints += 5 

            GreenPoints.objects.create(
                usuario=request.user,
                puntos=greenpoints
            )

            reserva = ReservaHotel.objects.get(
                hotel_id=hotel_id,
                usuario=request.user,
                puede_opinar=True
            )
            reserva.puede_opinar = False
            reserva.save()

            messages.success(request, "¡Gracias por tu opinión!")
            return redirect("opiniones")

    hoteles = {h.id: h.nombre for h in Hotel.objects.all()}
    rutas = {r.id: r.nombre for r in Ruta.objects.all()}
    servicios = {s.id: s.nombre for s in Servicio.objects.all()}

    opiniones_servicio = [
        {
            "nombre": servicios.get(op["servicio_id"], f"Servicio {op['servicio_id']} (eliminado)"),
            "tipo": "Servicio",
            "comentario": op["comentario"],
            "puntuacion": op["puntuacion"],
            "fecha": op["fecha"]
        }
        for op in OpinionServicio.objects.values("comentario", "puntuacion", "fecha", "servicio_id")
    ]

    opiniones_hoteles = [
        {
            "nombre": hoteles.get(op["hotel_id"], f"Hotel {op['hotel_id']} (eliminado)"),
            "tipo": "Hotel",
            "comentario": op["comentario"],
            "puntuacion": op["puntuacion"],
            "fecha": op["fecha"]
        }
        for op in OpinionHotel.objects.values("comentario", "puntuacion", "fecha", "hotel_id")
    ]

    opiniones = opiniones_servicio + opiniones_hoteles
    opiniones = [op for op in opiniones if op["fecha"] is not None]
    opiniones.sort(key=lambda x: x["fecha"], reverse=True)


    reservas_opinables = None
    if request.user.is_authenticated and request.user.tipo_usuario == "Turista":
        reservas_opinables = ReservaHotel.objects.filter(
            usuario=request.user,
            estado="confirmada",
            puede_opinar=True
        ).select_related("hotel")

    return render(request, "opiniones.html", {
        "opiniones": opiniones,
        "reservas_opinables": reservas_opinables,
        "error": error
    })

@login_required
def cambiar_rol(request):
    usuario = request.user
    if request.method == 'POST':
        form = CambiarRolForm(request.POST, instance=usuario)
        if form.is_valid():
            nuevo_rol = form.cleaned_data['tipo_usuario']

            usuario.tipo_usuario = nuevo_rol
            usuario.hotel_asignado = None
            usuario.servicio_asignado = None
            usuario.verificado = False
            usuario.save()

            messages.success(request, f"Tu rol ha sido actualizado a {nuevo_rol}.")
            return redirect("perfil")
    else:
        form = CambiarRolForm(instance=usuario)

    return render(request, "cambiar_rol.html", {"form": form})

@login_required
def eliminar_cuenta(request):
    usuario = request.user
    usuario.delete()  
    return redirect("home") 

@login_required
def gestionar_usuarios(request):
    if not request.user.is_superuser:
        return render(request, "error.html", {"mensaje": "Acceso denegado"})

    usuarios = Usuario.objects.all()

    return render(request, "admin_usuarios.html", {
        "usuarios": usuarios
    })

@login_required
def eliminar_usuario(request, usuario_id):
    if request.method == "POST":
        usuario = get_object_or_404(Usuario, id=usuario_id)  
        nombre_usuario = usuario.username
        usuario.delete()  
        messages.success(request, f"Se ha eliminado correctamente a {nombre_usuario}")
        return redirect("gestionar_usuarios")  
    messages.error(request, "Método no permitido.")
    return redirect("gestionar_usuarios")
    
@login_required
def quitar_hotel(request, usuario_id):
    if request.user.is_superuser: 
        usuario = get_object_or_404(Usuario, id=usuario_id)
        nombre_usuario = usuario.username
        nombre_hotel = usuario.hotel_asignado if usuario.hotel_asignado else "N/A"
        usuario.hotel_asignado = None 
        usuario.verificado = False 
        usuario.save()
        messages.success(request, f"Se ha eliminado el hotel '{nombre_hotel}' del usuario '{nombre_usuario}'.")
        return redirect("gestionar_usuarios")
    return render(request, "error.html", {"mensaje": "No tienes permisos para realizar esta acción."})

@login_required
def quitar_servicio(request, usuario_id):
    if request.user.is_superuser: 
        usuario = get_object_or_404(Usuario, id=usuario_id)
        nombre_usuario = usuario.username
        nombre_servicio = usuario.servicio_asignado if usuario.servicio_asignado else "N/A"
        usuario.servicio_asignado = None 
        usuario.verificado = False 
        usuario.save()
        messages.success(request, f"Se ha eliminado el servicio '{nombre_servicio}' del usuario '{nombre_usuario}'.")
        return redirect("gestionar_usuarios")
    return render(request, "error.html", {"mensaje": "No tienes permisos para realizar esta acción."})

@login_required
def admin_home(request):
    if not request.user.is_superuser:
        return render(request, "error.html", {"mensaje": "Acceso denegado"})

    return render(request, "admin_home.html")

@login_required
def dashboard_turista(request):
    try:
        recomendacion = Recomendacion.objects.get(usuario=request.user)
        recomendaciones_raw = recomendacion.recomendaciones
    except Recomendacion.DoesNotExist:
        messages.info(request, "Aún no has generado tus recomendaciones. Por favor completa la encuesta.")
        return render(request, "recomendacion_encuesta.html", {
            "error": "Aún no has generado tus recomendaciones.",
            "ya_tiene_recomendaciones": False
        })
    try:
        rutas_por_categoria = Recomendacion.agrupar_recomendaciones_por_categoria(recomendaciones_raw)
    except Exception:
        messages.error(request, "No se pudieron procesar tus recomendaciones. Puede que haya un error en el sistema.")
        return redirect("recomendacion_encuesta")

    hoteles_recomendados = []
    hoteles_extra = [] 
    for categoria, rutas_categoria in rutas_por_categoria.items():
        for ruta, data in rutas_categoria.items():
            hoteles_recomendados += list(data["hoteles_recomendados"].keys())
            if all(len(h) == 0 for h in data["hoteles_recomendados"].values()):
                for lugar, sublist in data["otros_hoteles"].items():
                    for hotel in sublist:
                        hotel["lugar_origen"] = lugar
                        hoteles_extra.append(hotel)
                    
    hoteles_sostenibles = []
    hay_hoteles_sostenibles = False
    for hotel in hoteles_sostenibles:
        sostenibilidad_alta = False
        ultimo_dato = DatosHotel.objects.filter(nombre_id=hotel['id']).order_by('-fecha').first()

        if ultimo_dato:
            if (
                ultimo_dato.consumo_energia_kwh < 300 and
                ultimo_dato.residuos_generados_kg < 100 and
                ultimo_dato.porcentaje_reciclaje > 75 and
                ultimo_dato.uso_agua_m3 < 2000
            ):
                sostenibilidad_alta = True
                hay_hoteles_sostenibles = True

        hoteles_sostenibles.append([hotel, sostenibilidad_alta])


    hoteles_sostenibles = sorted(hoteles_sostenibles, key=lambda x: x[1], reverse=True)

    total_gp = GreenPoints.objects.filter(usuario=request.user).aggregate(Sum("puntos"))["puntos__sum"] or 0

    if total_gp >= 500:
        nivel = "Nivel 5"
        descuento_pct = 20
    elif total_gp >= 300:
        nivel = "Nivel 4"
        descuento_pct = 15
    elif total_gp >= 150:
        nivel = "Nivel 3"
        descuento_pct = 10
    elif total_gp >= 50:
        nivel = "Nivel 2"
        descuento_pct = 5
    else:
        nivel = "Nivel 1"
        descuento_pct = 0.0
        
    extra_filtro = []
    nombres_vistos = []

    for rr in hoteles_extra:
        if rr["hotel_nombre"] not in nombres_vistos:
            extra_filtro.append(rr)
            nombres_vistos.append(rr["hotel_nombre"])

    hoteles_agrupados_por_lugar = {}
    for hotel in extra_filtro:
        lugar = hotel["lugar_origen"]
        if lugar not in hoteles_agrupados_por_lugar:
            hoteles_agrupados_por_lugar[lugar] = []
        hoteles_agrupados_por_lugar[lugar].append(hotel)

    context = {
        "hoteles": hoteles_sostenibles,
        "otros_hoteles" : hoteles_agrupados_por_lugar,
        "hay_hoteles_sostenibles": hay_hoteles_sostenibles, 
        "rutas": rutas_por_categoria,
        "greenpoints": total_gp,
        "nivel": nivel,
        "descuento_pct": descuento_pct,
    }
    return render(request, "dashboard_turista.html", context)


from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import plotly.express as px

@login_required
def vista_clusters(request):
    if not request.user.is_superuser:
        return render(request, "error.html", {"mensaje": "Acceso denegado"})

    try:
        preferencias = PreferenciasUsuario.objects.all().values(
            'usuario__username', 'presupuesto', 'duracion_ruta', 
            'sostenibilidad', 'tiempo_transporte', 'nivel_actividad', 'compania', 'experiencias'
        )

        df = pd.DataFrame(preferencias)

        usuarios = Usuario.objects.exclude(cluster=999).filter(username__in=df['usuario__username']).values('username', 'cluster')

        cluster_dict = {user['username']: user['cluster'] for user in usuarios}

        df['cluster'] = df['usuario__username'].map(cluster_dict)

        df = df.dropna(subset=['cluster'])

        if df.empty:
            return render(request, "admin_clusters.html", {"error": True, "mensaje": "No hay datos válidos para PCA."})

        columnas_numericas = ["presupuesto", "duracion_ruta"]
        columnas_categoricas = ['sostenibilidad', 'tiempo_transporte', 'nivel_actividad', 'compania']

        df_encoded = pd.get_dummies(df[columnas_numericas + columnas_categoricas])

        X_scaled = StandardScaler().fit_transform(df_encoded)

        kmeans = KMeans(n_clusters=3, random_state=42)
        df['cluster'] = kmeans.fit_predict(X_scaled)

        for i, user in enumerate(df['usuario__username']):
            usuario = Usuario.objects.get(username=user)
            usuario.cluster = df['cluster'].iloc[i] 
            usuario.save()

        fig = px.scatter(
            df,
            x="presupuesto",
            y="duracion_ruta",
            color="cluster", 
            hover_data=["usuario__username", "experiencias", "nivel_actividad", "compania"],
            title="Clusters visualizados con K-means"
        )

        plot_div = fig.to_html(full_html=False)

        return render(request, "admin_clusters.html", {"plot_div": plot_div})

    except Exception as e:
        return render(request, "admin_clusters.html", {"error": True, "mensaje": str(e)})
    
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg
from .models import DatosHotel, Hotel
from django.contrib.auth.decorators import login_required

@login_required
def leaderboard_sostenibilidad(request):
    hotel = request.user.hotel_asignado

    if not hotel:
        return render(request, 'leaderboard.html', {
            'error': 'No tienes un hotel asignado.'
        })

    datos_hotel = DatosHotel.objects.filter(nombre=hotel)

    if not datos_hotel.exists():
        return render(request, 'leaderboard.html', {
            'hotel': hotel,
            'error': 'No hay datos disponibles para este hotel.'
        })

    datos_hotel_agregados = datos_hotel.aggregate(
        promedio_reservas=Avg('reservas_confirmadas'),
        promedio_precio=Avg('precio_promedio'),
        promedio_tasa_ocupacion=Avg('tasa_ocupacion'),
        promedio_cancelaciones=Avg('cancelaciones'),
        promedio_consumo_energia=Avg('consumo_energia_kwh'),
        promedio_residuos=Avg('residuos_generados_kg'),
        promedio_porcentaje_reciclaje=Avg('porcentaje_reciclaje'),
        promedio_uso_agua=Avg('uso_agua_m3'),
    )

    datos_otros_hoteles = DatosHotel.objects.exclude(nombre=hotel)

    datos_otros_hoteles_agregados = datos_otros_hoteles.aggregate(
        promedio_reservas=Avg('reservas_confirmadas'),
        promedio_precio=Avg('precio_promedio'),
        promedio_tasa_ocupacion=Avg('tasa_ocupacion'),
        promedio_cancelaciones=Avg('cancelaciones'),
        promedio_consumo_energia=Avg('consumo_energia_kwh'),
        promedio_residuos=Avg('residuos_generados_kg'),
        promedio_porcentaje_reciclaje=Avg('porcentaje_reciclaje'),
        promedio_uso_agua=Avg('uso_agua_m3'),
    )

    comparison_data = {
        'residuos_comparacion': {
            'mio': datos_hotel_agregados['promedio_residuos'],
            'resto': datos_otros_hoteles_agregados['promedio_residuos']
        },
        'agua_comparacion': {
            'mio': datos_hotel_agregados['promedio_uso_agua'],
            'resto': datos_otros_hoteles_agregados['promedio_uso_agua']
        },
        'energia_comparacion': {
            'mio': datos_hotel_agregados['promedio_consumo_energia'],
            'resto': datos_otros_hoteles_agregados['promedio_consumo_energia']
        },
        'reciclaje_comparacion': {
            'mio': datos_hotel_agregados['promedio_porcentaje_reciclaje'],
            'resto': datos_otros_hoteles_agregados['promedio_porcentaje_reciclaje']
        },
    }

    return render(request, 'leaderboard.html', {
        'hotel': hotel,
        'datos_hotel_agregados': datos_hotel_agregados,
        'datos_otros_hoteles_agregados': datos_otros_hoteles_agregados,
        'comparison_data': comparison_data,
    })

@csrf_exempt
def voz_assistant(request):
    if request.method == "POST" and request.FILES.get("audio"):
        audio_file = request.FILES["audio"]
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_audio:
            for chunk in audio_file.chunks():
                temp_audio.write(chunk)
            temp_path = temp_audio.name

        try:
            audio = AudioSegment.from_file(temp_path, format="webm")
            wav_path = tempfile.mktemp(suffix=".wav")
            audio.export(wav_path, format="wav")

            transcriber = pipeline("automatic-speech-recognition", model="openai/whisper-base", device=-1)

            transcription = transcriber(wav_path)
            texto = transcription['text'].lower()

            user = request.user
            total_gp = GreenPoints.objects.filter(usuario=user).aggregate(Sum("puntos"))["puntos__sum"] or 0
            hoteles = Hotel.objects.all()[:5]
            rutas_populares = Ruta.objects.order_by("-popularidad")[:3]
    
            prompt = f"""
            Usa los datos que necesites para ceñirte a lo que te preguntan
            El usuario tiene {total_gp} puntos.
            Algunos hoteles disponibles son: {', '.join(h.nombre for h in hoteles)}.
            Las rutas o actividades más populares son: {', '.join(r.nombre for r in rutas_populares)}.
            Responde todo en español y sin emoticonos
            El usuario ha dicho esto: {texto}.
            Responde de manera muy breve y directa en una frase a lo que se te pide no des datos sin que se te pidan.
            """

            system_prompt = "hablas español y eres un experto de hoteles y rutas en la ciudad de Greenlake, eres encantador y no usas emoticonos. No respondas más de 1 frase y limitate a lo que te dicen"
            output = replicate.run(
                "meta/llama-2-7b-chat",
                input={"prompt": prompt, "system_prompt": system_prompt}
            )

            respuesta = respuesta = "".join(output).strip() 

            return JsonResponse({"respuesta": respuesta})

        except Exception as e:
            return JsonResponse({"respuesta": f"Error interno: {str(e)}"})

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(wav_path):
                os.remove(wav_path)

    return JsonResponse({"respuesta": "Hmm... aún no sé cómo ayudarte con eso, ¡pero estoy aprendiendo!"})

@login_required
def recomendacion_encuesta(request):
    if request.GET.get('reiniciar') == 'true':
        Recomendacion.objects.filter(usuario=request.user).delete()

    if Recomendacion.objects.filter(usuario=request.user).exists():
        return redirect("recomendacion_resultado")

    if request.method == "POST":
        datos_usuario = {
            "experiencias": request.POST.getlist("1"),
            "duracion_ruta": int(request.POST.get("2")),
            "sostenibilidad": request.POST.get("3"),
            "transporte": request.POST.getlist("4"),
            "tiempo_transporte": request.POST.get("5"),
            "nivel_actividad": request.POST.get("6"),
            "compania": request.POST.get("7"),
            "presupuesto": int(request.POST.get("8"))
        }

        try:
            r_cluster = requests.post("http://ir-srv2:8002/predict_cluster/", json=datos_usuario)
            cluster = r_cluster.json().get("cluster")

            r_recom = requests.get("http://ir-srv2:8002/get_recomendaciones/", json=datos_usuario)
            recomendaciones = r_recom.json()

            Recomendacion.objects.update_or_create(
                usuario=request.user,
                defaults={
                    "cluster": cluster,
                    "recomendaciones": recomendaciones
                }
            )

            return redirect("recomendacion_resultado")

        except requests.RequestException:
            return render(request, "recomendacion_encuesta.html", {
                "error": True,
                "ya_tiene_recomendaciones": False
            })

    return render(request, "recomendacion_encuesta.html", {
        "ya_tiene_recomendaciones": False
    })

@login_required
def recomendacion_resultado(request):
    try:
        recomendacion = Recomendacion.objects.get(usuario=request.user)
        recomendaciones = recomendacion.recomendaciones
        cluster = recomendacion.cluster

        rutas_por_categoria = Recomendacion.agrupar_recomendaciones_por_categoria(recomendaciones)
        return render(request, "recomendacion_resultado.html", {
            "cluster": cluster,
            "recomendaciones": rutas_por_categoria,
        })

    except Recomendacion.DoesNotExist:
        return render(request, "recomendacion_encuesta.html", {
            "error": "No se encontró una recomendación para tu usuario.",
            "ya_tiene_recomendaciones": False
        })
    
@login_required
def greencard(request):
    user = request.user

    total_puntos = GreenPoints.objects.filter(usuario=user).aggregate(Sum("puntos"))["puntos__sum"] or 0
    equivalente_dinero = round(total_puntos * 0.20, 2)

    if total_puntos >= 500:
        nivel = "🌟 Nivel 5 - Embajador Verde"
        descuento = "20% de descuento en reservas"
    elif total_puntos >= 300:
        nivel = "🌿 Nivel 4 - Eco Viajero"
        descuento = "15% de descuento en reservas"
    elif total_puntos >= 150:
        nivel = "✅ Nivel 3 - Viajero Consciente"
        descuento = "10% de descuento en reservas"
    elif total_puntos >= 50:
        nivel = "🌱 Nivel 2 - Explorador Verde"
        descuento = "5% de descuento en reservas"
    else:
        nivel = "🍃 Nivel 1 - Principiante"
        descuento = "Aún sin descuentos"

    context = {
        "total_puntos": total_puntos,
        "equivalente_dinero": equivalente_dinero,
        "nivel": nivel,
        "descuento": descuento
    }

    return render(request, "greencard.html", context)


