import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Curso, Pregunta

def autopsia_powerbi():
    print("🔍 INICIANDO AUTOPSIA DE DATOS - POWER BI")
    print("="*60)
    
    # 1. Buscamos el curso
    curso = Curso.objects.filter(nombre__icontains="Power BI").first()
    if not curso:
        print("❌ No encontré el curso de Power BI.")
        return

    print(f"📘 Curso: {curso.nombre}")
    print(f"📋 Receta actual del examen: {curso.estructura_examen}")
    
    # 2. Total real
    todas = Pregunta.objects.filter(curso=curso)
    print(f"📦 Total en Bodega: {todas.count()} preguntas.")
    
    # 3. Análisis de Dificultad vs Nivel (Sospecha #1)
    print("\n--- 1. SOSPECHA DE CAMPOS (Nivel vs Dificultad) ---")
    print(f"Items con 'dificultad' (1-5): {todas.filter(dificultad__gt=0).count()}")
    print(f"Items con 'nivel' (Legacy):   {todas.filter(nivel__gt=0).count()}")
    
    # 4. Análisis de Temas (Sospecha #2)
    print("\n--- 2. SOSPECHA DE TEMAS (Etiquetas) ---")
    # Agrupamos por tema
    temas_stats = {}
    for p in todas:
        # Obtenemos los temas de cada pregunta
        mis_temas = list(p.temas.values_list('nombre', flat=True))
        for t in mis_temas:
            temas_stats[t] = temas_stats.get(t, 0) + 1
            
    for tema, count in temas_stats.items():
        print(f"🏷️  Tema '{tema}': {count} preguntas")

    # 5. Muestra de las 'Invisibles'
    print("\n--- 3. COMPARATIVA ---")
    visible = todas.first() # Tomamos una cualquiera
    print(f"Ejemplo de pregunta existente:\nID: {visible.id}\nTexto: {visible.texto[:50]}...\nDificultad: {visible.dificultad}\nTemas: {[t.nombre for t in visible.temas.all()]}")

if __name__ == "__main__":
    autopsia_powerbi()