from django.contrib import sitemaps
from django.urls import reverse

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.8          # Prioridad alta para tu portada (0.0 a 1.0)
    changefreq = 'daily'    # Le decimos a Google que nos visite diario

    def items(self):
        # Aquí pon el 'name' de tus URLs importantes.
        # Asumo que tu portada se llama 'home' o 'index' en urls.py
        return ['home'] 

    def location(self, item):
        return reverse(item)