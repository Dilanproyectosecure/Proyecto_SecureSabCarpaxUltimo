import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from apps.login.models import Usuarios
u = Usuarios.objects.filter(id_usuario=86).first()
if u:
    print(f"Usuario 86: nombre={u.nombre} cedula={u.cedula}")
else:
    print("Usuario 86 NO existe")
print("Webhook busca: cedula=86")
if u and str(u.cedula) == "86":
    print("MATCH - webhook funciona")
else:
    print("NO MATCH - webhook falla silenciosamente")
    if u:
        print(f"El cedula real es '{u.cedula}', no '86'")
