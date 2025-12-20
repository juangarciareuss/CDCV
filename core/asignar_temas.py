import os
import sys
import django

# --- CONFIGURACIÓN DE DJANGO (La Llave Maestra) ---
# Esto permite que el script funcione por sí solo
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Curso, Pregunta, Tema

def arreglar_temas():
    print("🔌 Conectando con la base de datos...")
    cursos = Curso.objects.all()
    
    if not cursos:
        print("❌ No hay cursos en la base de datos.")
        return

    print(f"📦 Revisando {cursos.count()} cursos para asignación de temas...\n")

    cambios_realizados = False

    for curso in cursos:
        # Buscamos preguntas HUÉRFANAS (sin tema)
        # Nota: 'temas' es el nombre del campo en tu modelo
        huerfanas = Pregunta.objects.filter(curso=curso, temas__isnull=True)
        count = huerfanas.count()

        if count == 0:
            print(f"✅ {curso.nombre}: Todo en orden.")
            continue

        cambios_realizados = True
        print(f"⚠️ {curso.nombre}: Detectadas {count} preguntas sin tema.")

        # Buscamos o creamos un tema destino
        tema_destino = Tema.objects.filter(curso=curso).first()

        if not tema_destino:
            print(f"   > No hay temas. Creando 'Fundamentos Generales'...")
            tema_destino = Tema.objects.create(
                curso=curso, 
                nombre="Fundamentos Generales", 
                descripcion="Tema generado automáticamente por script"
            )
        
        # Asignamos masivamente
        print(f"   > Asignando las {count} preguntas al tema '{tema_destino.nombre}'...")
        
        for pregunta in huerfanas:
            pregunta.temas.add(tema_destino)
            
    if cambios_realizados:
        print("\n✨ ¡Listo! Todas las preguntas tienen tema asignado.")
    else:
        print("\n✨ El inventario ya estaba organizado. No se requirieron cambios.")

if __name__ == "__main__":
    arreglar_temas()