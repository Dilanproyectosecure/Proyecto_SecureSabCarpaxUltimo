from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa


def generate_pdf_response(template_src, context_dict, filename="reporte.pdf"):
    """
    Genera un PDF desde una plantilla HTML y retorna HttpResponse
    """

    template = get_template(template_src)
    html = template.render(context_dict)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error al generar PDF')

    return response