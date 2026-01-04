from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# --- Importaciones para el Sitemap (Las movemos aquí) ---
from django.contrib.sitemaps.views import sitemap
from core.sitemaps import StaticViewSitemap

# Definimos el diccionario de sitemaps global
sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    # 1. Panel de Administración (Global)
    path('admin/', admin.site.urls),

    # 2. Rutas de Autenticación (Google, Login) - SE QUEDA AQUÍ
    path('accounts/', include('allauth.urls')),

    # 3. Sitemap para Google (Global) - MEJOR LUGAR
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    # 4. Rutas de tu Aplicación (Todo lo demás va a Core)
    path('', include('core.urls')),
]

# Configuración para servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)