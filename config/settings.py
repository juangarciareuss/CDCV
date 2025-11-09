from pathlib import Path
import os
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Lee la llave secreta desde el archivo .env
SECRET_KEY = os.getenv('SECRET_KEY')

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
    'core',  # Tu app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# --- CORRECCIÓN AQUÍ ---
# El traceback indica que esto es uno de los problemas.
# Debe apuntar a 'config.urls', no 'cdcv.urls'
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

# --- CORRECCIÓN AQUÍ ---
# Debe apuntar a 'config.wsgi.application'
WSGI_APPLICATION = 'config.wsgi.application'
# --- CORRECCIÓN AQUÍ ---
# Debe apuntar a 'config.asgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

STATIC_URL = 'static/'

# --- Configuración de Archivos Media (Uploads) ---
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Modelo de Usuario Personalizado
AUTH_USER_MODEL = 'core.Usuario'

# --- Configuración de PayPal (Hora 7) ---
import paypalrestsdk
# (Asegúrate de que 'import os' esté al inicio de tu archivo settings.py)

# Lee las llaves de PayPal desde el archivo .env
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')

PAYPAL_MODE = 'sandbox'

# Modo 'sandbox' para pruebas. Cambiar a 'live' para producción.
PAYPAL_MODE = 'sandbox' 

paypalrestsdk.configure({
    "mode": PAYPAL_MODE,
    "client_id": PAYPAL_CLIENT_ID ,
    "client_secret": PAYPAL_CLIENT_SECRET
})