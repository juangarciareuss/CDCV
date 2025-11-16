import json
import os
import django
import sys

"""
SCRIPT DE MIGRACIÓN TEMPORAL (UN SOLO USO)

Este script genera el archivo 'ia_prompts_10.json' 
usando los IDs de los Temas (Tags) que 'seed_taxonomy' acaba de crear.
(VERSIÓN CORREGIDA CON 4 ALTERNATIVAS POR PREGUNTA)
"""

# --- 1. CONFIGURAR EL ENTORNO DE DJANGO ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT) 
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# --- 2. IMPORTAR MODELOS ---
from core.models import Tema

def get_tema_id(nombre):
    """Función helper para obtener el ID de un Tema (Tag) por su nombre."""
    try:
        return Tema.objects.get(nombre=nombre).id
    except Tema.DoesNotExist:
        print(f"Error CRÍTICO: El Tema (Tag) '{nombre}' no existe. Ejecuta 'seed_taxonomy' primero.")
        sys.exit(1)

def main():
    print("Iniciando generación de 'ia_prompts_10.json' (con 4 alternativas)...")
    
    # --- 3. DATOS DE LAS PREGUNTAS DE IA (CORREGIDO CON 4 OPCIONES) ---
    preguntas_ia_data = [
        # Preguntas de Conceptos Básicos (4)
        {
            "texto": "¿Qué se conoce como 'Zero-shot prompting'?", 
            "opciones": {
                "A": { "texto": "Proporcionar al modelo solo la tarea, sin ejemplos previos.", "justificacion": "Correcto. El modelo debe responder basándose solo en su entrenamiento." }, 
                "B": { "texto": "Pedir a la IA que genere código en un solo paso.", "justificacion": "Incorrecto." }, 
                "C": { "texto": "Usar la salida de un prompt como entrada del siguiente.", "justificacion": "Incorrecto, eso es Chain-of-Thought." },
                "D": { "texto": "Darle a la IA un ejemplo de la tarea.", "justificacion": "Incorrecto, eso es 'One-shot prompting'." }
            }, 
            "respuesta_correcta": "A",
            "dificultad": 2,
            "tema_nombre": "Zero-shot / Few-shot" # Usamos el nombre del Tag
        },
        {
            "texto": "¿Qué elemento es fundamental para definir el tono de la respuesta de una IA?", 
            "opciones": {
                "A": { "texto": "La extensión del prompt.", "justificacion": "Incorrecto, la extensión afecta el detalle, no el tono." }, 
                "B": { "texto": "Asignar un 'Rol' (ej. 'Actúa como un profesor universitario...').", "justificacion": "Correcto. El Rol dirige el estilo y la perspectiva de la respuesta." }, 
                "C": { "texto": "Usar solo mayúsculas.", "justificacion": "Incorrecto." },
                "D": { "texto": "Preguntar en un idioma extranjero.", "justificacion": "Incorrecto." }
            }, 
            "respuesta_correcta": "B",
            "dificultad": 1,
            "tema_nombre": "Roles y Formatos"
        },
        {
            "texto": "Para que una IA dé una respuesta concisa, ¿qué instrucción es la más efectiva?", 
            "opciones": {
                "A": { "texto": "Utiliza un lenguaje poético.", "justificacion": "Incorrecto, eso haría la respuesta más larga." }, 
                "B": { "texto": "Responde en un máximo de 50 palabras.", "justificacion": "Correcto. La restricción explícita es la mejor manera de controlar el formato." }, 
                "C": { "texto": "Ignora todos los detalles.", "justificacion": "Incorrecto, es ambiguo." },
                "D": { "texto": "Pedirle que sea 'muy inteligente'.", "justificacion": "Incorrecto, demasiado vago." }
            }, 
            "respuesta_correcta": "B",
            "dificultad": 1,
            "tema_nombre": "Conceptos Básicos de Prompts"
        },
        {
            "texto": "¿Cuál es el objetivo de usar delimitadores (ej. comillas triples) en un prompt?", 
            "opciones": {
                "A": { "texto": "Hacer que el prompt se vea más ordenado.", "justificacion": "Incorrecto." }, 
                "B": { "texto": "Separar claramente las instrucciones del texto que la IA debe procesar.", "justificacion": "Correcto. Esto reduce la posibilidad de que la IA se confunda." }, 
                "C": { "texto": "Forzar una respuesta en código.", "justificacion": "Incorrecto." },
                "D": { "texto": "Aumentar la dificultad de la tarea.", "justificacion": "Incorrecto." }
            }, 
            "respuesta_correcta": "B",
            "dificultad": 2,
            "tema_nombre": "Conceptos Básicos de Prompts"
        },
        # Preguntas de Técnicas (3)
        {
            "texto": "¿Qué término describe el fenómeno en el que la IA genera información falsa pero convincente?", 
            "opciones": {
                "A": { "texto": "Overfitting", "justificacion": "Incorrecto, es un término de Machine Learning." }, 
                "B": { "texto": "Alucinación (Hallucination).", "justificacion": "Correcto. Este es el principal riesgo al confiar ciegamente en la IA." }, 
                "C": { "texto": "Tokenización", "justificacion": "Incorrecto, es un proceso de lenguaje." },
                "D": { "texto": "Context Window.", "justificacion": "Incorrecto, es un término relacionado pero distinto." }
            }, 
            "respuesta_correcta": "B",
            "dificultad": 2,
            "tema_nombre": "Conceptos Básicos de Prompts"
        },
        {
            "texto": "Si pides a la IA que actúe como un 'revisor de código', ¿qué componente del prompt estás usando?", 
            "opciones": {
                "A": { "texto": "La Tarea.", "justificacion": "Incorrecto, la tarea sería 'revisar el código'." }, 
                "B": { "texto": "El Rol (Persona).", "justificacion": "Correcto. El Rol define la identidad y el contexto del modelo." }, 
                "C": { "texto": "El Formato de Salida.", "justificacion": "Incorrecto." },
                "D": { "texto": "La Temperatura (Temp).", "justificacion": "Incorrecto, la temperatura es un parámetro del modelo, no un componente del prompt." }
            }, 
            "respuesta_correcta": "B",
            "dificultad": 2,
            "tema_nombre": "Roles y Formatos"
        },
        {
            "texto": "¿Qué es la 'Cadena de Pensamiento' (Chain-of-Thought)?", 
            "opciones": {
                "A": { "texto": "Pedir a la IA que se tome un momento para pensar y explicar su razonamiento antes de dar la respuesta final.", "justificacion": "Correcto. Mejora la precisión de la respuesta final." }, 
                "B": { "texto": "Un error de la IA.", "justificacion": "Incorrecto."}, 
                "C": { "texto": "Un tipo de dato.", "justificacion": "Incorrecto." },
                "D": { "texto": "El modelo de IA más rápido.", "justificacion": "Incorrecto." }
            }, 
            "respuesta_correcta": "A",
            "dificultad": 3,
            "tema_nombre": "Chain-of-Thought (CoT)"
        },
        # Preguntas de Roles y Formatos (3)
        {
            "texto": "En el prompt: 'Dime los pasos para arreglar una lámpara rota. Formato: Lista numerada.' ¿Cuál es la 'Restricción'?", 
            "opciones": {
                "A": { "texto": "Arreglar una lámpara rota.", "justificacion": "Incorrecto, esa es la Tarea." }, 
                "B": { "texto": "Lista numerada.", "justificacion": "Correcto. Es una restricción sobre el formato de salida." }, 
                "C": { "texto": "Dime los pasos.", "justificacion": "Incorrecto." },
                "D": { "texto": "La lámpara.", "justificacion": "Incorrecto, es el sujeto." }
            }, 
            "respuesta_correcta": "B",
            "dificultad": 1,
            "tema_nombre": "Roles y Formatos"
        },
        {
            "texto": "¿Cuál es la forma más común de usar 'Few-shot prompting'?", 
            "opciones": {
                "A": { "texto": "Dar al modelo 1 a 3 ejemplos de la tarea y su respuesta esperada antes de pedirle que resuelva el caso final.", "justificacion": "Correcto. Guía el modelo hacia el formato deseado." }, 
                "B": { "texto": "Usar solo un prompt de una sola línea.", "justificacion": "Incorrecto."}, 
                "C": { "texto": "Restringir la respuesta a 5 palabras.", "justificacion": "Incorrecto." },
                "D": { "texto": "Pedir la respuesta en formato JSON.", "justificacion": "Incorrecto, eso es una restricción de formato." }
            }, 
            "respuesta_correcta": "A",
            "dificultad": 2,
            "tema_nombre": "Zero-shot / Few-shot"
        },
        {
            "texto": "¿Qué se debe hacer si la IA ignora una instrucción crítica?", 
            "opciones": {
                "A": { "texto": "Eliminar la instrucción.", "justificacion": "Incorrecto." }, 
                "B": { "texto": "Repetir la instrucción al final del prompt y usar mayúsculas y delimitadores para enfatizarla.", "justificacion": "Correcto. La reescritura y el énfasis suelen ser efectivos." }, 
                "C": { "texto": "Reducir la complejidad de la tarea.", "justificacion": "Incorrecto." },
                "D": { "texto": "Reiniciar la conversación.", "justificacion": "Incorrecto, eso es una acción de UI, no una técnica de prompt." }
            }, 
            "respuesta_correcta": "B",
            "dificultad": 2,
            "tema_nombre": "Conceptos Básicos de Prompts"
        }
    ]
    
    # --- 4. MAPEO DE DATOS AL NUEVO FORMATO ROBUSTO ---
    
    output_json = []
    
    for q in preguntas_ia_data:
        
        # Obtenemos el ID del Tema (Tag) de la base de datos
        tema_id = get_tema_id(q["tema_nombre"])
        
        # Creamos la nueva estructura JSON que espera 'import_questions'
        nueva_pregunta = {
            "texto": q["texto"],
            "opciones": q["opciones"],
            "respuesta_correcta": q["respuesta_correcta"],
            "dificultad": q["dificultad"],
            "idioma": "es",
            "temas": [
                {
                    "tema_id": tema_id,
                    "relevancia_score": 1.0, 
                    "revisado_por_agente": True # Marcamos como revisadas por nosotros
                }
            ]
        }
        output_json.append(nueva_pregunta)

    # --- 5. GUARDAR EL ARCHIVO JSON ---
    output_filename = "ia_prompts_10.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False)
        
    print(f"¡Éxito! Se ha generado el archivo '{output_filename}' con 10 preguntas (de 4 alternativas).")
    print("El siguiente paso es ejecutar:")
    print(f"python manage.py import_questions --file {output_filename}")

if __name__ == "__main__":
    main()