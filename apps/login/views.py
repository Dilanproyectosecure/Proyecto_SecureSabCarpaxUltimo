# apps/autenticacion/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.login.models import Usuarios, RoleUser
from apps.reporte_monitoreo.coordinador.models import AsistenciaAmbiente, Competencia, Justificacion
from django.views.decorators.cache import never_cache
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
import time
from apps.gestor_sistema.services import registrar_actividad


from .forms import RecuperarForm, ConfirmarCodigoForm, NuevaPasswordForm
from .utils import generar_codigo_recuperacion, enviar_codigo_recuperacion, generar_token_seguro
from apps.login.models import Usuarios



def login_view(request):
    """
    Vista de login - Autenticación con cédula y contraseña
    """
    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        password = request.POST.get('password')
        
        # Verificar si el usuario existe pero está inactivo
        try:
            usuario_check = Usuarios.objects.filter(cedula=cedula).first()
            if usuario_check and not usuario_check.is_active:
                messages.error(request, 'Usuario inactivo, comuníquese con el gestor')
                return render(request, 'login.html', {'error': 'Usuario inactivo, comuníquese con el gestor'})
        except Usuarios.DoesNotExist:
            pass

        # Intento de autenticación con Django
        user = authenticate(request, username=cedula, password=password)
        
        if user:
            # Login exitoso
            login(request, user)
            
            # Obtener el rol del usuario
            rol = user.get_rol()
            
            # Guardar rol en sesión
            request.session['user_rol'] = rol

             # ✅ REGISTRAR INICIO DE SESIÓN
            registrar_actividad(
                usuario=user,
                tipo_accion='LOGIN',
                actividad='Inicio de sesión',
                descripcion=f'Usuario {user.nombre} {user.apellido} inició sesión correctamente',
                request=request
            )
            
            # Redirigir según el rol
            if rol == 'aprendiz':
                messages.success(request, f'¡Bienvenido {user.nombre}!')
                return redirect('aprendiz:consultar_asistencia')
            elif rol == 'instructor':
                messages.success(request, f'¡Bienvenido Instructor {user.nombre}!')
                return redirect('instructor:fichas_instructor')
            elif rol == 'coordinador':
                messages.success(request, f'¡Bienvenido Coordinador {user.nombre}!')
                return redirect('coordinador:inicio')
            elif rol == 'vigilante':
                messages.success(request, f'¡Bienvenido Vigilante {user.nombre}!')
                return redirect('vigilante:iniciov')
            elif rol == 'gestor':
                messages.success(request, f'¡Bienvenido Gestor {user.nombre}!')
                return redirect('gestor_sistema:crear_usuario')
            else:
                # Si no tiene rol, redirigir a home genérico
                messages.warning(request, 'Usuario sin rol asignado')
                return redirect('login:mi_perfil')
        else:
             # ✅ REGISTRAR INTENTO FALLIDO
            registrar_actividad(
                usuario=None,
                tipo_accion='LOGIN_FAILED',
                actividad='Intento de inicio fallido',
                descripcion=f'Intento fallido con cédula {cedula}',
                request=request
            )
            # Login fallido
            messages.error(request, 'Cédula o contraseña incorrectos')
    
    # GET - Mostrar formulario de login
    return render(request, 'login.html', {
        'error': 'Cédula o contraseña incorrectos' if request.method == 'POST' else None
    })

@login_required
def logout_view(request):
    user = request.user
    nombre = f"{user.nombre} {user.apellido}"
    """
    Vista para cerrar sesión
    """
     # ✅ REGISTRAR CIERRE DE SESIÓN
    
    registrar_actividad(
        usuario=user,
        tipo_accion='LOGOUT',
        actividad='Cierre de sesión',
        descripcion=f'Usuario {user.nombre} {user.apellido}  cerró sesión',
        request=request
    )

    logout(request)
    messages.success(request, 'Sesión cerrada correctamente')
    return redirect('login:login')


@login_required
def mi_perfil(request):
    """
    Vista del perfil de usuario (accesible para todos los roles)
    """
    usuario = Usuarios.objects.select_related('id_coordinacion').get(id_usuario=request.user.id_usuario)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'actualizar_perfil':
            nombre = request.POST.get('nombre', '').strip()
            apellido = request.POST.get('apellido', '').strip()
            telefono = request.POST.get('telefono', '').strip()
            correo = request.POST.get('correo', '').strip()
            cedula = request.POST.get('cedula', '').strip()

            errores = []

            if cedula and cedula != usuario.cedula:
                if Usuarios.objects.filter(cedula=cedula).exclude(id_usuario=usuario.id_usuario).exists():
                    errores.append(f'Ya existe otro usuario con la cédula {cedula}')

            if correo and correo != usuario.correo:
                if Usuarios.objects.filter(correo=correo).exclude(id_usuario=usuario.id_usuario).exists():
                    errores.append(f'Ya existe otro usuario con el correo {correo}')

            if telefono and telefono != usuario.telefono:
                if Usuarios.objects.filter(telefono=telefono).exclude(id_usuario=usuario.id_usuario).exists():
                    errores.append(f'Ya existe otro usuario con el teléfono {telefono}')

            if errores:
                for e in errores:
                    messages.error(request, e)
                return redirect('login:mi_perfil')

            usuario.nombre = nombre or usuario.nombre
            usuario.apellido = apellido or usuario.apellido
            usuario.telefono = telefono or usuario.telefono
            usuario.correo = correo or usuario.correo
            usuario.cedula = cedula or usuario.cedula
            usuario.save()

            registrar_actividad(
                usuario=request.user,
                tipo_accion='UPDATE',
                actividad='Actualización de perfil',
                descripcion='El usuario actualizó su perfil',
                request=request,
            )

            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('login:mi_perfil')

        elif action == 'cambiar_password':
            password_actual = request.POST.get('password_actual', '')
            password_nueva = request.POST.get('password_nueva', '')
            password_confirm = request.POST.get('password_confirm', '')

            if not usuario.check_password(password_actual):
                messages.error(request, 'La contraseña actual no es correcta.')
                return redirect('login:mi_perfil')

            if len(password_nueva) < 6:
                messages.error(request, 'La nueva contraseña debe tener al menos 6 caracteres.')
                return redirect('login:mi_perfil')

            if password_nueva != password_confirm:
                messages.error(request, 'Las contraseñas nuevas no coinciden.')
                return redirect('login:mi_perfil')

            usuario.set_password(password_nueva)
            usuario.save()

            registrar_actividad(
                usuario=request.user,
                tipo_accion='UPDATE',
                actividad='Cambio de contraseña',
                descripcion='El usuario cambió su contraseña',
                request=request,
            )

            messages.success(request, 'Contraseña cambiada correctamente.')
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, usuario)
            return redirect('login:mi_perfil')

    return render(request, 'mi_perfil.html', {
        'usuario': usuario
    })


def landing_page(request):
    """Página de inicio del sistema (landing page)"""
    return render(request, 'landing.html')


@never_cache
def recuperar(request):
    """Paso 1: Ingresar correo para recuperación"""
    if request.method == 'POST':
        form = RecuperarForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            usuario = form.usuario
            
            # Generar código y guardar en sesión
            codigo = generar_codigo_recuperacion()
            request.session[f'recuperacion_{email}'] = {
                'codigo': codigo,
                'usuario_id': usuario.id_usuario,
                'timestamp': time.time()
            }
            
            # Enviar correo
            enviado, error_envio = enviar_codigo_recuperacion(email, codigo)
            if enviado:
                messages.success(request, f'Se ha enviado un código de verificación a {email}')
                return redirect('login:recuperar_confirmar', email=email)
            else:
                detalle_error = f' Detalle: {error_envio}' if settings.DEBUG and error_envio else ''
                messages.error(request, f'Error al enviar el correo. Intenta nuevamente.{detalle_error}')
    else:
        form = RecuperarForm()
    
    return render(request, 'recuperar.html', {'form': form})


@never_cache
def recuperar_confirmar(request, email):
    """Paso 2: Ingresar código de verificación"""
    # Verificar que el email está en proceso de recuperación
    datos = request.session.get(f'recuperacion_{email}')
    if not datos:
        messages.error(request, 'La sesión de recuperación ha expirado. Por favor, inicia nuevamente.')
        return redirect('login:recuperar')
    
    if request.method == 'POST':
        form = ConfirmarCodigoForm(request.POST)
        if form.is_valid():
            codigo_ingresado = form.cleaned_data['codigo']
            
            if codigo_ingresado == datos['codigo']:
                # Código correcto, generar token y redirigir
                token = generar_token_seguro(email)
                request.session[f'recuperacion_token_{token}'] = {
                    'email': email,
                    'usuario_id': datos['usuario_id']
                }
                return redirect('login:recuperar_nueva_pass', token=token)
            else:
                messages.error(request, 'Código incorrecto. Verifica e intenta nuevamente.')
    else:
        form = ConfirmarCodigoForm()
    
    context = {
        'form': form,
        'email': email
    }
    return render(request, 'recuperar_confirmar.html', context)


def recuperar_nueva_pass(request, token):
    datos = request.session.get(f'recuperacion_token_{token}')
    if not datos:
        messages.error(request, 'El enlace de recuperación ha expirado')
        return redirect('login:recuperar')
    
    email = datos['email']
    usuario_id = datos['usuario_id']
    
    if request.method == 'POST':
        form = NuevaPasswordForm(request.POST)
        if form.is_valid():
            nueva_password = form.cleaned_data['password']
            
            try:
                usuario = Usuarios.objects.get(id_usuario=usuario_id)
                usuario.password = make_password(nueva_password)
                usuario.save()
                
                # Limpiar sesión
                request.session.pop(f'recuperacion_{email}', None)
                request.session.pop(f'recuperacion_token_{token}', None)
                
                messages.success(request, '✅ Contraseña actualizada correctamente')
                return redirect('login:login')
            except Usuarios.DoesNotExist:
                messages.error(request, 'Usuario no encontrado')
                return redirect('login:recuperar')
        else:
            # Mostrar errores del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = NuevaPasswordForm()
    
    context = {
        'form': form,
        'email': email
    }
    return render(request, 'recuperar_nueva_pass.html', context)


@never_cache
def reenviar_codigo(request, email):
    """Reenviar código de verificación al mismo correo"""
    usuario_data = request.session.get(f'recuperacion_{email}')
    if not usuario_data:
        messages.error(request, 'La sesión de recuperación ha expirado. Por favor, inicia nuevamente.')
        return redirect('login:recuperar')

    try:
        usuario = Usuarios.objects.get(id_usuario=usuario_data['usuario_id'])
    except Usuarios.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('login:recuperar')

    codigo = generar_codigo_recuperacion()
    request.session[f'recuperacion_{email}'] = {
        'codigo': codigo,
        'usuario_id': usuario.id_usuario,
        'timestamp': time.time()
    }

    enviado, error_envio = enviar_codigo_recuperacion(email, codigo)
    if enviado:
        messages.success(request, f'Se ha enviado un nuevo código de verificación a {email}')
    else:
        messages.error(request, 'Error al enviar el correo. Intenta nuevamente.')

    return redirect('login:recuperar_confirmar', email=email)
