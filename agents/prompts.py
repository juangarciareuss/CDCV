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
            "rol": "Instructor de Fundamentos y conceptos básicos",
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

def prompt_arquitectura_curso(nicho, nivel):
    
    if ":" in nicho:
        base = nicho.split(":")[0].strip()
    else:
        base = nicho.strip()
    
    return f"""
    Actúa como un Arquitecto de Datos Educativos y Experto en SEO.
    Tu misión es diseñar la estructura de base de datos para una certificación de: "{nicho}" (Nivel {nivel} de 1-5).

    ESTRUCTURA DE RESPUESTA REQUERIDA (JSON):
    {{
      "curso": {{
        "descripcion": "Descripción técnica objetiva enfocada en validación de competencias."
      }},
      "temas": [
        {{
          "nombre": "{base}: Subtema Específico", 
          "micro_competencias": [
             {{ 
               "nombre": "Nombre técnico de la competencia", 
               "slug_seo": "como-hacer-la-accion-exacta",
               "definicion": "Explicación atómica.", 
               "criterio": "Criterio de éxito." 
             }}
          ]
        }}
      ]
    }}

    🛑 REGLAS CRÍTICAS de Taxonomía:
    
    1. REGLA DEL TEMA (FORMATO PATH):
       - El campo "nombre" del tema DEBE seguir estrictamente el formato: "Categoria: Subtema". Si tiene más de un subtema puede ser 
       Categoría:subtema:subtema (subtema tantas veces como subcategorías queremos crear).
       - La Categoría y los subtemas, la primera letra debe ser mayúscula por cada palabra relevante
       - ✅ CORRECTO: "Excel: Filtros
       - ✅ CORRECTO: "Excel: Fórmulas: Fórmulas de Texto"
       - ❌ PROHIBIDO: "Fórmulas" (Sin contexto).

    2. REGLA DE MICRO-COMPETENCIAS (SLUG SEO):
       - El campo "slug_seo" es CRÍTICO. Debe responder a lo que el usuario escribe en Google.
       - Debe usar formato: "como-accion-objeto" o "que-es-concepto".
       - Debe tener un máximo de 6 palabras
       - ✅ Bien: "como-fijar-celdas-excel"
       - ✅ Bien: "como-crear-tabla-dinamica"
       - ✅ Bien: "diferencia-buscarv-buscarx"
       - ✅ Bien: "Inglés Negocios: Emails Formales"
       - ✅ Bien:"Inglés Negocios: Reuniones"
       - ✅ Bien:"Python: Data Science"
       - ✅ Bien:"Python: Web Scraping"
       - ❌ Mal: "fijar-celdas" (Muy corto)
       - ❌ Mal: "aprender-a-fijar-las-celdas-de-forma-correcta" (Muy largo, máx 6 palabras).

    3. CANTIDAD:
       - Genera entre 5 Temas
       - Genera entre 4 Micro-competencias por Tema.

    4. CONTENIDO
       ⚠️ INSTRUCCIÓN CRÍTICA DE CONTENIDO:
    - El contenido debe ser **100% sobre "{nicho}"**.

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