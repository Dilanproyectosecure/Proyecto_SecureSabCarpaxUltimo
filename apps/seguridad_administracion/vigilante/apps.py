from django.apps import AppConfig

class VigilanteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.seguridad_administracion.vigilante'  # ¡Esta es la clave!
    verbose_name = 'Módulo Vigilante'