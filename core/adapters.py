from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    
    def pre_social_login(self, request, sociallogin):
        """
        Interviene antes del login para evitar duplicados.
        Si el email de Google ya existe en la base de datos, 
        conecta la cuenta social al usuario existente en lugar de fallar.
        """
        
        # 1. Si el usuario ya está logueado, no hacemos nada.
        if request.user.is_authenticated:
            return

        # 2. Si la cuenta social ya existe (ya se vinculó antes), dejamos pasar.
        if sociallogin.is_existing:
            return

        # 3. Buscamos si el email ya existe en nuestra BD
        email = sociallogin.account.extra_data.get('email')
        
        if email:
            User = get_user_model()
            try:
                # Buscamos al usuario por email
                user = User.objects.get(email=email)
                
                # ¡MAGIA AQUÍ! 🪄
                # Conectamos la cuenta de Google a este usuario existente.
                sociallogin.connect(request, user)
                
            except User.DoesNotExist:
                # Si no existe, no hacemos nada. Allauth creará uno nuevo automáticamente.
                pass