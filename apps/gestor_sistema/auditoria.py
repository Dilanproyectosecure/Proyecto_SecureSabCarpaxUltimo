# apps/gestor_sistema/auditoria.py

from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import registro_actividad


def registrar_actividad(
    request,
    usuario,
    actividad,
    tipo_accion,
    descripcion=""
):
    registro_actividad.objects.create(
        id_usuario=usuario,
        actividad=actividad,
        tipo_accion=tipo_accion,
        descripcion=descripcion,
        fecha=timezone.now().date(),
        hora=timezone.now().time(),
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )


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