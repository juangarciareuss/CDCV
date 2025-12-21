import json
import os
import random
from google import genai
from dotenv import load_dotenv
from core.models import Curso, Tema, Pregunta, PreguntaTema


load_dotenv()

class BuilderAgent:
    """
    Agente Constructor: Basado en tu función 'agente_constructor_de_negocio'.
    """
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        # Mantenemos tu modelo preferido
        self.model = "gemini-2.5-flash"

    def construir_negocio(self, nicho_mercado):
        # TU PROMPT ORIGINAL (INTACTO)
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
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            
            # Tu lógica de extracción segura
            data = json.loads(response.text)
            if not data: return "❌ Error: La IA devolvió un objeto vacío."

            # Tu lógica de creación de Curso
            curso = Curso.objects.create(
                nombre=data['nombre_comercial'],
                descripcion=data['descripcion_marketing'],
                estructura_examen={"reglas_seleccion": data['receta']}
            )

            # Tu lógica de creación de Activos
            for bloque in data['contenido']:
                tema_obj, _ = Tema.objects.get_or_create(nombre=bloque['tema'])
                for p in bloque['preguntas']:
                    nueva_p = Pregunta.objects.create(
                        texto=p['texto'],
                        opciones=p['opciones'],
                        respuesta_correcta=p['correcta'],
                        dificultad=random.randint(1, 5),
                        idioma='es'
                    )
                    PreguntaTema.objects.create(
                        pregunta=nueva_p, tema=tema_obj, relevancia_score=1.0, revisado_por_agente=True
                    )

            return f"🚀 ÉXITO: El curso '{curso.nombre}' ha sido creado."

        except Exception as e:
            print(f"DEBUG: Error detallado -> {str(e)}")
            return f"❌ Error en BuilderAgent: {str(e)}"