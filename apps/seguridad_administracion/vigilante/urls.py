from django.urls import path
from . import views

app_name = 'vigilante'

urlpatterns = [
    path('iniciov/', views.iniciov, name='iniciov'),
    path('consultar-invitado/', views.consultar_invitado, name='consultar_invitado'),
    path('registrar-invitado/', views.registrar_invitado, name='registrar_invitado'),
    path('entrada-invitado/<int:visitante_id>/', views.entrada_invitado, name='entrada_invitado'),
    path('salida-invitado/<int:visitante_id>/', views.salida_invitado, name='salida_invitado'),
    path('registro-manual/', views.registro_manual, name='registro_manual'),
    path('historial/', views.historial, name='historial'),
    path('api/buscar-visitante/', views.buscar_visitante_por_cedula, name='buscar_visitante'),
    path('api/consultar-usuario-sede/', views.consultar_usuario_sede_api, name='consultar_usuario_sede'),
]