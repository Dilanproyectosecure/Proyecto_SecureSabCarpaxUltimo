from django.urls import include, path
from . import views

app_name = 'gestor_sistema' 
urlpatterns = [
    path('admin-sistema/', views.panel_admin, name='panel_admin'),
    path('registrar-huella/<int:id_usuario>/', views.registrar_huella_view, name='registrar_huella'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('monitoreo/', views.monitoreo_huellas, name='monitoreo'),
    path('descargar-reporte-sede/', views.descargar_reporte_sede, name='descargar_reporte_sede'),
    path('asistencia-ambiente/', views.asistencia_ambiente, name='asistencia_ambiente'),
    path('asistencia-sede/', views.asistencia_sede, name='asistencia_sede'),
    path('verificar-huella/', views.verificar_ultima_huella, name='verificar_huella'),
    path('exportar-asistencia-csv/', views.exportar_asistencia_csv, name='exportar_csv'),
    path('reportes/', views.reportes, name='reportes'),
    path('registro-actividad/', views.registro_view, name='registro_actividad'),
    path('perfil/', views.perfil_view, name='mi_perfil'),
    path('crear-usuario/', views.crear_usuario, name='crear_usuario'), 
    path('reportes/asistencia-ambientes/excel/', views.exportar_ambientes_excel, name='exportar_ambientes_excel'),
    path('sincronizar-asistencia/', views.sincronizar_asistencia, name='sincronizar_asistencia'),
    path('desactivar-usuario/<int:id_usuario>/', views.desactivar_usuario, name='desactivar_usuario'),
    path('activar-usuario/<int:id_usuario>/', views.activar_usuario, name='activar_usuario'),
    path('editar-usuario/<int:id_usuario>/', views.editar_usuario, name='editar_usuario'),
]