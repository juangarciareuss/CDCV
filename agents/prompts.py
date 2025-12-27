# core/agents/prompts.py

def obtener_reglas_nivel(nivel):
    try:
        nivel = int(nivel)
    except:
        nivel = 3

    niveles = {
        1: {
            "rol": "Maestro de Alfabetización Técnica",
            "longitud_max": "15 palabras por pregunta",
            "estilo": "Definición directa y Memoria visual.",
            "prohibido": "Contextos, historias, casos de uso, ambigüedad.",
            "ejemplo_abstracto": "¿Qué es X? / Selecciona el icono de Y."
        },
        2: {
            "rol": "Instructor de Procedimientos Básicos",
            "longitud_max": "25 palabras por pregunta",
            "estilo": "Secuencial y Operativo (Causa-Efecto simple).",
            "prohibido": "Excepciones a la regla o análisis profundo.",
            "ejemplo_abstracto": "¿Cuál es el paso siguiente a X? / Para lograr Y, se usa Z."
        },
        3: {
            "rol": "Técnico Especialista Estándar",
            "longitud_max": "40 palabras por pregunta",
            "estilo": "Aplicación en situaciones cotidianas.",
            "prohibido": "Teoría pura sin práctica.",
            "ejemplo_abstracto": "Para resolver el problema común A, ¿qué herramienta usas?"
        },
        4: {
            "rol": "Analista Senior / Auditor",
            "longitud_max": "Sin límite estricto (Escenarios breves)",
            "estilo": "Análisis de Fallos y Distinción.",
            "prohibido": "Respuestas obvias. Debe haber distractores plausibles.",
            "ejemplo_abstracto": "El sistema falló con error X, ¿cuál es la causa raíz?"
        },
        5: {
            "rol": "Experto Mundial / Arquitecto",
            "longitud_max": "Extensa (Casos complejos)",
            "estilo": "Juicio Crítico, Estrategia y Síntesis.",
            "prohibido": "Preguntas de memoria simple.",
            "ejemplo_abstracto": "Dado el escenario con variables contradictorias X, Y, Z, ¿cuál es la estrategia óptima?"
        }
    }
    return niveles.get(nivel, niveles[3])

def prompt_plan_maestro(nicho, nivel): # <--- AHORA RECIBE EL NIVEL
    """
    Prompt para diseñar el Syllabus (Temario) adaptado al Nivel.
    """
    reglas = obtener_reglas_nivel(nivel)
    
    return f"""
    ACTÚA COMO UN: {reglas['rol']}.
    
    Diseña la especificación técnica de certificación de NIVEL {nivel} para: '{nicho}'.
    
    ENFOQUE DEL CURSO (NIVEL {nivel}):
    - Estilo: {reglas['estilo']}
    - Objetivo: {reglas['ejemplo_abstracto']}
    
    REGLAS CRÍTICAS DE DISEÑO DE DATOS:
    1. NAMESPACING: Cada competencia inicia con la Tecnología/Concepto (Ej: "Excel: Tablas").
    2. DETERMINISMO: Verbos de acción técnica.
    3. TÍTULO: Debe reflejar el nivel (Ej: "Introducción a..." vs "Maestría en...").
    
    FORMATO JSON SOLICITADO:
    {{
      "curso": {{ 
          "nombre": "Título del Curso acorde al Nivel {nivel}", 
          "descripcion": "Descripción del alcance para este nivel...", 
          "precio_usd": 5.00 
      }},
      "temas": [
        {{
          "nombre": "Nombre del Módulo (Acorde a dificultad)", 
          "micro_competencias": [
            {{ "nombre": "Tecnología: Acción Técnica", "definicion": "...", "criterio": "..." }}
          ]
        }}
      ]
    }}
    Devuelve SOLO JSON válido.
    """

def prompt_generacion_reactivos(mc_obj, nivel):
    reglas = obtener_reglas_nivel(nivel)
    return f"""
    ROL: {reglas['rol']}.
    TAREA: Crea 3 preguntas de selección múltiple para: "{mc_obj.nombre}".
    DEFINICIÓN: {mc_obj.definicion_atomica}
    
    CONFIGURACIÓN NIVEL {nivel}:
    - Longitud Máx: {reglas['longitud_max']}.
    - Estilo: {reglas['estilo']}
    - PROHIBIDO: {reglas['prohibido']}
    
    FORMATO JSON:
    [
      {{
        "texto": "Pregunta...",
        "opciones": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
        "respuesta_correcta": "A",
        "justificacion": "...",
        "dificultad": {nivel}
      }}
    ]
    Devuelve SOLO JSON válido.
    """