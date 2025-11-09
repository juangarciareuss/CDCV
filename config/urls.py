from django.contrib import admin
from django.urls import path, include 
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')), # <--- Asumimos que tus URLs de core están en 'core.urls'
]

# --- Añadir esto al final ---
# Esto permite que los archivos de MEDIA_ROOT se vean en el navegador
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

