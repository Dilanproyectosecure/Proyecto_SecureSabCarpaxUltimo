from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa

def generar_pdf_asistencia_ambiente(request, asistencias, registros, logo_data):
    """Genera PDF de asistencia ambiente"""
    
    total = len(registros)
    asistio = len([r for r in registros if 'asistio' in r.get('estado', '').lower()])
    inasistio = len([r for r in registros if 'inasistio' in r.get('estado', '').lower()])
    justificada = len([r for r in registros if 'justificad' in r.get('estado', '').lower()])
    
    context = {
        'total': total,
        'asistio': asistio,
        'inasistio': inasistio,
        'justificada': justificada,
        'pct_asistio': round((asistio / total) * 100, 2) if total else 0,
        'pct_inasistio': round((inasistio / total) * 100, 2) if total else 0,
        'pct_justificada': round((justificada / total) * 100, 2) if total else 0,
        'registros': registros[:500],
        'logo_data': logo_data,
        'filtros_display': {
            'ficha': request.GET.get('ficha') or 'Todas',
            'documento': request.GET.get('documento') or 'Todos',
            'fecha': request.GET.get('fecha') or 'Todas',
            'estado': request.GET.get('estado') or 'Todos',
        }
    }
    
    html_string = render_to_string('reporte_ambiente.html', context, request=request)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_asistencia_ambiente.pdf"'
    
    pdf_buffer = BytesIO()
    pisa.CreatePDF(html_string, dest=pdf_buffer, encoding='utf-8')
    response.write(pdf_buffer.getvalue())
    return response


def generar_pdf_asistencia_sede(request, asistencias, registros, logo_data):
    """Genera PDF de asistencia sede"""
    
    total = len(registros)
    con_salida = len([r for r in registros if r.get('salida') and r.get('salida') != '-'])
    sin_salida = total - con_salida
    
    context = {
        'total': total,
        'con_salida': con_salida,
        'sin_salida': sin_salida,
        'pct_con_salida': round((con_salida / total) * 100, 2) if total else 0,
        'pct_sin_salida': round((sin_salida / total) * 100, 2) if total else 0,
        'registros': registros[:500],
        'logo_data': logo_data,
        'filtros_display': {
            'ficha': request.GET.get('ficha') or 'Todas',
            'documento': request.GET.get('documento') or 'Todos',
            'fecha': request.GET.get('fecha') or 'Todas',
        }
    }
    
    html_string = render_to_string('reporte_sede.html', context, request=request)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_asistencia_sede.pdf"'
    
    pdf_buffer = BytesIO()
    pisa.CreatePDF(html_string, dest=pdf_buffer, encoding='utf-8')
    response.write(pdf_buffer.getvalue())
    return response