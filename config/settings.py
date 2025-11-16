from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url # AÑADIDO: Para la base de datos de producción

# Carga las variables del archivo .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Lee la llave secreta desde el archivo .env
# Render usará sus propias variables de entorno, pero esto funciona para local
SECRET_KEY = os.getenv('SECRET_KEY')

# MODIFICADO: Configuración de DEBUG dinámica
# En Render, DEBUG será 'False' por defecto. En local, puedes poner DEBUG=True en tu .env
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# MODIFICADO: Configuración de ALLOWED_HOSTS dinámica
# Acepta localhost y la URL de Render (.onrender.com)
ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
else:
    # Si no estamos en Render, permitimos el desarrollo local
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    # AÑADIDO: Para la gestión de estáticos en producción (debe ir antes de staticfiles)
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # AÑADIDO: Middleware de WhiteNoise (debe ir después de SecurityMiddleware)
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# --- MODIFICACIÓN: Configuración de Base de Datos (Robusta) ---
# ELIMINADA: La configuración de sqlite3

# Esta lógica usa la DB de PostgreSQL de Render (si existe la variable de entorno DATABASE_URL),
# o vuelve a usar sqlite3 si no lo está (para desarrollo local).
DATABASES = {
    'default': dj_database_url.config(
        # La URL de la DB gratuita de Render se leerá de la variable de entorno DATABASE_URL
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600
    )
}

# --- MODIFICACIÓN: Configuración de Estáticos (CSS/JS) para Producción ---
STATIC_URL = 'static/'
# AÑADIDO: Dónde 'collectstatic' pondrá los archivos (Render lo necesita)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# AÑADIDO: Storage para WhiteNoise (para servir estáticos eficientemente)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# --- FIN DE MODIFICACIÓN DE ESTÁTICOS ---


# --- Configuración de Archivos Media (Uploads) (Sin cambios) ---
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Modelo de Usuario Personalizado
AUTH_USER_MODEL = 'core.Usuario'

# --- Configuración de PayPal (Sin cambios) ---
import paypalrestsdk
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
PAYPAL_MODE = 'sandbox' 
paypalrestsdk.configure({
    "mode": PAYPAL_MODE,
    "client_id": PAYPAL_CLIENT_ID ,
    "client_secret": PAYPAL_CLIENT_SECRET
})