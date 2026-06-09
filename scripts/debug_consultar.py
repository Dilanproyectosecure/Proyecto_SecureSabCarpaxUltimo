import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.test import RequestFactory
from apps.seguridad_administracion.vigilante import views

rf = RequestFactory()
req = rf.get('/vigilante/consultar-invitado/', {'tipo_documento': 'TI'})
# Attach a fake authenticated user to bypass login_required
class FakeUser:
    is_authenticated = True
    nombre = 'debug'

req.user = FakeUser()

# Replace render to capture context
def fake_render(request, template, context):
    print('template=', template)
    print('has_tipos_documento=', 'tipos_documento' in context)
    print('tipos_documento=', context.get('tipos_documento'))
    visitas = context.get('visitantes')
    try:
        count = len(visitas.object_list)
    except Exception:
        try:
            count = len(list(visitas))
        except Exception:
            count = 'unknown'
    print('visitantes_count=', count)
    return None

views.render = fake_render

# Call view
views.consultar_invitado(req)
