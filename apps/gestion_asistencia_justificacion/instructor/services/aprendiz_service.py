from apps.login.models import Usuarios


def actualizar_datos_aprendiz(user_id, campo, valor):
    """
    Actualiza datos básicos de un aprendiz
    """

    usuario = Usuarios.objects.get(id_usuario=user_id)

    if campo == 'correo':
        usuario.correo = valor

    elif campo == 'telefono':
        usuario.telefono = valor

    else:
        raise ValueError("Campo no válido")

    usuario.save()

    return usuario