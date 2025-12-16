import os
import sys
import json
import django

# --- 1. CONFIGURACIÓN DEL ENTORNO (CRÍTICO: ESTO VA PRIMERO) ---
# Añadimos el directorio actual al path del sistema
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Le decimos a Django cuál es el archivo de configuración
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Iniciamos Django.
# Si intentas importar modelos ANTES de esta línea, el script fallará.
django.setup()

# --- 2. IMPORTAR MODELOS (AHORA ES SEGURO HACERLO) ---
from django.db import transaction
from core.models import Tema, Curso, Pregunta

def importar_json():
    archivo_json = 'powerbi_avanzado.json'
    
    print(f"Iniciando carga desde {archivo_json}...")

    # Verificación de existencia del archivo
    if not os.path.exists(archivo_json):
        print(f"ERROR: No se encuentra el archivo {archivo_json} en la raíz.")
        return

    try:
        # Lectura del archivo JSON
        with open(archivo_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Transacción atómica para asegurar integridad de datos
        with transaction.atomic():
            # A. Crear o Obtener Tema
            tema_nombre = data.get('tema_principal', 'General')
            tema, _ = Tema.objects.get_or_create(nombre=tema_nombre)
            print(f"Tema procesado: {tema.nombre}")

            # B. Crear o Obtener Curso
            curso, created = Curso.objects.get_or_create(
                nombre=data['nombre_curso'],
                tema=tema,
                defaults={
                    'nivel': data.get('nivel', 1),
                    'descripcion': data.get('descripcion', ''),
                    'idioma': data.get('idioma', 'es')
                }
            )
            
            if created:
                print(f"Curso CREADO: {curso.nombre}")
            else:
                print(f"Curso EXISTENTE: {curso.nombre} (Se añadirán preguntas nuevas si no existen)")

            # C. Cargar Preguntas
            preguntas = data.get('preguntas', [])
            contador_nuevas = 0
            
            print(f"Procesando {len(preguntas)} preguntas...")
            
            for p_data in preguntas:
                # Usamos get_or_create para no duplicar preguntas si corres el script varias veces
                pregunta, p_created = Pregunta.objects.get_or_create(
                    curso=curso,
                    texto=p_data['texto'],
                    defaults={
                        'opciones': p_data['opciones'],
                        'respuesta_correcta': p_data['respuesta_correcta'],
                        'dificultad': p_data.get('dificultad', 1),
                        # Mapeo para campos legacy si existen en tu modelo
                        'nivel': p_data.get('dificultad', 1), 
                        'idioma': data.get('idioma', 'es')
                    }
                )
                if p_created:
                    contador_nuevas += 1

            print("-" * 30)
            print(f"¡Éxito! Se cargaron {contador_nuevas} preguntas nuevas.")
            print(f"Total de preguntas en el curso: {curso.pregunta_set.count()}")
            print("-" * 30)

    except json.JSONDecodeError:
        print("ERROR: El archivo JSON tiene un formato inválido.")
    except Exception as e:
        print(f"ERROR INESPERADO: {e}")

if __name__ == "__main__":
    importar_json()