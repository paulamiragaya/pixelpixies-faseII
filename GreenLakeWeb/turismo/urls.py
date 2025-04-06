from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import home, perfil, hoteles, rutas, opiniones,registro, cerrar_sesion, CustomLoginView, dashboard_hotelero, dashboard_turista, dashboard_servicio, asignar_hotel, asignar_servicio, verificar_empresas
from .views import aprobar_asignacion, rechazar_asignacion, espera_verificacion, leaderboard_sostenibilidad, eliminar_cuenta, gestionar_usuarios
from .views import eliminar_usuario, quitar_hotel,quitar_servicio, recomendacion_encuesta, vista_clusters, recomendacion_resultado
from .views import admin_home,cambiar_rol, reservas_turista, reservar_hotel, reservas_hotelero, confirmar_reserva, cancelar_reserva, marketing_view, voz_assistant, greencard

urlpatterns = [
    path('', home, name='home'),
    path('marketing/<int:hotel_id>/', marketing_view, name='marketing_view'),
    path("perfil/", perfil, name="perfil"),
    path('leaderboard/', leaderboard_sostenibilidad, name='leaderboard_sostenibilidad'),
    path('hoteles/', hoteles, name='hoteles'),
    path('rutas/', rutas, name='rutas'),
    path('opiniones/', opiniones, name='opiniones'),
    path('mis-reservas/', reservas_turista, name='reservas_turista'),
    path('registro/', registro, name='registro'),
    path('logout/', cerrar_sesion, name='logout'),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("dashboard/turista/", dashboard_turista, name="dashboard_turista"),
    path("dashboard/hotelero/", dashboard_hotelero, name="dashboard_hotelero"),
    path("dashboard/empresario/", dashboard_servicio, name="dashboard_servicio"),
    path("asignar-hotel/", asignar_hotel, name="asignar_hotel"),
    path("asignar-servicio/", asignar_servicio, name="asignar_servicio"),
    path('verificaciones/', verificar_empresas, name='verificaciones'),
    path("espera_verificacion/", espera_verificacion, name="espera_verificacion"),
    path("aprobar-asignacion/<int:id>/<str:tipo>/", aprobar_asignacion, name="aprobar_asignacion"),
    path("rechazar-asignacion/<int:id>/<str:tipo>/", rechazar_asignacion, name="rechazar_asignacion"),
    path("eliminar-cuenta/", eliminar_cuenta, name="eliminar_cuenta"),
    path("gestionar-usuarios/", gestionar_usuarios, name="gestionar_usuarios"),
    path("eliminar-usuario/<int:usuario_id>/", eliminar_usuario, name="eliminar_usuario"), 
    path("quitar-hotel/<int:usuario_id>/", quitar_hotel, name="quitar_hotel"),
    path("quitar-servicio/<int:usuario_id>/", quitar_servicio, name="quitar_servicio"),
    path("recomendacion/encuesta/", recomendacion_encuesta, name="recomendacion_encuesta"),
    path("recomendacion/resultado/", recomendacion_resultado, name="recomendacion_resultado"),
    path('administrator/clusters/', vista_clusters, name='vista_clusters'),
    path("administrator/home/", admin_home, name="admin_home"),
    path("cambiar_rol", cambiar_rol, name="cambiar_rol"),
    path('reservar-hotel/<int:hotel_id>/', reservar_hotel, name='reservar_hotel'),
    path('reservas', reservas_hotelero, name='reservas_hotelero'),
    path("confirmar-reserva/<int:reserva_id>/", confirmar_reserva, name="confirmar_reserva"),
    path("cancelar-reserva/<int:reserva_id>/", cancelar_reserva, name="cancelar_reserva"),
    path("asistente-voz/", voz_assistant, name="voz_assistant"),
    path("greencard/", greencard, name="greencard"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)