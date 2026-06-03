from apps.seguridad_administracion.vigilante.models import Area

def obtener_areas_activas():
    """Obtiene todas las áreas activas ordenadas por nombre"""
    return Area.objects.filter(activo=1).order_by('nombre')