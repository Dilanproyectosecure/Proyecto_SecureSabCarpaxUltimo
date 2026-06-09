# apps/gestor_sistema/auditoria.py

from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import registro_actividad



def registrar_actividad(usuario, tipo_accion, actividad, descripcion="", request=None):
    try:
        ip_address = None
        user_agent = None

        ahora = timezone.localtime(timezone.now())

        if request:
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        registro_actividad.objects.create(
            id_usuario=usuario,
            tipo_accion=tipo_accion,
            actividad=actividad,
            descripcion=descripcion,
            ip_address=ip_address,
            user_agent=user_agent,
            fecha_hora=timezone.now(),
        )

    except Exception as e:
        print(f"Error al registrar actividad: {e}")


@receiver(user_logged_in)
def login_handler(sender, request, user, **kwargs):

    registrar_actividad(
        request=request,
        usuario=user,
        actividad="Inicio de sesión",
        tipo_accion="LOGIN",
        descripcion="Ingreso exitoso al sistema"
    )


@receiver(user_logged_out)
def logout_handler(sender, request, user, **kwargs):

    if user:
        registrar_actividad(
            request=request,
            usuario=user,
            actividad="Cierre de sesión",
            tipo_accion="LOGOUT",
            descripcion="Salida del sistema"
        )