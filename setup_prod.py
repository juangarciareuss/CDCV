import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialApp

def setup():
    print("🚑 Iniciando Protocolo de Rescate...")

    # 1. Configurar el Sitio (Para eliminar el Error 500)
    site, created = Site.objects.update_or_create(
        id=1,
        defaults={
            'domain': 'cdcv.onrender.com',
            'name': 'CDCV Production'
        }
    )
    print(f"✅ Sitio configurado: {site.domain}")

    # 2. Crear App de Google (Dummy para que cargue el Home)
    app, created = SocialApp.objects.update_or_create(
        provider='google',
        defaults={
            'name': 'Google Auth',
            'client_id': 'LLENAR_EN_ADMIN_DESPUES', # <--- No olvides cambiar esto luego
            'secret': 'LLENAR_EN_ADMIN_DESPUES',
        }
    )
    app.sites.add(site)
    print(f"✅ Configuración de Google creada.")

    # 3. Resucitar TU Usuario Admin
    User = get_user_model()
    
    # TUS DATOS REALES:
    USERNAME = 'juangarciareuss'
    EMAIL = 'juangarciareuss@gmail.com'
    PASSWORD = 'waarewer6' 

    if not User.objects.filter(username=USERNAME).exists():
        User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
        print(f"✅ Tu usuario {USERNAME} ha sido restaurado en Producción.")
    else:
        print(f"ℹ️ El usuario {USERNAME} ya existía.")

if __name__ == '__main__':
    setup()