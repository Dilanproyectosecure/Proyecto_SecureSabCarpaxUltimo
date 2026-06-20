from django.urls import path
from . import views

app_name = 'coordinador'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('asistencia-ambiente/', views.asistencia_ambiente, name='asistencia_ambiente'),
    path('asistencia-ambiente/exportar/csv/', views.exportar_asistencia_ambiente_csv, name='exportar_asistencia_ambiente_csv'),
    path('asistencia-ambiente/exportar/pdf/', views.exportar_asistencia_ambiente_pdf, name='exportar_asistencia_ambiente_pdf'),
    path('asistencia-sede/', views.asistencia_sede, name='asistencia_sede'),
    path('asistencia-sede/exportar/csv/', views.exportar_asistencia_sede_csv, name='exportar_asistencia_sede_csv'),
    path('asistencia-sede/exportar/pdf/', views.exportar_asistencia_sede_pdf, name='exportar_asistencia_sede_pdf'),
    path('justificaciones/', views.justificaciones, name='justificaciones'),
    path('aprendiz/<int:usuario_id>/', views.detalle_aprendiz, name='detalle_aprendiz'),
]
