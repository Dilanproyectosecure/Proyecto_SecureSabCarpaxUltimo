# ver_huella.py
import requests
from requests.auth import HTTPDigestAuth
import re

url = 'http://192.168.1.13/ISAPI/Event/notification/alertStream'
response = requests.get(url, auth=HTTPDigestAuth('admin', 'Dilan1105'), stream=True)

print('Esperando eventos... (CTRL+C para salir)')
print('-' * 50)

for line in response.iter_lines():
    if line:
        texto = line.decode('utf-8')
        # Buscar cédula en el texto
        match = re.search(r'"employeeNoString"\s*:\s*"(\d*)"', texto)
        if match:
            cedula = match.group(1)
            if cedula:
                print(f'✅ Cédula detectada: {cedula}')
            else:
                print('⚠️ Evento sin cédula')