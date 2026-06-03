from django.utils import timezone
from .models import Huella
from .services import registrar_actividad


def registrar_huella(request, usuario):
    huella, created = Huella.objects.update_or_create(
        usuario=usuario,
        defaults={
            'tiene_huella': True,
            'fecha_registro': timezone.now(),
            'datos_huella_dactilar': 'REGISTRADA_EN_SISTEMA',
        }
    )

    registrar_actividad(
        usuario=request.user,
        tipo_accion='HUELLA_REGISTRO',
        actividad='Registro de huella',
        descripcion=f'Se registró huella para {usuario.nombre} {usuario.apellido} (cédula: {usuario.cedula})',
        request=request,
    )

    return huella


def eliminar_huella(request, usuario):
    huella = Huella.objects.filter(usuario=usuario)

    if huella.exists():
        huella.delete()

        registrar_actividad(
            usuario=request.user,
            tipo_accion='HUELLA_ELIMINAR',
            actividad='Eliminación de huella',
            descripcion=f'Se eliminó la huella de {usuario.nombre} {usuario.apellido} (cédula: {usuario.cedula})',
            request=request,
        )
        return True
    return False