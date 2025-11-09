"""
ASGI config for el proyecto.
"""
import os
from django.core.asgi import get_asgi_application

# --- CORRECCIÓN AQUÍ ---
# Debe apuntar a 'config.settings'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()