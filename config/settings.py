from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url # Para base de datos (si se requiere en producción)

# Carga las variables de entorno si existe el archivo .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Lee la llave secreta desde el archivo .env o usa una por defecto insegura para desarrollo
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-clave-por-defecto-para-dev')

# Poner en True para desarrollo
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Tu aplicación principal
    'core',

    # --- CORRECCIÓN ---
    # Se eliminó 'whitenoise.middleware.WhiteNoiseMiddleware' de aquí.
    # Esta lista es SOLO para aplicaciones (Apps).
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    
    # --- CORRECCIÓN ---
    # WhiteNoise debe ir aquí, justo después de SecurityMiddleware
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

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
# Configuración para WhiteNoise (archivos estáticos en producción)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# Compresión y almacenamiento eficiente
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage' (Opcional por ahora)

# Configuración de Archivos Media (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Modelo de Usuario Personalizado
AUTH_USER_MODEL = 'core.Usuario'

# --- Configuración de PayPal ---
import paypalrestsdk

# Lee las llaves de PayPal desde el archivo .env
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')

if PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET:
    paypalrestsdk.configure({
        "mode": PAYPAL_MODE,
        "client_id": PAYPAL_CLIENT_ID,
        "client_secret": PAYPAL_CLIENT_SECRET
    })
else:
    print("ADVERTENCIA: Credenciales de PayPal no encontradas en .env")