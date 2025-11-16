import json
import os
import django
import sys

"""
SCRIPT DE MIGRACIÓN TEMPORAL (UN SOLO USO)

Este script genera el archivo 'ia_python_10.json' 
usando los IDs de los Temas (Tags) que 'seed_taxonomy' (Sprint 13, Paso 1) acaba de crear,
y migrando las 10 preguntas del antiguo 'curso.py' a 4 opciones.
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
    print("Iniciando generación de 'ia_python_10.json' (con 4 alternativas)...")
    
    # --- 3. DATOS DE LAS PREGUNTAS DE PYTHON (MIGRADO DE curso.py Y CORREGIDO A 4 OPCIONES) ---
    preguntas_python_data = [
        {
            "texto": "¿Cuál es el resultado de 'print(1 + \"1\")'?",
            "opciones": {
                "A": {"texto": "2", "justificacion": "Incorrecto, no se pueden sumar un entero y una cadena de esta forma."},
                "B": {"texto": "11", "justificacion": "Incorrecto, ese sería el resultado de '\"1\" + \"1\"'."},
                "C": {"texto": "TypeError", "justificacion": "Correcto, Python no puede sumar (add) un 'int' y un 'str'."},
                "D": {"texto": "\"11\"", "justificacion": "Incorrecto, este es el resultado de la concatenación de cadenas '\"1\" + \"1\"'."}
            },
            "respuesta_correcta": "C",
            "dificultad": 3, # Esta es una pregunta engañosa
            "tema_nombre": "Sintaxis Básica (Python)"
        },
        {
            "texto": "¿Qué función se usa para obtener la longitud de una lista o cadena?",
            "opciones": {
                "A": {"texto": "count()", "justificacion": "Incorrecto, count() se usa para contar ocurrencias."},
                "B": {"texto": "len()", "justificacion": "Correcto, len() (length) devuelve el número de elementos."},
                "C": {"texto": "size()", "justificacion": "Incorrecto, size() es común en otras librerías (Pandas) pero no en Python base."},
                "D": {"texto": "length()", "justificacion": "Incorrecto, length() es común en otros lenguajes (Java/JS), no en Python."}
            },
            "respuesta_correcta": "B",
            "dificultad": 1,
            "tema_nombre": "Funciones (Python)"
        },
        {
            "texto": "¿Cuál es el tipo de dato de 'True'?",
            "opciones": {
                "A": {"texto": "bool", "justificacion": "Correcto, 'True' y 'False' son de tipo booleano."},
                "B": {"texto": "str", "justificacion": "Incorrecto, 'True' no es una cadena de texto."},
                "C": {"texto": "int", "justificacion": "Incorrecto, aunque True equivale a 1, su tipo es 'bool'."},
                "D": {"texto": "boolean", "justificacion": "Incorrecto, el nombre del tipo en Python es 'bool'."}
            },
            "respuesta_correcta": "A",
            "dificultad": 1,
            "tema_nombre": "Sintaxis Básica (Python)"
        },
        {
            "texto": "Dada la lista 'mi_lista = [10, 20, 30]', ¿qué devuelve 'mi_lista[1]'?",
            "opciones": {
                "A": {"texto": "10", "justificacion": "Incorrecto, 10 es el índice 0."},
                "B": {"texto": "20", "justificacion": "Correcto, Python usa indexación basada en cero."},
                "C": {"texto": "IndexError", "justificacion": "Incorrecto, el índice 1 está dentro de los límites."},
                "D": {"texto": "30", "justificacion": "Incorrecto, 30 es el índice 2."}
            },
            "respuesta_correcta": "B",
            "dificultad": 1,
            "tema_nombre": "Estructuras de Datos (Python)"
        },
        {
            "texto": "¿Qué estructura de datos almacena pares 'clave: valor'?",
            "opciones": {
                "A": {"texto": "list", "justificacion": "Incorrecto, las listas almacenan elementos ordenados."},
                "B": {"texto": "tuple", "justificacion": "Incorrecto, las tuplas son listas inmutables."},
                "C": {"texto": "dict", "justificacion": "Correcto, un diccionario (dict) almacena pares clave-valor."},
                "D": {"texto": "set", "justificacion": "Incorrecto, un set almacena elementos únicos sin orden."}
            },
            "respuesta_correcta": "C",
            "dificultad": 2,
            "tema_nombre": "Estructuras de Datos (Python)"
        },
        {
            "texto": "¿Qué símbolo se usa para escribir comentarios de una sola línea en Python?",
            "opciones": {
                "A": {"texto": "//", "justificacion": "Incorrecto, esto es común en lenguajes como C++ o Java."},
                "B": {"texto": "#", "justificacion": "Correcto, el símbolo de numeral inicia un comentario."},
                "C": {"texto": "/* ... */", "justificacion": "Incorrecto, esto es para comentarios multilínea en otros lenguajes."},
                "D": {"texto": "", "justificacion": "Incorrecto, esto es un comentario HTML."}
            },
            "respuesta_correcta": "B",
            "dificultad": 1,
            "tema_nombre": "Sintaxis Básica (Python)"
        },
        {
            "texto": "¿Qué método se usa para añadir un elemento al final de una lista?",
            "opciones": {
                "A": {"texto": ".add()", "justificacion": "Incorrecto, .add() es para 'sets' (conjuntos)."},
                "B": {"texto": ".push()", "justificacion": "Incorrecto, .push() es de JavaScript."},
                "C": {"texto": ".append()", "justificacion": "Correcto, .append() añade el elemento al final de la lista."},
                "D": {"texto": ".insert()", "justificacion": "Incorrecto, .insert() añade en un índice específico, no necesariamente al final."}
            },
            "respuesta_correcta": "C",
            "dificultad": 2,
            "tema_nombre": "Estructuras de Datos (Python)"
        },
        {
            "texto": "¿Qué palabra clave se usa para definir una función en Python?",
            "opciones": {
                "A": {"texto": "def", "justificacion": "Correcto, se usa 'def nombre_funcion():'."},
                "B": {"texto": "function", "justificacion": "Incorrecto, 'function' es de JavaScript y otros lenguajes."},
                "C": {"texto": "fun", "justificacion": "Incorrecto, 'fun' es de Kotlin o Swift."},
                "D": {"texto": "define", "justificacion": "Incorrecto."}
            },
            "respuesta_correcta": "A",
            "dificultad": 1,
            "tema_nombre": "Funciones (Python)"
        },
        {
            "texto": "¿Cuál es el operador para 'igualdad' (comparación)?",
            "opciones": {
                "A": {"texto": "=", "justificacion": "Incorrecto, '=' es el operador de asignación."},
                "B": {"texto": "==", "justificacion": "Correcto, '==' compara si dos valores son iguales."},
                "C": {"texto": "!=", "justificacion": "Incorrecto, '!=' es el operador de 'diferente a'."},
                "D": {"texto": "<=", "justificacion": "Incorrecto, es 'menor o igual que'."}
            },
            "respuesta_correcta": "B",
            "dificultad": 1,
            "tema_nombre": "Sintaxis Básica (Python)"
        },
        {
            "texto": "¿Qué hace la construcción 'if __name__ == \"__main__\":'?",
            "opciones": {
                "A": {"texto": "Define la función principal 'main'.", "justificacion": "Incorrecto, solo es una comprobación, no define nada."},
                "B": {"texto": "Comprueba si el script se está ejecutando directamente.", "justificacion": "Correcto, el código dentro de este bloque solo se ejecuta si el archivo es corrido como script principal."},
                "C": {"texto": "Inicia un hilo (thread) principal.", "justificacion": "Incorrecto, no tiene relación con multithreading."},
                "D": {"texto": "Comprueba si la clase es la principal.", "justificacion": "Incorrecto, comprueba el módulo, no la clase."}
            },
            "respuesta_correcta": "B",
            "dificultad": 3,
            "tema_nombre": "Conceptos Clave (Python)"
        }
    ]
    
    # --- 4. MAPEO DE DATOS AL NUEVO FORMATO ROBUSTO ---
    
    output_json = []
    
    for q in preguntas_python_data:
        
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
                    "revisado_por_agente": True # Marcamos como revisadas por nosotros (ya que las migramos)
                }
            ]
        }
        output_json.append(nueva_pregunta)

    # --- 5. GUARDAR EL ARCHIVO JSON ---
    output_filename = "ia_python_10.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False)
        
    print(f"¡Éxito! Se ha generado el archivo '{output_filename}' con 10 preguntas (de 4 alternativas).")
    print("El siguiente paso (Paso 3) es ejecutar:")
    print(f"python manage.py import_questions --file {output_filename}")

if __name__ == "__main__":
    main()