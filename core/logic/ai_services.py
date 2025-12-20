# core/ai_services.py
import json
import os
from google import genai
from dotenv import load_dotenv
import pandas as pd
import time
from tqdm import tqdm
import os

# Importación absoluta desde la raíz del proyecto
from core.logic.analytics import obtener_kpis_globales

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def agente_constructor_de_negocio(nicho_mercado):
    """
    Agente Autónomo de Negocios.
    Extrae contenido puro de Gemini 2.5 y lo inyecta en Django.
    """
    from ..models import Curso, Tema, Pregunta, PreguntaTema
    import json

    # 1. Definimos el Prompt con una instrucción de formato estricta
    prompt = f"""
    Eres un Agente de Inteligencia de Negocios. Genera un producto educativo para: '{nicho_mercado}'.
    Responde ÚNICAMENTE con un objeto JSON que tenga esta estructura exacta:
    {{
      "nombre_comercial": "título",
      "descripcion_marketing": "descripción",
      "receta": [
        {{"tema_nombre": "tema1", "cantidad": 5, "dificultad_min": 1, "dificultad_max": 5}}
      ],
      "contenido": [
        {{
          "tema": "tema1",
          "preguntas": [
            {{
              "texto": "pregunta",
              "opciones": {{"a": "1", "b": "2", "c": "3", "d": "4"}},
              "correcta": "a"
            }}
          ]
        }}
      ]
    }}
    """

    try:
        # 2. Llamada al modelo (Gemini 2.5 Flash)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        # 3. EXTRACCIÓN LÓGICA SEGURA (Aquí estaba el fallo)
        # Forzamos la obtención del texto y su conversión a dict
        raw_text = response.text
        data = json.loads(raw_text)

        if not data:
            return "❌ Error: La IA devolvió un objeto vacío."

        # 4. Creación del Curso
        curso = Curso.objects.create(
            nombre=data['nombre_comercial'],
            descripcion=data['descripcion_marketing'],
            estructura_examen={"reglas_seleccion": data['receta']}
        )

        # 5. Creación de Activos
        for bloque in data['contenido']:
            # Obtenemos o creamos el tema
            tema_obj, _ = Tema.objects.get_or_create(nombre=bloque['tema'])
            
            for p in bloque['preguntas']:
                # Creamos la pregunta
                nueva_p = Pregunta.objects.create(
                    texto=p['texto'],
                    opciones=p['opciones'],
                    respuesta_correcta=p['correcta'],
                    dificultad=3,
                    idioma='es'
                )
                # Vinculamos al tema usando la tabla intermedia (Many-to-Many)
                PreguntaTema.objects.create(
                    pregunta=nueva_p,
                    tema=tema_obj,
                    relevancia_score=1.0,
                    revisado_por_agente=True
                )

        return f"🚀 ÉXITO: El curso '{curso.nombre}' ha sido creado y poblado con sus temas y preguntas."

    except Exception as e:
        # Este print te dirá exactamente qué campo falló en la consola
        print(f"DEBUG: Error detallado -> {str(e)}")
        return f"❌ Error en el Agente Constructor: {str(e)}"

def agente_poblador_v3(tema_objetivo, cantidad=10):
    """
    Agente de Curaduría basado en Gemini 2.5 Flash.
    Genera, etiqueta y puntúa preguntas para el Banco Universal.
    """
    
    # Importación diferida para evitar problemas de carga circular en Django
    from ..models import Tema, Pregunta, PreguntaTema
    
    # Obtenemos tu taxonomía actual
    temas_existentes = list(Tema.objects.values_list('nombre', flat=True))
    
    config_agente = {
        "temperature": 0.7,
        "response_mime_type": "application/json",
    }

    prompt = f"""
    Eres un Agente Senior de Certificación de Competencias Digitales (CDCV).
    Tu misión: Generar {cantidad} reactivos técnicos de alta calidad sobre '{tema_objetivo}'.
    
    TAXONOMÍA DISPONIBLE EN EL SISTEMA: {temas_existentes}
    
    INSTRUCCIONES DE RAZONAMIENTO:
    1. Calidad: Las preguntas deben evaluar criterio profesional, no solo memoria.
    2. Asociación: Identifica qué temas de la TAXONOMÍA se relacionan con cada pregunta.
    3. Scoring: Asigna un peso (0.0 a 1.0) según la relevancia de la pregunta para ese tema.
    4. Formato: Devuelve un JSON puro.
    
    ESTRUCTURA DE RESPUESTA:
    [
      {{
        "texto": "Pregunta...",
        "opciones": {{"a": "op1", "b": "op2", "c": "op3", "d": "op4"}},
        "correcta": "a",
        "dificultad": 3,
        "explicacion": "...",
        "asociaciones": [
          {{"tema": "Nombre del Tema", "score": 0.95}}
        ]
      }}
    ]
    """

    try:
        # Usamos Gemini 2.5 Flash para balance perfecto entre velocidad y razonamiento
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config_agente
        )
        
        # El nuevo SDK ya maneja mejor el objeto de respuesta
        data = response.parsed if hasattr(response, 'parsed') else json.loads(response.text)
        
        contador = 0
        for item in data:
            # 1. Crear la pregunta en el Banco
            pregunta = Pregunta.objects.create(
                texto=item['texto'],
                opciones=item['opciones'],
                respuesta_correcta=item['correcta'],
                dificultad=item['dificultad'],
                # Guardamos la explicación si existe (bueno para el usuario)
                idioma='es'
            )
            
            # 2. El Agente vincula Many-to-Many
            for asoc in item['asociaciones']:
                t_obj = Tema.objects.filter(nombre=asoc['tema']).first()
                if t_obj:
                    PreguntaTema.objects.create(
                        pregunta=pregunta,
                        tema=t_obj,
                        relevancia_score=asoc['score'],
                        revisado_por_agente=True
                    )
            contador += 1
            
        return f"✅ Agente 2.5 finalizó: {contador} nuevas preguntas en el banco."

    except Exception as e:
        return f"❌ Fallo en Agente 2.5: {str(e)}"
    