#!/usr/bin/env bash
# (Paso 1: Salir inmediatamente si algo falla)
set -o errexit

# (Paso 2: Instalar dependencias)
pip install -r requirements.txt

# (Paso 3: Archivos estáticos)
python manage.py collectstatic --no-input

# (Paso 4: Base de datos - Tablas)
python manage.py migrate

# (Paso 5: Sembrar Cursos y Temas - CRÍTICO antes de las preguntas)
# Si este comando falla, las preguntas no tendrán donde guardarse.
python manage.py seed_taxonomy

# (Paso 6: Llenar la tienda - Importar Preguntas desde tus JSON)
# Ajusta las rutas si moviste los archivos, aquí asumo que están en la raíz o en core/
if [ -f "ia_excel_100.json" ]; then
    python manage.py import_questions --file ia_excel_100.json
fi

if [ -f "ia_prompts_10.json" ]; then
    python manage.py import_questions --file ia_prompts_10.json
fi

if [ -f "ia_python_10.json" ]; then
    python manage.py import_questions --file ia_python_10.json
fi

if [ -f "core/powerbi_avanzado.json" ]; then
    python manage.py import_questions --file core/powerbi_avanzado.json
fi

# (Paso 7: Hack Superusuario - Mantenemos el que funcionó)
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='juangarciareuss').exists() or User.objects.create_superuser('juangarciareuss', 'junagarciareuss@gmail.com', 'waarewer6')"