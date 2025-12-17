from django.contrib import admin
from django.urls import path, include, re_path # <--- Agregamos re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve # <--- Importante para servir archivos en prod

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    
    # --- LA SOLUCIÓN ---
    # Esta línea crea una ruta manual que atrapa todo lo que empiece por 'media/'
    # y lo sirve usando la carpeta MEDIA_ROOT, sin importar si DEBUG es True o False.
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]