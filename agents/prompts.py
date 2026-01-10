# core/agents/prompts.py

#Define las búsquedas según nivel de dificultad.
def obtener_reglas_nivel(nivel):
    """
    Define la 'Personalidad Pedagógica' según el nivel de dificultad (1-5).
    """
    try:
        nivel = int(nivel)
    except:
        nivel = 3

    niveles = {
        1: {
            "rol": "Maestro de Alfabetización Técnica",
            "estilo": "Definición directa, memoria visual, reconocimiento de interfaz.",
            "longitud_max": "15 palabras",
            "prohibido": "Ambigüedad, casos de uso complejos, excepciones.",
            "ejemplo": "¿Qué icono guarda el archivo? / ¿Qué es una celda?"
        },
        2: {
            "rol": "Instructor de Procedimientos",
            "estilo": "Secuencial (Paso A -> Paso B), Operativo.",
            "longitud_max": "25 palabras",
            "prohibido": "Teoría abstracta sin práctica inmediata.",
            "ejemplo": "Para poner negrita, ¿qué teclas presionas?"
        },
        3: {
            "rol": "Técnico Especialista",
            "estilo": "Resolución de problemas estándar y uso de herramientas.",
            "longitud_max": "40 palabras",
            "prohibido": "Preguntas con respuesta obvia.",
            "ejemplo": "Si quieres filtrar datos únicos, ¿qué herramienta usas?"
        },
        4: {
            "rol": "Analista Senior",
            "estilo": "Diagnóstico de fallos, distinción de matices, optimización.",
            "longitud_max": "Breves escenarios de caso.",
            "prohibido": "Preguntas de memoria pura.",
            "ejemplo": "El proceso falló por timeout, ¿cuál es la causa más probable?"
        },
        5: {
            "rol": "Arquitecto de Soluciones",
            "estilo": "Estrategia, juicio crítico ante variables contradictorias.",
            "longitud_max": "Escenarios complejos.",
            "prohibido": "Soluciones únicas simples (requiere análisis).",
            "ejemplo": "Dado el requerimiento X y la limitación Y, ¿qué arquitectura eliges?"
        }
    }
    return niveles.get(nivel, niveles[3])

# core/agents/prompts.py

def prompt_plan_maestro(nicho, nivel):
    return f"""
    Actúa como un Arquitecto Curricular Senior especializado en Taxonomía Educativa.
    Tu misión es diseñar la estructura de base de datos para un curso de: "{nicho}" (Nivel {nivel} de 1-5).

    ESTRUCTURA DE RESPUESTA REQUERIDA (JSON):
    {{
      "curso": {{
        "nombre": "Título Comercial y Atractivo",
        "descripcion": "Descripción breve enfocada en beneficios.",
        "precio_usd": 19.99
      }},
      "temas": [
        {{
          "nombre": "CATEGORÍA MAESTRA: Subtema Específico", 
          "micro_competencias": [
             {{ 
               "nombre": "Verbo de Acción + Objeto + Contexto", 
               "definicion": "Explicación breve.", 
               "criterio": "Criterio de evaluación." 
             }}
          ]
        }}
      ]
    }}

    🛑 REGLAS CRÍTICAS DE TAXONOMÍA (FORMATO AMAZON):
    
    1. REGLA DEL TEMA (Tags Globales):
       - El campo "nombre" del tema DEBE seguir estrictamente el formato: "CATEGORÍA: Subtema".
       - La CATEGORÍA suele ser la herramienta, lenguaje o habilidad principal.
       - El Subtema es el área específica.
       
       ✅ EJEMPLOS CORRECTOS:
       - "Excel: Fórmulas Lógicas"
       - "Excel: Tablas Dinámicas"
       - "Inglés Negocios: Emails Formales"
       - "Inglés Negocios: Reuniones"
       - "Python: Data Science"
       - "Python: Web Scraping"
       
       ❌ EJEMPLOS PROHIBIDOS (Grave error):
       - "Módulo 1" (No aporta información)
       - "Fórmulas" (Muy genérico, colisiona con otros cursos)
       - "Introducción" (Demasiado vago)

    2. REGLA DE MICRO-COMPETENCIAS:
       - Deben ser atómicas y verificables.
       - Usa nombres autocontenidos.
       - ✅ Bien: "Crear una tabla dinámica con fuentes externas en Excel"
       - ❌ Mal: "Crear tabla"

    3. CANTIDAD:
       - Genera entre 5 y 8 Temas (Categoría: Subtema).
       - Genera entre 2 y 4 Micro-competencias por Tema.
    """

def prompt_generacion_reactivos(mc, nivel):
    return f"""
    Eres un experto en psicometría y evaluación técnica.
    Genera 2 preguntas de selección múltiple (dificultad {nivel}/5) para evaluar la siguiente micro-competencia:
    
    COMPETENCIA: "{mc.nombre}"
    CONTEXTO (Tema): "{mc.temas.first().nombre if mc.temas.exists() else 'General'}"
    DEFINICIÓN: "{mc.definicion_atomica}"

    REGLAS DE FORMATO (JSON ARRAY):
    [
      {{
        "texto": "¿Pregunta situacional o técnica?",
        "opciones": {{
          "a": "Distractor plausible 1",
          "b": "Respuesta Correcta",
          "c": "Distractor plausible 2",
          "d": "Error común"
        }},
        "respuesta_correcta": "b",
        "justificacion": "Explicación breve de por qué 'b' es la correcta."
      }}
    ]
    
    IMPORTANTE:
    - Las preguntas deben ser prácticas, no teóricas.
    - La respuesta correcta debe variar de posición (a, b, c, d) aleatoriamente.
    """

def prompt_generacion_reactivos(mc_obj, nivel):
    reglas = obtener_reglas_nivel(nivel)
    return f"""
    ROL: {reglas['rol']}.
    TAREA: Generar 3 preguntas de selección múltiple.
    MICRO-COMPETENCIA: "{mc_obj.nombre}" ({mc_obj.definicion_atomica}).
    
    RESTRICCIONES NIVEL {nivel}:
    - {reglas['estilo']}
    - Máximo {reglas['longitud_max']}.
    
    RETORNA SOLO JSON:
    [
      {{
        "texto": "¿Pregunta...?",
        "opciones": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
        "respuesta_correcta": "A",
        "justificacion": "Breve explicación.",
        "dificultad": {nivel}
      }}
    ]
    """