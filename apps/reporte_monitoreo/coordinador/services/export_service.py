import os
import base64
from django.conf import settings
from django.http import HttpResponse
import csv

def obtener_logo_pdf():
    """Obtiene el logo en base64 para PDFs"""
    logo_path = None
    logo_data = None
    
    try:
        candidate_folders = [
            os.path.join(settings.BASE_DIR, 'apps', 'reporte_monitoreo', 'static', 'imagen logo sena'),
            os.path.join(settings.BASE_DIR, 'apps', 'reporte_monitoreo', 'coordinador', 'static', 'imagen logo sena'),
            os.path.join(settings.BASE_DIR, 'apps', 'reporte_monitoreo', 'coordinador', 'static', 'img'),
            os.path.join(settings.BASE_DIR, 'apps', 'static', 'img'),
            os.path.join(settings.BASE_DIR, 'static', 'img'),
        ]
        for imagen_folder in candidate_folders:
            if os.path.isdir(imagen_folder):
                preferred = os.path.join(imagen_folder, 'logoSenaNaranja.png')
                if os.path.exists(preferred):
                    logo_path = preferred
                    break
                for fname in os.listdir(imagen_folder):
                    if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                        logo_path = os.path.join(imagen_folder, fname)
                        break
            if logo_path:
                break
    except Exception:
        logo_path = None

    if logo_path:
        try:
            with open(logo_path, 'rb') as f:
                data = f.read()
            mime = 'image/png' if logo_path.lower().endswith('.png') else 'image/jpeg'
            logo_data = 'data:' + mime + ';base64,' + base64.b64encode(data).decode('utf-8')
        except Exception:
            logo_data = None
    
    return logo_data


def preparar_registros_pdf(asistencias):
    """Prepara los registros para el PDF"""
    registros = []
    for asistencia in asistencias[:800]:
        usuario = asistencia.id_usuario
        ficha = getattr(usuario, 'id_ficha', None)
        jornada = getattr(ficha, 'id_jornada', None)
        instructor = asistencia.id_instructor
        estado = (asistencia.estado_asistencia or '').lower()
        
        if 'asisti' in estado and 'inasisti' not in estado:
            estado_display = 'asistio'
        elif 'inasisti' in estado:
            estado_display = 'inasistio'
        elif 'justificad' in estado:
            estado_display = 'justificada'
        else:
            estado_display = estado
        
        registros.append({
            'documento': getattr(usuario, 'cedula', '-'),
            'nombre': f"{getattr(usuario, 'nombre', '')} {getattr(usuario, 'apellido', '')}".strip() or '-',
            'instructor': f"{getattr(instructor, 'nombre', '')} {getattr(instructor, 'apellido', '')}".strip() or 'No asignado',
            'ficha': getattr(ficha, 'numero_ficha', 'Sin ficha'),
            'jornada': getattr(jornada, 'nombre_jornada', 'No asignada'),
            'fecha': asistencia.fecha.strftime('%d/%m/%Y') if asistencia.fecha else '-',
            'estado': estado_display,
        })
    return registros


def obtener_filtros_display(request):
    """Obtiene los filtros para mostrar en el PDF"""
    instructor_id = request.GET.get('instructor', '')
    instructor_display = 'Todos'
    if instructor_id and instructor_id != 'all':
        from apps.login.models import Usuarios
        instructor_obj = Usuarios.objects.filter(id_usuario=instructor_id).first()
        if instructor_obj:
            instructor_display = f"{instructor_obj.nombre or ''} {instructor_obj.apellido or ''}".strip()
    
    return {
        'ficha': request.GET.get('ficha') or 'Todas las Fichas',
        'documento': request.GET.get('documento') or 'Todos',
        'fecha': request.GET.get('fecha') or 'Todas',
        'estado': request.GET.get('estado') or 'Todos',
        'jornada': request.GET.get('jornada') or 'Todas las Jornadas',
        'instructor': instructor_display,
    }

def exportar_csv(asistencias, headers, filename, data_extractor):
    """Exporta cualquier queryset a CSV"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    response.write('\ufeff')
    
    writer = csv.writer(response)
    writer.writerow(headers)
    
    for asistencia in asistencias:
        writer.writerow(data_extractor(asistencia))
    
    return response