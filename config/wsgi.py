"""
WSGI config for el proyecto.
"""
import os
from django.core.wsgi import get_wsgi_application

# --- CORRECCIÓN AQUÍ ---
# Debe apuntar a 'config.settings'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()