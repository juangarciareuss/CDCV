import os
import sys
import django
from django.utils.text import slugify

# Configuración para que el script pueda "hablar" con Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Curso, Pregunta

def run():
    print("🐌 Generando Slugs para SEO...")

    # 1. Cursos
    cursos = Curso.objects.all()
    for c in cursos:
        if not c.slug:
            base_slug = slugify(c.nombre)
            c.slug = base_slug
            c.save()
            print(f"   Curso '{c.nombre}' -> /{c.slug}")

    # 2. Preguntas
    preguntas = Pregunta.objects.all()
    count = 0
    for p in preguntas:
        if not p.slug:
            # Cortamos el texto si es muy largo para la URL
            texto_base = p.texto[:50] 
            base_slug = slugify(texto_base)
            
            # Manejo de duplicados (por si dos preguntas empiezan igual)
            slug_final = base_slug
            counter = 1
            while Pregunta.objects.filter(slug=slug_final).exclude(id=p.id).exists():
                slug_final = f"{base_slug}-{counter}"
                counter += 1
            
            p.slug = slug_final
            p.save()
            count += 1
            if count % 50 == 0: print(f"   Procesadas {count} preguntas...")

    print("✅ ¡Listo! URLs amigables generadas.")

if __name__ == "__main__":
    run()