import csv
import json
import random
import re
import string
import pandas as pd

from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings

from apps.email_service import enviar_correo_seguro
from django.db import connections
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.login.models import Usuarios
from apps.reporte_monitoreo.coordinador.models import AsistenciaAmbiente as AsistenciaAmbienteReporte, AsistenciaSede as AsistenciaSedeReporte

from .hikvision_service import (
    enviar_usuario_hikvision,
    procesar_eventos,
    registrar_huella_hikvision,
    guardar_huella_en_bd,
    subir_huella_a_dispositivo,
)
from .models import HistorialFallos, Huella, registro_actividad
from apps.login.models import Roles, RoleUser
from apps.reporte_monitoreo.coordinador.models import Ficha, AsistenciaAmbiente, AsistenciaSede
from .services import (
    registrar_actividad,
    registrar_asistencia_sede_por_huella,
    crear_usuario,
    actualizar_usuario,
    eliminar_usuario,
    cambiar_estado_usuario,
)
from .usuario_huella_services import eliminar_huella as eliminar_huella_service, registrar_huella as registrar_huella_service
from .models import registro_actividad  # noqa: F811

def generar_password_segura(cedula='', nombre=''):
    if cedula and len(cedula) >= 8:
        inicial = nombre[0].upper() if nombre else 'A'
        signo = random.choice('!@#$%^&*')
        return cedula + inicial + signo
    chars = string.ascii_letters + string.digits + '!@#$%^&*'
    password = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice('!@#$%^&*'),
    ]
    password += random.choices(chars, k=6)
    random.shuffle(password)
    return ''.join(password)


def enviar_password_usuario(nombre, apellido, correo, password, cedula):
    asunto = "SecureSab - Tu cuenta ha sido creada"
    mensaje_texto = (
        f"Hola {nombre} {apellido},\n\n"
        f"Tu cuenta en SecureSab ha sido creada exitosamente.\n\n"
        f"Tu usuario es: {cedula}\n"
        f"Tu contraseña de acceso es: {password}\n\n"
        "Por favor cambia tu contraseña después de iniciar sesión.\n\n"
        "SecureSab - Sistema de Control de Asistencia SENA"
    )
    mensaje_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="background: linear-gradient(135deg, #178202 0%, #1a9e05 100%); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">SecureSab</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0;">Sistema de Control de Asistencia</p>
            </div>
            <div style="padding: 30px;">
                <h2 style="color: #333; margin-top: 0;">Hola {nombre} {apellido}</h2>
                <p>Tu cuenta en <strong>SecureSab</strong> ha sido creada exitosamente.</p>
                <p>Tu <strong>usuario</strong> es:</p>
                <div style="background: #f8f9fa; padding: 15px; text-align: center; border-radius: 8px; margin: 10px 0;">
                    <span style="font-size: 24px; font-weight: bold; letter-spacing: 3px; color: #333;">{cedula}</span>
                </div>
                <p>Tu <strong>contraseña</strong> de acceso es:</p>
                <div style="background: #f8f9fa; padding: 15px; text-align: center; border-radius: 8px; margin: 10px 0;">
                    <span style="font-size: 24px; font-weight: bold; letter-spacing: 3px; color: #178202;">{password}</span>
                </div>
                <p style="color: #e74c3c; font-weight: bold;">Por favor cambia tu contraseña después de iniciar sesión.</p>
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #999; font-size: 12px; text-align: center;">
                    SecureSab - Sistema de Control de Asistencia SENA<br>
                    Este es un correo automático, por favor no responder.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    try:
        enviar_correo_seguro(asunto, correo, mensaje_texto, mensaje_html)
        return True
    except Exception:
        return False

@login_required
def panel_admin(request):
    if request.method == "POST" and request.FILES.get('archivo_csv'):
        csv_file = request.FILES['archivo_csv']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'El archivo debe ser un formato CSV.')
            return HttpResponseRedirect(reverse('gestor_sistema:panel_admin'))

        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        creados = 0
        omitos = 0
        for row in reader:
            try:
                cedula = row.get('cedula', '').strip()
                correo = row.get('correo', '').strip()
                telefono = row.get('telefono', '').strip()
                tipo_doc = row.get('tipo_documento', '').strip()

                if Usuarios.objects.filter(cedula=cedula).exists():
                    omitos += 1
                    continue
                if Usuarios.objects.filter(correo=correo).exists():
                    omitos += 1
                    continue
                if telefono and Usuarios.objects.filter(telefono=telefono).exists():
                    omitos += 1
                    continue

                Usuarios.objects.create_user(
                    tipo_documento=tipo_doc,
                    cedula=cedula,
                    password=row.get('password') or generar_password_segura(cedula, row.get('nombre', '')),
                    nombre=row['nombre'],
                    apellido=row['apellido'],
                    correo=correo,
                    telefono=telefono,
                    estado='Activo',
                    is_active=True,
                )

                nombre_rol = row.get('rol', '').strip().lower()

                if nombre_rol:
                    rol = Roles.objects.filter(name=nombre_rol).first()
                    if rol:
                        usuario = Usuarios.objects.get(cedula=cedula)
                        with connections['default'].cursor() as cursor:
                            cursor.execute(
                                "INSERT INTO role_user (id_usuario, role_id) VALUES (%s, %s)",
                                [usuario.id_usuario, rol.id],
                            )

                password_generada = row.get('password') or generar_password_segura(cedula, row.get('nombre', ''))
                enviar_password_usuario(row['nombre'], row['apellido'], correo, password_generada, cedula)
                creados += 1
            except Exception as e:
                print(f"Error: {e}")

        if creados > 0:
            messages.success(request, f'Se crearon {creados} usuarios.')
        if omitos > 0:
            messages.warning(request, f'Se omitieron {omitos} usuarios.')
        return HttpResponseRedirect(reverse('gestor_sistema:panel_admin'))

    if request.method == "POST":
        tipo_documento = request.POST.get('tipo_documento')
        cedula = request.POST.get('cedula')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        correo = request.POST.get('correo')
        telefono = request.POST.get('telefono')
        role_id = request.POST.get('role_id') or request.POST.get('rol')
        password = request.POST.get('password') or '123'

        _name_re = re.compile(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$')
        _errores = []
        if not (cedula and cedula.isdigit() and len(cedula) > 4 and len(cedula) <= 10):
            _errores.append("La cédula debe tener entre 5 y 10 dígitos numéricos.")
        if not (nombre and 3 <= len(nombre) <= 40 and _name_re.match(nombre)):
            _errores.append("El nombre debe tener entre 3 y 40 letras.")
        if not (apellido and 3 <= len(apellido) <= 40 and _name_re.match(apellido)):
            _errores.append("El apellido debe tener entre 3 y 40 letras.")
        if _errores:
            for _e in _errores:
                messages.error(request, _e)
            return redirect('gestor_sistema:panel_admin')
        
        #vaalida la cedula pa que no se repita
        if Usuarios.objects.filter(cedula=cedula).exists():
            messages.error(request, f'Ya existe un usuario con la cédula {cedula}')
            return redirect('gestor_sistema:panel_admin')

        #valida el correo pa que no se repita
        if correo and Usuarios.objects.filter(correo=correo).exists():
            messages.error(request, f'Ya existe un usuario con el correo {correo}')
            return redirect('gestor_sistema:panel_admin')
        

        ficha_id = request.POST.get('ficha')
        nueva_ficha = request.POST.get('nueva_ficha')
        if nueva_ficha:
            ficha, _ = Ficha.objects.get_or_create(numero_ficha=nueva_ficha)
            ficha_id = ficha.id_ficha

        try:
            usuario = Usuarios.objects.create_user(
                tipo_documento=tipo_documento,
                cedula=cedula,
                password=password,
                nombre=nombre,
                apellido=apellido,
                correo=correo,
                telefono=telefono,
                estado='Activo',
                is_active=True,
            )

            if role_id:
                with connections['default'].cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO role_user (id_usuario, role_id) VALUES (%s, %s)",
                        [usuario.id_usuario, role_id],
                    )

            if ficha_id:
                usuario.id_ficha_id = ficha_id
                usuario.save(update_fields=['id_ficha_id'])

            enviar_usuario_hikvision(usuario)
            enviar_password_usuario(nombre, apellido, correo, password, cedula)
            messages.success(request, f"Usuario {nombre} creado y sincronizado correctamente.")
        except Exception as e:
            messages.error(request, f"Error al guardar: {str(e)}")

        return redirect('gestor_sistema:panel_admin')

    query = """
        SELECT
            u.*,
            r.name as nombre_rol,
            CASE WHEN EXISTS (
                SELECT 1
                FROM huella h
                WHERE h.id_usuario = u.id_usuario
            ) THEN 1 ELSE 0 END AS huella_registrada
        FROM usuarios u
        LEFT JOIN role_user ru ON u.id_usuario = ru.id_usuario
        LEFT JOIN roles r ON ru.role_id = r.id
    """
    usuarios_con_roles = Usuarios.objects.raw(query)
    roles_disponibles = Roles.objects.all()

    return render(request, 'gestor_sistema/panel_admin.html', {
        'usuarios': usuarios_con_roles,
        'roles': roles_disponibles,
        'fichas': Ficha.objects.filter(estado='Activa'),
    })
    

@csrf_exempt
def registrar_huella_view(request, id_usuario):
    try:
        if request.method != 'POST':
            return JsonResponse({"error": "Metodo no permitido"}, status=405)

        usuario = get_object_or_404(Usuarios, id_usuario=id_usuario)

        print(f"👤 Sincronizando usuario {usuario.nombre} en el dispositivo...")
        enviar_usuario_hikvision(usuario)

        print(f"📱 Iniciando captura de huella para {usuario.nombre}...")
        response = registrar_huella_hikvision(usuario)

        if not response.get("ok"):
            return JsonResponse({
                "error": response.get("error", "No fue posible capturar la huella"),
                "detalle": response.get("raw", "")
            }, status=502)

        datos_huella = response.get("huella")
        if not datos_huella:
            return JsonResponse({
                "error": "El dispositivo no devolvió datos de huella"
            }, status=422)

        # Guardar en BD
        print(f"💾 Guardando huella en BD para {usuario.nombre}...")
        resultado_bd = guardar_huella_en_bd(usuario, datos_huella)
        if not resultado_bd.get("ok"):
            return JsonResponse({
                "error": "No se pudo guardar en BD",
                "detalle": resultado_bd.get("error", "")
            }, status=500)

        # ── Subir al dispositivo (PUT /UserInfo/Modify con fingerData + doorRight) ──
        print(f"📤 Subiendo huella al dispositivo para {usuario.nombre}...")
        subida = subir_huella_a_dispositivo(usuario.id_usuario, datos_huella)

        if not subida.get("ok"):
            print(f"⚠️ Huella en BD pero NO en dispositivo: {subida.get('error')}")
            return JsonResponse({
                "mensaje": "⚠️ Huella guardada en BD pero no en dispositivo",
                "id_huella": resultado_bd.get("id_huella"),
                "usuario": usuario.nombre,
                "detalle_subida": subida.get("raw", subida.get("error", ""))
            }, status=207)

        print(f"✅ Proceso completo para {usuario.nombre}")
        return JsonResponse({
            "mensaje": "✅ Huella registrada correctamente",
            "id_huella": resultado_bd.get("id_huella"),
            "usuario": usuario.nombre,
            
        }, status=200)

    except Exception as e:
        
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "error": f"Error no esperado: {str(e)}"
        }, status=500)
        
        

def dashboard(request):
    total_usuarios = Usuarios.objects.count()
    usuarios_activos = Usuarios.objects.filter(estado='Activo').count()
    ingresos_hoy = AsistenciaSedeReporte.objects.filter(fecha=date.today()).count()
    ambientes_hoy = AsistenciaAmbienteReporte.objects.filter(fecha=date.today()).count()

    context = {
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'ingresos_hoy': ingresos_hoy,
        'ambientes_hoy': ambientes_hoy,
        'fecha_actual': date.today(),
    }
    return render(request, 'gestor_sistema/dashboard.html', context)


def monitoreo_huellas(request):
    return render(request, 'gestor_sistema/monitoreo.html')


def descargar_reporte_sede(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_asistencia_sede.csv"'

    writer = csv.writer(response)
    writer.writerow(['Cedula', 'Nombre Completo', 'Fecha', 'Hora Ingreso', 'Hora Salida'])

    asistencias = AsistenciaSede.objects.all()
    for a in asistencias:
        writer.writerow([a.usuario.cedula, a.usuario.nombre, a.fecha, a.hora_entrada, a.hora_salida])

    return response


def verificar_ultima_huella(request):
    data = cache.get('ultima_huella')

    if data:
        cache.delete('ultima_huella')
        return JsonResponse(data)

    return JsonResponse({'status': 'esperando'})


def asistencia_ambiente(request):
    datos = AsistenciaAmbienteReporte.objects.all().select_related('usuario')
    print(f"DEBUG AMBIENTE: {datos.count()} registros encontrados")

    return render(request, 'gestor_sistema/asistencia_ambiente.html', {
        'asistencias': datos
    })


def asistencia_sede(request):
    datos = AsistenciaSedeReporte.objects.all().order_by('-fecha', '-hora_entrada')
    print(f"Registros encontrados: {datos.count()}")

    return render(request, 'gestor_sistema/asistencia_sede.html', {'asistencias': datos})


def exportar_asistencia_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_asistencia.csv"'

    writer = csv.writer(response)
    writer.writerow(['Documento', 'Nombre', 'Fecha', 'Ingreso', 'Salida'])

    asistencias = AsistenciaSedeReporte.objects.all().select_related('usuario')

    for a in asistencias:
        writer.writerow([
            a.usuario.cedula,
            f"{a.usuario.nombre} {a.usuario.apellido}",
            a.fecha,
            a.hora_entrada,
            a.hora_salida
        ])

    return response


def reportes(request):
    return render(request, 'gestor_sistema/reportes.html')


def registro_view(request):
    return render(request, 'gestor_sistema/registro_actividad.html')


def perfil_view(request):
    return render(request, 'gestor_sistema/mi_perfil.html')


def crear_usuario(request):
    registrar_actividad(
        request=request,
        usuario=request.user,
        actividad="Creación de usuario",
        tipo_accion="USUARIO",
        descripcion="Se creó un nuevo usuario"
    )
    
    
    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        correo = request.POST.get('correo')
        telefono = request.POST.get('telefono')

        try:
            usuario = Usuarios.objects.create_user(
                tipo_documento=request.POST.get('tipo_documento'),
                cedula=cedula,
                password=request.POST.get('password') or generar_password_segura(request.POST.get('cedula', ''), request.POST.get('nombre', '')),
                nombre=nombre,
                apellido=apellido,
                correo=correo,
                telefono=telefono,
                estado='Activo',
                is_active=True,
            )

            role_id = request.POST.get('role_id') or request.POST.get('rol')
            if role_id:
                with connections['default'].cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO role_user (id_usuario, role_id) VALUES (%s, %s)",
                        [usuario.id_usuario, role_id]
                    )

            enviar_usuario_hikvision(usuario)
            messages.success(request, f"Usuario {nombre} creado y sincronizado correctamente.")
        except Exception as e:
            messages.error(request, f"Error al guardar: {str(e)}")

        return redirect('gestor_sistema:panel_admin')

    return redirect('gestor_sistema:panel_admin')


def exportar_ambientes_excel(request):
    asistencia = AsistenciaAmbiente.objects.all().values(
        'usuario__nombre',
        'usuario__apellido',
        'id_instructor',
        'estado_asistencia'
    )

    df = pd.DataFrame(list(asistencia))

    if df.empty:
        return HttpResponse("No hay datos para exportar", status=404)

    df['Aprendiz'] = df['usuario__nombre'] + ' ' + df['usuario__apellido']
    columnas_finales = ['Aprendiz', 'id_instructor', 'estado_asistencia']
    df = df[columnas_finales]
    df.columns = ['Aprendiz', 'ID Instructor', 'Estado']

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="asistencia_ambientes.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    return response


def sincronizar_asistencia(request):
    procesar_eventos()
    return JsonResponse({"mensaje": "Asistencia sincronizada"})


def desactivar_usuario(request, id_usuario):
    usuario = get_object_or_404(Usuarios, id_usuario=id_usuario)
    usuario.estado = 'Inactivo'
    usuario.is_active = False
    usuario.save()

    messages.warning(request, f"El usuario {usuario.nombre} ha sido desactivado correctamente.")
    return redirect('gestor_sistema:panel_admin')


@login_required
def activar_usuario(request, id_usuario):
    usuario = get_object_or_404(Usuarios, id_usuario=id_usuario)
    usuario.estado = 'Activo'
    usuario.is_active = True
    usuario.save()
    messages.success(request, f"El usuario {usuario.nombre} ha sido activado.")
    return redirect('gestor_sistema:panel_admin')


@login_required
def editar_usuario(request, id_usuario):
    usuario = get_object_or_404(Usuarios, id_usuario=id_usuario)
    if request.method == "POST":
        usuario.tipo_documento = request.POST.get('tipo_documento', usuario.tipo_documento)
        usuario.cedula = request.POST.get('cedula')
        usuario.nombre = request.POST.get('nombre')
        usuario.apellido = request.POST.get('apellido')
        usuario.correo = request.POST.get('correo')
        usuario.telefono = request.POST.get('telefono', usuario.telefono)
        usuario.save()

        role_id = request.POST.get('role_id') or request.POST.get('rol')
        if role_id:
            with connections['default'].cursor() as cursor:
                cursor.execute(
                    "UPDATE role_user SET role_id = %s WHERE id_usuario = %s",
                    [role_id, id_usuario]
                )

        messages.success(request, "Usuario actualizado correctamente.")
        return redirect('gestor_sistema:panel_admin')

    return redirect('gestor_sistema:panel_admin')


@login_required
def gestionar_usuarios(request):
    query = """
        SELECT u.*, r.name as nombre_rol,
        CASE WHEN EXISTS (
            SELECT 1 FROM huella h WHERE h.id_usuario = u.id_usuario
        ) THEN 1 ELSE 0 END AS huella_registrada
        FROM usuarios u
        LEFT JOIN role_user ru ON u.id_usuario = ru.id_usuario
        LEFT JOIN roles r ON ru.role_id = r.id
    """
    usuarios = Usuarios.objects.raw(query)

    buscar = request.GET.get('buscar', '')
    rol_filtro = request.GET.get('rol', '')
    estado_filtro = request.GET.get('estado', '')

    usuarios_lista = list(usuarios)
    if buscar:
        usuarios_lista = [u for u in usuarios_lista if buscar.lower() in (u.nombre or '').lower() or buscar.lower() in (u.apellido or '').lower() or buscar.lower() in (u.cedula or '').lower()]
    if rol_filtro:
        usuarios_lista = [u for u in usuarios_lista if getattr(u, 'nombre_rol', '') == rol_filtro]
    if estado_filtro:
        usuarios_lista = [u for u in usuarios_lista if getattr(u, 'estado', '') == estado_filtro]

    context = {
        'usuarios': usuarios_lista,
        'roles': Roles.objects.all(),
        'fichas': Ficha.objects.filter(estado='Activa'),
        'filtros': {
            'buscar': buscar,
            'rol': rol_filtro,
            'estado': estado_filtro,
        }
    }
    return render(request, 'gestor_sistema/gestionar_usuarios.html', context)


@login_required
def crear_usuario_view(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        if Usuarios.objects.filter(cedula=cedula).exists():
            messages.error(request, f'Ya existe un usuario con la cédula {cedula}')
            return redirect('gestor_sistema:gestionar_usuarios')

        ficha_id = request.POST.get('ficha')
        nueva_ficha = request.POST.get('nueva_ficha')
        if nueva_ficha:
            ficha, _ = Ficha.objects.get_or_create(numero_ficha=nueva_ficha)
            ficha_id = ficha.id_ficha

        datos = {
            'cedula': cedula,
            'nombre': request.POST.get('nombre'),
            'apellido': request.POST.get('apellido'),
            'correo': request.POST.get('correo'),
            'telefono': request.POST.get('telefono'),
            'password': request.POST.get('password'),
            'rol_id': request.POST.get('rol'),
            'ficha_id': ficha_id,
        }

        usuario = crear_usuario(request, datos)
        messages.success(request, f'Usuario {usuario.nombre} {usuario.apellido} creado exitosamente')
        return redirect('gestor_sistema:gestionar_usuarios')

    return redirect('gestor_sistema:gestionar_usuarios')


@login_required
def editar_usuario_view(request, id_usuario):
    usuario = get_object_or_404(Usuarios, id_usuario=id_usuario)

    if request.method == 'POST':
        datos = {
            'nombre': request.POST.get('nombre'),
            'apellido': request.POST.get('apellido'),
            'correo': request.POST.get('correo'),
            'telefono': request.POST.get('telefono'),
            'rol_id': request.POST.get('rol'),
        }

        actualizar_usuario(usuario, datos)
        registrar_actividad(
            usuario=request.user,
            tipo_accion='UPDATE',
            actividad='Edición de usuario',
            descripcion=f'Se editó el usuario {usuario.nombre} {usuario.apellido}',
            request=request
        )

        messages.success(request, 'Usuario actualizado correctamente')
        return redirect('gestor_sistema:gestionar_usuarios')

    return redirect('gestor_sistema:gestionar_usuarios')


@login_required
def eliminar_usuario_view(request, id_usuario):
    usuario = get_object_or_404(Usuarios, id_usuario=id_usuario)

    if request.method == 'POST':
        eliminar_usuario(request, usuario)
        messages.success(request, 'Usuario eliminado permanentemente')

    return redirect('gestor_sistema:gestionar_usuarios')


@login_required
def cambiar_estado_usuario_view(request, id_usuario):
    usuario = get_object_or_404(Usuarios, id_usuario=id_usuario)

    if request.method == 'POST':
        accion = request.POST.get('accion')
        cambiar_estado_usuario(request, usuario, accion)

        if accion == 'desactivar':
            messages.warning(request, f'Usuario {usuario.nombre} {usuario.apellido} desactivado')
        else:
            messages.success(request, f'Usuario {usuario.nombre} {usuario.apellido} activado')

    return redirect('gestor_sistema:gestionar_usuarios')


@login_required
def gestion_huellas(request):
    query = """
        SELECT u.*, r.name as nombre_rol,
        CASE WHEN EXISTS (
            SELECT 1 FROM huella h WHERE h.id_usuario = u.id_usuario
        ) THEN 1 ELSE 0 END AS tiene_huella,
        (SELECT MAX(h.fecha_registro) FROM huella h WHERE h.id_usuario = u.id_usuario) AS fecha_huella
        FROM usuarios u
        LEFT JOIN role_user ru ON u.id_usuario = ru.id_usuario
        LEFT JOIN roles r ON ru.role_id = r.id
    """
    usuarios = list(Usuarios.objects.raw(query))

    buscar = request.GET.get('buscar', '')
    estado_huella = request.GET.get('estado_huella', '')
    rol_filtro = request.GET.get('rol', '')

    if buscar:
        usuarios = [u for u in usuarios if buscar.lower() in (u.nombre or '').lower() or buscar.lower() in (u.apellido or '').lower() or buscar.lower() in (u.cedula or '').lower()]
    if estado_huella == 'con_huella':
        usuarios = [u for u in usuarios if getattr(u, 'tiene_huella', False)]
    elif estado_huella == 'sin_huella':
        usuarios = [u for u in usuarios if not getattr(u, 'tiene_huella', False)]
    if rol_filtro:
        usuarios = [u for u in usuarios if getattr(u, 'nombre_rol', '') == rol_filtro]

    context = {
        'usuarios': usuarios,
        'roles': Roles.objects.all(),
        'filtros': {
            'buscar': buscar,
            'estado_huella': estado_huella,
            'rol': rol_filtro,
        }
    }
    return render(request, 'gestor_sistema/gestion_huellas.html', context)


@login_required
def eliminar_huella_usuario_view(request, id_usuario):
    usuario = get_object_or_404(Usuarios, id_usuario=id_usuario)

    if eliminar_huella_service(request, usuario):
        messages.success(request, f'✅ Huella eliminada para {usuario.nombre} {usuario.apellido}')
    else:
        messages.warning(request, 'El usuario no tiene huella registrada')

    return redirect('gestor_sistema:gestion_huellas')



@login_required
def registro_actividad_view(request):

    actividades = registro_actividad.objects.select_related(
        'id_usuario'
    ).all()

    buscar = request.GET.get('buscar', '')
    tipo_accion = request.GET.get('tipo_accion', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    if buscar:
        actividades = actividades.filter(
            Q(actividad__icontains=buscar) |
            Q(descripcion__icontains=buscar) |
            Q(id_usuario__nombre__icontains=buscar) |
            Q(id_usuario__apellido__icontains=buscar)
        )

    if tipo_accion:
        actividades = actividades.filter(
            tipo_accion=tipo_accion
        )

    if fecha_desde:
        actividades = actividades.filter(
            fecha__gte=fecha_desde
        )

    if fecha_hasta:
        actividades = actividades.filter(
            fecha__lte=fecha_hasta
        )

    actividades = actividades.order_by(
        '-fecha',
        '-hora'
    )

    total_actividades = registro_actividad.objects.count()

    total_login = registro_actividad.objects.filter(
        tipo_accion='LOGIN'
    ).count()

    total_huellas = registro_actividad.objects.filter(
        tipo_accion='HUELLA'
    ).count()

    total_usuarios = registro_actividad.objects.filter(
        tipo_accion='USUARIO'
    ).count()

    context = {

        'actividades': actividades,

        'total_actividades': total_actividades,
        'total_login': total_login,
        'total_huellas': total_huellas,
        'total_usuarios': total_usuarios,

        'filtros': {
            'buscar': buscar,
            'tipo_accion': tipo_accion,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta
        }
    }

    return render(
        request,
        'gestor_sistema/registro_actividad.html',
        context
    )
    
    
@login_required
def historial_fallos(request):
    from django.core.paginator import Paginator

    fallos = HistorialFallos.objects.select_related('usuario').all().order_by('-fecha', '-hora')

    total_fallos = fallos.count()
    registros_exitosos = fallos.filter(tipo_fallo='REGISTRO_HUELLA').count()
    fallos_huella = fallos.filter(tipo_fallo='HUELLA_FALLIDA').count()
    fallos_sin_huella = fallos.filter(tipo_fallo='SIN_HUELLA').count()
    fallos_no_existe = fallos.filter(tipo_fallo='USUARIO_NO_EXISTE').count()

    buscar = request.GET.get('buscar', '')
    tipo_fallo = request.GET.get('tipo_fallo', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    if buscar:
        fallos = fallos.filter(
            usuario__nombre__icontains=buscar
        ) | fallos.filter(
            usuario__apellido__icontains=buscar
        ) | fallos.filter(
            usuario__cedula__icontains=buscar
        ) | fallos.filter(
            cedula_intentada__icontains=buscar
        )

    if tipo_fallo:
        fallos = fallos.filter(tipo_fallo=tipo_fallo)

    if fecha_desde:
        fallos = fallos.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        fallos = fallos.filter(fecha__lte=fecha_hasta)

    paginator = Paginator(fallos, 50)
    page = request.GET.get('page', 1)
    fallos_page = paginator.get_page(page)

    context = {
        'fallos': fallos_page,
        'total_fallos': total_fallos,
        'registros_exitosos': registros_exitosos,
        'fallos_huella': fallos_huella,
        'fallos_sin_huella': fallos_sin_huella,
        'fallos_no_existe': fallos_no_existe,
        'filtros': {
            'buscar': buscar,
            'tipo_fallo': tipo_fallo,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        }
    }
    return render(request, 'gestor_sistema/historial_fallos.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_huella(request):
    try:
        body = request.body.decode('utf-8')
        print(f"📦 Recibido: {body[:200]}")

        import re

        match = re.search(r'"employeeNoString"\s*:\s*"(\d+)"', body)

        if match:
            cedula = match.group(1)
            print(f"✅ Cédula detectada: {cedula}")

            try:
                usuario = Usuarios.objects.get(cedula=cedula)
                resultado = registrar_asistencia_sede_por_huella(usuario, request=request)

                if resultado['estado'] == 'entrada':
                    print(f"   🟢 ENTRADA: {usuario.nombre} {usuario.apellido} - {timezone.localtime().time()}")
                elif resultado['estado'] == 'salida':
                    print(f"   🔴 SALIDA: {usuario.nombre} {usuario.apellido} - {timezone.localtime().time()}")
                else:
                    print(f"   ⚠️ Ya tiene entrada y salida hoy")

            except Usuarios.DoesNotExist:
                print(f"   ❌ Usuario no existe: {cedula}")
                HistorialFallos.objects.create(
                    tipo_fallo='USUARIO_NO_EXISTE',
                    cedula_intentada=cedula,
                    fecha=timezone.localtime().date(),
                    hora=timezone.localtime().time(),
                    detalles=f"Webhook: huella detectada con cédula {cedula} pero no existe en el sistema",
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
        else:
            print("📌 Evento sin cédula (otro tipo de evento)")

        return JsonResponse({'status': 'ok'})

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'status': 'error'}, status=500)