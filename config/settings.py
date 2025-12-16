from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url # Importante para la base de datos en la nube

# Carga las variables de entorno si existe el archivo .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SEGURIDAD:
# Lee la llave secreta desde el archivo .env. Si no existe (prod), falla o usa default.
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-clave-por-defecto-para-dev')

# DEBUG:
# En producción (Render), 'RENDER' suele estar en las variables de entorno.
# Si estamos en Render, DEBUG debe ser False. Si no, True.
if 'RENDER' in os.environ:
    DEBUG = False
else:
    DEBUG = True

# HOSTS PERMITIDOS:
# En producción, esto debe incluir tu dominio (ej. 'cdcv.onrender.com').
# El '*' permite todo, útil para probar el deploy inicial, luego ciérralo.
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Gestión de archivos estáticos
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

# --- BASE DE DATOS (CONFIGURACIÓN HÍBRIDA) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Si existe la variable DATABASE_URL (que Render pone automáticamente para PostgreSQL),
# sobrescribimos la configuración para usar esa base de datos real.
db_from_env = dj_database_url.config(conn_max_age=600)
DATABASES['default'].update(db_from_env)


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

# Internationalization
LANGUAGE_CODE = 'es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS (CRÍTICO PARA PRODUCCIÓN) ---
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Habilitar compresión y almacenamiento en caché de Whitenoise
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuración de Archivos Media (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Modelo de Usuario Personalizado
AUTH_USER_MODEL = 'core.Usuario'

# --- Configuración de PayPal ---
import paypalrestsdk

PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
# Si estamos en Render, asumimos producción (live), si no, sandbox.
# Opcional: puedes controlarlo con una variable PAYPAL_MODE en el .env
PAYPAL_MODE = os.getenv('PAYPAL_MODE', 'sandbox')

if PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET:
    paypalrestsdk.configure({
        "mode": PAYPAL_MODE,
        "client_id": PAYPAL_CLIENT_ID,
        "client_secret": PAYPAL_CLIENT_SECRET
    })
else:
    print("ADVERTENCIA: Credenciales de PayPal no encontradas en variables de entorno.")