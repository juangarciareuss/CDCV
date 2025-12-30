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
# Borra el if 'RENDER'... y pon esto:
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

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
    
    # --- Tu App Principal ---
    'core',

    # --- NUEVAS LIBRERÍAS (OBLIGATORIAS PARA GOOGLE) ---
    'django.contrib.sites',  # Django necesita saber "qué sitio es este"
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google', # El conector específico de Google
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

    # --- AGREGA ESTA LÍNEA AL FINAL ---
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': 
            BASE_DIR / 'templates',         # 1. Busca aquí primero (Carpeta raíz)
            
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

# --- BASE DE DATOS (CONFIGURACIÓN HÍBRIDA INTELIGENTE) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Solo si existe la variable DATABASE_URL (en Render), sobrescribimos.
# Esto evita que en local se borre la configuración de SQLite.
if os.getenv('DATABASE_URL'):
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
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')] # O donde tengas tus estáticos
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder', # Añade esta línea
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]
STATICFILES_DIRS = []
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
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

# --- CONFIGURACIÓN DE LOGIN SOCIAL (ALLAUTH) ---
SITE_ID = 1

# Esto le dice a Django: "Permite login normal (admin) Y login por Google"
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]



# ==========================================
# CONFIGURACIÓN DEFINITIVA DE ALLAUTH (2025)
# ==========================================

# 1. Proveedores (Google)
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'}
    }
}

# 2. Autenticación Moderna
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email']
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False

# 3. Estrategia de Fusión
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_AUTO_SIGNUP = True

# 4. Verificación
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_EMAIL_VERIFICATION = 'none'

# 5. Adaptador Personalizado
SOCIALACCOUNT_ADAPTER = 'core.adapters.MySocialAccountAdapter'

# 6. Redirecciones
LOGIN_REDIRECT_URL = 'core:homepage'
LOGOUT_REDIRECT_URL = 'core:homepage'
LOGIN_URL = 'account_login'

# 7. Protocolo (HTTPS en Render)
import os
if os.environ.get('RENDER'):
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
else:
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'

# =======================================================
# ARREGLO DE EMERGENCIA PARA LOGIN LOCAL (EVITA ERROR 10061)
# =======================================================

# 1. Esto simula el servidor de correos.
# En lugar de intentar enviarlo (y fallar), solo lo escribe en tu terminal negra.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# 2. Esto asegura que no pida confirmación para entrar.
ACCOUNT_EMAIL_VERIFICATION = 'none'