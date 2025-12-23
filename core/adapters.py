# core/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import perform_login
from django.contrib.auth import get_user_model

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # 1. Si el usuario ya está logueado, no hacemos nada (el comportamiento normal lo maneja)
        if request.user.is_authenticated:
            return

        # 2. Si no, verificamos si ya existe un usuario con ese email
        email = sociallogin.account.extra_data.get('email')
        
        if email:
            User = get_user_model()
            try:
                # Buscamos al usuario por email
                user = User.objects.get(email=email)
                
                # 3. ¡LA MAGIA! Conectamos manualmente la cuenta de Google al usuario existente
                sociallogin.connect(request, user)
                
                # Opcional: Forzamos el login inmediato para saltar confirmaciones
                # perform_login(request, user, email_verification='none', redirect_url='/dashboard')
                
            except User.DoesNotExist:
                # Si no existe, dejamos que Allauth cree el usuario nuevo normalmente
                pass