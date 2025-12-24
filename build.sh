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

# 4. Estructura Base (Corregido: Comando comentado para evitar error)
# python manage.py seed_taxonomy

# Carga de datos de respaldo (solo si existe)
if [ -f "datos_iniciales.json" ]; then
    echo "📦 Cargando datos de respaldo..."
    python manage.py loaddata datos_iniciales.json
fi

# 5. Asegurar Superusuario
echo "👤 Asegurando cuenta de administrador..."
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='juangarciareuss').exists() or User.objects.create_superuser('juangarciareuss', 'junagarciareuss@gmail.com', 'waarewer6')"

# 6. Parche de Certificados
python manage.py shell -c "from django.contrib.auth import get_user_model; u = get_user_model().objects.get(username='juangarciareuss'); u.first_name='JUAN IGNACIO'; u.last_name='GARCIA REUSS'; u.save()"

echo "✅ Build completado con éxito."