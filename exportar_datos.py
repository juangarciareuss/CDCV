import os
import django
from django.core.management import call_command

# Configura Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("⏳ Generando copia de seguridad en UTF-8 puro...")

# Abre el archivo forzando la codificación UTF-8
with open('datos_iniciales.json', 'w', encoding='utf-8') as f:
    # Ejecuta el comando dumpdata y envía la salida directo al archivo
    call_command('dumpdata', 'core', indent=2, stdout=f)

print("✅ ¡Listo! Archivo 'datos_iniciales.json' generado correctamente.")