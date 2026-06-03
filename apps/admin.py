from django.contrib import admin

# Register your models here.

from django.contrib import admin
from apps.reporte_monitoreo.coordinador.models import AsistenciaSede

@admin.register(AsistenciaSede)
class AsistenciaSedeAdmin(admin.ModelAdmin):
    list_display = ('id_asistencia', 'id_usuario', 'fecha', 'estado_asistencia')