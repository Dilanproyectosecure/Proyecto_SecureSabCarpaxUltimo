import os, sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.test import RequestFactory
from apps.seguridad_administracion.vigilante import views

rf = RequestFactory()
req = rf.get('/vigilante/registrar-invitado/')
class FakeUser:
    is_authenticated = True
    nombre = 'debug'
req.user = FakeUser()

def fake_render(request, template, context):
    print('template=', template)
    print('has_tipos_documento=', 'tipos_documento' in context)
    print('tipos_documento=', context.get('tipos_documento'))
    return None

views.render = fake_render
views.registrar_invitado(req)
