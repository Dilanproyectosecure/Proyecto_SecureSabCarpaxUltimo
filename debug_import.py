import sys
sys.path.insert(0, 'apps/gestor_sistema')
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

print('sys.path[0]:', os.path.abspath(sys.path[0]))

try:
    import apps
    print('apps:', apps)
    print('apps.__path__:', apps.__path__)
    import apps.login
    print('apps.login:', apps.login)
except Exception as e:
    print('Import error:', type(e).__name__, e)
    import traceback
    traceback.print_exc()
