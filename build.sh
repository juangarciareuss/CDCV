#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Iniciando Build para Producción..."

# 1. Instalar dependencias (Aquí se instalará google-genai)
pip install -r requirements.txt

# 2. Archivos estáticos (CSS, JS, Imágenes del diseño)
python manage.py collectstatic --no-input

# 3. Base de datos (Aplica los cambios nuevos: campo 'activo', tablas nuevas, etc.)
python manage.py migrate

# 4. Estructura Base (Mantenemos esto SOLO si crea las categorías/niveles vacíos)
# Si tu 'seed_taxonomy' crea cursos de prueba viejos, bórralo también.
# Si solo crea la estructura de niveles (Nivel 1, 2, 3...), déjalo.
python manage.py seed_taxonomy

# --- SECCIÓN LIMPIA: ADIÓS A LOS JSON VIEJOS ---
# Ya no importamos 'ia_excel_100.json' ni nada manual.
# Ahora el contenido se crea dinámicamente desde el Dashboard con IA.

# 5. Asegurar Superusuario (Para que siempre puedas entrar al admin)
echo "👤 Asegurando cuenta de administrador..."
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='juangarciareuss').exists() or User.objects.create_superuser('juangarciareuss', 'junagarciareuss@gmail.com', 'waarewer6')"

# 6. Parche de Certificados (Nombre y Apellido para PDF)
python manage.py shell -c "from django.contrib.auth import get_user_model; u = get_user_model().objects.get(username='juangarciareuss'); u.first_name='JUAN IGNACIO'; u.last_name='GARCIA REUSS'; u.save()"

echo "✅ Build completado con éxito."