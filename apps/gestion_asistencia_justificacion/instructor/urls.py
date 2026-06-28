# apps/gestion_asistencia_justificacion/instructor/urls.py

print("[OK] instructor/urls.py se está cargando correctamente")
print(f"   Namespace: instructor")
print(f"   URLs registradas: fichas_instructor, gestionar_asistencia")

from django.urls import path
from . import views

app_name = 'instructor'  # ← NAMESPACE

urlpatterns = [
    path('fichas/', views.fichas_instructor, name='fichas_instructor'),
    path('fichas/gestionar-asistencia/', views.gestionar_asistencia, name='gestionar_asistencia'),
    path('actualizar-aprendiz/', views.actualizar_aprendiz, name='actualizar_aprendiz'),
    path('consultar-asistenciaI/', views.consultar_asistenciaI, name='consultar_asistenciaI'),
    path('gestionar-justificaciones/', views.gestionar_justificaciones, name='gestionar_justificaciones'),
    path('procesar-justificacion/', views.procesar_justificacion, name='procesar_justificacion'),
    path('habilitar-carga/', views.habilitar_carga, name='habilitar_carga'),
    path('notificar-llamado/<int:llamado_id>/', views.reenviar_notificacion_llamado, name='reenviar_notificacion_llamado'),
    path('notificar-aprendiz/', views.notificar_aprendiz, name='notificar_aprendiz'),
    path('enviar-correos-inasistencia/', views.enviar_correos_inasistencia_view, name='enviar_correos_inasistencia'),
    path('enviar-correo-retardo/', views.enviar_correo_retardo_view, name='enviar_correo_retardo'),
    path('dismiss-llamado/<int:llamado_id>/', views.dismiss_llamado, name='dismiss_llamado'),
]