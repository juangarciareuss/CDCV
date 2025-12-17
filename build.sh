#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Archivos estáticos
python manage.py collectstatic --no-input

# 3. Base de datos
python manage.py migrate

# 4. Crear Cursos (Esqueleto)
python manage.py seed_taxonomy

# 5. Cargar Preguntas (SOLO EXCEL que funciona)
if [ -f "ia_excel_100.json" ]; then
    python manage.py import_questions --file ia_excel_100.json
fi

# NOTA: Comentamos los que dan error para que el servidor arranque.
# Cuando arregles los JSON, descomenta estas líneas:
# python manage.py import_questions --file ia_python_10.json
# python manage.py import_questions --file core/powerbi_avanzado.json

# 6. Crear Superusuario (CORREGIDO y con NOMBRE para el certificado)
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='juangarciareuss').exists() or User.objects.create_superuser('juangarciareuss', 'junagarciareuss@gmail.com', 'waarewer6')"

# 7. Asegurar que el usuario tenga Nombre y Apellido (Para que el PDF no salga en blanco)
python manage.py shell -c "from django.contrib.auth import get_user_model; u = get_user_model().objects.get(username='juangarciareuss'); u.first_name='JUAN IGNACIO'; u.last_name='GARCIA REUSS'; u.save()"