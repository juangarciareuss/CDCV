import os
import sys
import time
import django
import json  # <--- IMPORTANTE: Necesario para generar las opciones

# 1. Configuración de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Curso, Pregunta

class AgenteGeneradorDeInventario:
    def __init__(self, meta_preguntas=30):
        self.meta_preguntas = meta_preguntas

    def barra_progreso(self, actual, total, texto="Procesando"):
        percent = 100 * (actual / float(total))
        # Evitamos división por cero o barras infinitas
        sys.stdout.write(f'\r🏭 {texto}: {percent:.1f}%')
        sys.stdout.flush()

    def ejecutar(self):
        print("🔌 Conectando con el Almacén de Datos...")
        cursos = Curso.objects.all()
        print(f"📦 Analizando inventario de {cursos.count()} cursos...")

        for curso in cursos:
            cantidad_actual = Pregunta.objects.filter(curso=curso).count()
            faltantes = self.meta_preguntas - cantidad_actual

            if faltantes <= 0:
                print(f"\n✅ {curso.nombre}: Inventario completo ({cantidad_actual} preguntas).")
                continue

            print(f"\n⚠️ {curso.nombre}: Faltan {faltantes} preguntas. Generando stock...")

            for i in range(faltantes):
                # --- CORRECCIÓN: Generamos opciones válidas ---
                opciones_fake = {
                    "A": "Respuesta generada A",
                    "B": "Respuesta generada B",
                    "C": "Respuesta generada C",
                    "D": "Respuesta generada D"
                }

                try:
                    Pregunta.objects.create(
                        curso=curso,
                        texto=f"Pregunta técnica #{i+1} sobre {curso.nombre} (Generada por IA)",
                        # Enviamos las opciones como Texto JSON para evitar error de formato
                        opciones=json.dumps(opciones_fake), 
                        respuesta_correcta="A", # Asumimos 'A' por defecto
                        nivel=1
                    )
                except Exception as e:
                    print(f"\n❌ Error al crear pregunta: {e}")
                    return # Detenemos para no llenar la pantalla de errores

                self.barra_progreso(i + 1, faltantes, texto="Manufacturando")
                time.sleep(0.05) # Un poco más rápido

            # Actualizamos KPIs del curso
            curso.status = 'OPTIMIZADO'
            curso.score = 30
            curso.save()

        print("\n\n✨ Inventario completado. Actualiza tu Dashboard (F5).")

if __name__ == "__main__":
    agente = AgenteGeneradorDeInventario(meta_preguntas=30)
    agente.ejecutar()