#!/usr/bin/env bash

# (Paso 1: Salir inmediatamente si un comando falla - Muro de Contención)
set -o errexit

# (Paso 2: Instalar todas las dependencias de requirements.txt)
pip install -r requirements.txt

# (Paso 3: Recolectar todos los archivos estáticos (CSS/JS) en la carpeta /staticfiles/)
# (Render necesita esto porque DEBUG=False)
python manage.py collectstatic --no-input

# (Paso 4: Aplicar las migraciones a la base de datos PostgreSQL gratuita de Render)
# (Esto crea las tablas PreguntaTema, dificultad, etc., en producción)
python manage.py migrate

# Hack corregido: Busca 'juangarciareuss' y si no está, lo crea.
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='juangarciareuss').exists() or User.objects.create_superuser('juangarciareuss', 'junagarciareuss@gmail.com', 'waarewer6')"