from django.contrib import admin
from django.urls import path, include, re_path # <--- Agregamos re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve # <--- Importante para servir archivos en prod

urlpatterns = [
    # 1. Panel de Administración
    path('admin/', admin.site.urls),

    # 2. Rutas de Autenticación (Google, Login, Logout)
    # ESTA ES LA LÍNEA CLAVE QUE FALTA O ESTÁ MAL PUESTA
    path('accounts/', include('allauth.urls')),

    # 3. Rutas de tu Aplicación Principal (CDCV)
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)