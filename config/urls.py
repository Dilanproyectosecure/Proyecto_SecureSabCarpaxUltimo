"""
URL configuration for config project.
"""

print("✅ Cargando URLs principales...")
print("   - Incluyendo instructor URLs")

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.login.views import landing_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_page, name='landing'),    
    # Nuestras apps
    path('login/', include('apps.login.urls')),  
    path('aprendiz/', include('apps.gestion_asistencia_justificacion.aprendiz.urls')),
    path('instructor/', include('apps.gestion_asistencia_justificacion.instructor.urls')),
    path('coordinador/', include('apps.reporte_monitoreo.coordinador.urls')),
    path('vigilante/', include('apps.seguridad_administracion.vigilante.urls')),
    path('gestor_sistema/', include('apps.gestor_sistema.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    