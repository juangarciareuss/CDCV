import json
import os
import time
import random
from google import genai
from google.genai import types 
from dotenv import load_dotenv
from core.models import Tema, Pregunta, PreguntaTema

load_dotenv()

class RefillerAgent:
    """
    Agente Poblador Maestro (Versión Definitiva).
    Características:
    - Prioridad de Modelos: Gemini 3 (Calidad) -> Gemini 2 (Velocidad) -> Gemini 1.5 (Estabilidad).
    - Fallback Agresivo: Ante cualquier error, cambia de modelo sin detenerse.
    - Distribución de Dificultad: Asegura variedad para el motor de exámenes.
    """
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # 👑 LISTA DE PRIORIDAD (De mejor a más seguro)
        self.modelos = [
            "gemini-2.5-flash",    # 2. El Deportivo (Rápido, experimental)
            "gemini-2.0-flash"         # 3. El Tanque (Mucha cuota, nunca falla)
        ]

    def _generar_con_fallback(self, prompt, config):
        """
        Intenta generar contenido rotando por la lista de modelos.
        Si uno falla, salta al siguiente inmediatamente.
        """
        errores_log = []
        
        for modelo_actual in self.modelos:
            try:
                # print(f"🤖 Intentando con modelo: {modelo_actual}...") # Debug opcional
                
                response = self.client.models.generate_content(
                    model=modelo_actual,
                    contents=prompt,
                    config=config
                )
                
                # Si llegamos aquí, FUNCIONÓ. Retornamos respuesta y el nombre del modelo ganador.
                return response, modelo_actual 
                
            except Exception as e:
                # 🔥 FALLBACK AGRESIVO
                # No importa el error (Cuota 429, Servidor 500, etc), pasamos al siguiente.
                mensaje_corto = str(e)[:100]
                print(f"⚠️ {modelo_actual} falló ({mensaje_corto}...). Saltando al siguiente...")
                
                errores_log.append(f"{modelo_actual}: {mensaje_corto}")
                time.sleep(1) # Pequeña pausa de seguridad
                continue # Forza la siguiente iteración del bucle

        # Si sale del bucle, es que fallaron los 3 modelos
        raise Exception(f"❌ TODOS los modelos fallaron. Detalles: {errores_log}")

    def poblar_tema(self, tema_objetivo, cantidad=5):
        """
        Genera preguntas para un tema específico y las guarda en la BD.
        """
        # 1. Contexto: Le damos a la IA los temas que ya existen para que intente reutilizarlos
        temas_existentes = list(Tema.objects.values_list('nombre', flat=True))
        
        config_agente = {
            "temperature": 0.7,
            "response_mime_type": "application/json",
        }

        # 2. Prompt de Ingeniería Robusto
        prompt = f"""
        Eres un Agente Senior de Certificación (CDCV).
        Misión: Generar {cantidad} reactivos técnicos de alta calidad sobre '{tema_objetivo}'.
        
        TAXONOMÍA EXISTENTE (Úsala si aplica): {temas_existentes}
        
        INSTRUCCIONES:
        1. Evalúa criterio profesional y técnico.
        2. Genera preguntas variadas (Conceptuales, Prácticas, Casos).
        3. Formato JSON estricto.
        
        ESTRUCTURA JSON REQUERIDA:
        [
          {{
            "texto": "Enunciado claro de la pregunta...",
            "opciones": {{"a": "Opción 1", "b": "Opción 2", "c": "Opción 3", "d": "Opción 4"}},
            "correcta": "a", 
            "dificultad": 3, 
            "explicacion": "Breve explicación de por qué es la correcta.",
            "asociaciones": [
              {{"tema": "{tema_objetivo}", "score": 0.95}}
            ]
          }}
        ]
        """

        try:
            # 3. Llamada Inteligente (Con Fallback)
            response, modelo_usado = self._generar_con_fallback(prompt, config_agente)
            
            # 4. Procesamiento
            data = json.loads(response.text)
            contador = 0

            for item in data:
                # 🛡️ LÓGICA DE DIFICULTAD (Para evitar error "Stock 0")
                # Si la IA manda siempre 3, introducimos variedad aleatoria (1-5)
                # para que el motor de examen encuentre preguntas fáciles y difíciles.
                dificultad_final = item.get('dificultad', 3)
                if dificultad_final == 3: 
                    # Pequeño "fuzzing" para distribuir mejor
                    dificultad_final = random.randint(1, 5)

                # Creación de la Pregunta
                pregunta = Pregunta.objects.create(
                    texto=item['texto'],
                    opciones=item['opciones'],
                    respuesta_correcta=item['correcta'],
                    dificultad=dificultad_final,
                    idioma='es'
                    # activo=True (Descomentar si agregas el campo activo al modelo Pregunta)
                )

                # Asociación con Temas (Reutilizables)
                for asoc in item.get('asociaciones', []):
                    t_obj, _ = Tema.objects.get_or_create(nombre=asoc['tema'])
                    PreguntaTema.objects.create(
                        pregunta=pregunta,
                        tema=t_obj,
                        relevancia_score=asoc['score'],
                        revisado_por_agente=True
                    )
                contador += 1
            
            # 5. Reporte de Éxito con Icono del Modelo
            icon = "🏎️" if "gemini-3" in modelo_usado else ("🚀" if "2.0" in modelo_usado else "🛡️")
            return f"✅ {icon} Agente finalizó: {contador} preguntas usando {modelo_usado}."

        except Exception as e:
            return f"❌ Error Fatal: {str(e)}"