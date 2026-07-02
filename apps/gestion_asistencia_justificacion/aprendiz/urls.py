# apps/gestion_asistencia_justificacion/aprendiz/urls.py

from django.urls import path
from . import views

app_name = 'aprendiz'

urlpatterns = [
    path('consultar-asistencia/', views.consultar_asistencia, name='consultar_asistencia'),
    path('radicar-justificacion/', views.radicar_justificacion, name='radicar_justificacion'),
    path('solicitar-peticion/', views.solicitar_peticion, name='solicitar_peticion'),
]