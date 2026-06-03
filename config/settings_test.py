from .settings import *
import sys

TESTING = True

# 🔥 FORZAR BD DE TEST AISLADA
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # BD temporal en RAM
    }
}

# 🔥 IMPORTANTE: evitar conexión a MySQL
DEBUG = False