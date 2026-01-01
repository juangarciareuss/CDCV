#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Iniciando Build para Producción..."

# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Archivos estáticos
python manage.py collectstatic --no-input

# 3. Base de datos
python manage.py migrate

# 4. Estructura Base (Opcional)
# python manage.py seed_taxonomy

# Carga de datos de respaldo (solo si existe)
if [ -f "datos_iniciales.json" ]; then
    echo "📦 Cargando datos de respaldo..."
    #python manage.py loaddata datos_iniciales.json
fi

# 5. Asegurar Superusuario (VERSIÓN SEGURA 🔒)
# Lee la contraseña de la variable de entorno 'DJANGO_SUPERUSER_PASSWORD'
# Si no existe la variable, usa una por defecto (solo por seguridad para que no falle el build)
echo "👤 Asegurando cuenta de administrador..."
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = 'juangarciareuss'
email = 'juangarciareuss@gmail.com'
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'CambiaEstaPass123')

if not User.objects.filter(username=username).exists():
    print(f'Creando superusuario: {username}')
    User.objects.create_superuser(username, email, password)
else:
    print(f'El usuario {username} ya existe.')
"

# 6. Parche de Certificados (Actualizar Nombres)
echo "🏷️ Actualizando datos del perfil..."
python manage.py shell -c "from django.contrib.auth import get_user_model; u = get_user_model().objects.get(username='juangarciareuss'); u.first_name='JUAN IGNACIO'; u.last_name='GARCIA REUSS'; u.save()"

echo "✅ Build completado con éxito."