import json
import os
import time
from google import genai
from django.utils.text import slugify
from core.models import Curso, Tema, MicroCompetencia, Pregunta

class BuilderAgent:
    """
    Agente Constructor V5 (Arquitectura Spotify).
    Genera Cursos -> Temas -> MicroCompetencias -> Preguntas.
    """
    def __init__(self):
        # Usamos tu clave de entorno
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        # Mantenemos el modelo flash que te gusta por velocidad/costo
        self.model = "gemini-2.5-flash" 

    def construir_curso(self, nicho_mercado):
        print(f"\n🏗️  [ARQUITECTO] Diseñando Syllabus para: '{nicho_mercado}'...")

        # --- PASO 1: EL ARQUITECTO (Diseño Jerárquico) ---
        prompt_syllabus = f"""
        ACTÚA COMO ARQUITECTO DE CURSOS.
        Diseña un curso completo sobre: '{nicho_mercado}'.
        
        ESTRUCTURA OBLIGATORIA (Modelo Spotify):
        1. Curso: Título y descripción.
        2. Temas (Playlists): Entre 3 y 4 temas grandes.
        3. Micro-Competencias (Átomos): Dentro de cada tema, define 3 habilidades ultra-específicas.
        
        FORMATO JSON EXACTO:
        {{
          "curso": {{
            "nombre": "Título Vendedor",
            "descripcion": "Descripción comercial corta",
            "precio_usd": 5.00
          }},
          "temas": [
            {{
              "nombre": "Nombre del Tema 1",
              "micro_competencias": [
                {{
                  "nombre": "Nombre MicroCompetencia 1.1",
                  "definicion": "Qué sabe hacer exactamente (ej: Usa SUMAR.SI)",
                  "criterio": "Cómo se valida (ej: El resultado es exacto)",
                  "icono": "📊"
                }},
                 {{ "nombre": "...", "definicion": "...", "criterio": "...", "icono": "..." }}
              ]
            }}
          ]
        }}
        """

        try:
            # 1. Generar el Plan Maestro
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt_syllabus,
                config={"response_mime_type": "application/json"}
            )
            plan = json.loads(response.text)
            
            # --- PASO 2: LOS ALBAÑILES (Creación de DB) ---
            print(f"✅ [DISEÑO APROBADO] Creando estructura en base de datos...")
            
            # A. Crear Curso
            curso = Curso.objects.create(
                nombre=plan['curso']['nombre'],
                descripcion=plan['curso']['descripcion'],
                precio_usd=plan['curso'].get('precio_usd', 5.00),
                activo=False
            )
            
            total_preguntas = 0
            
            # B. Iterar sobre Temas
            for t_data in plan['temas']:
                tema_obj, created = Tema.objects.get_or_create(
                    nombre=t_data['nombre']
                )
                # Vincular Tema al Curso (M2M)
                curso.temas.add(tema_obj)
                
                print(f"\n📂 TEMA: {tema_obj.nombre}")
                
                # C. Iterar sobre Micro-Competencias
                for mc_data in t_data['micro_competencias']:
                    mc_obj, created = MicroCompetencia.objects.get_or_create(
                        nombre=mc_data['nombre'],
                        defaults={
                            'definicion_atomica': mc_data['definicion'],
                            'criterio_exito': mc_data['criterio'],
                            'icono': mc_data.get('icono', '🏆')
                        }
                    )
                    # Vincular MC al Tema (M2M)
                    tema_obj.micro_competencias.add(mc_obj)
                    
                    # D. GENERACIÓN DE PREGUNTAS (El Átomo)
                    # Generamos 3 preguntas por competencia para tener variedad
                    print(f"   ⚡ MC: {mc_obj.nombre} -> Generando reactivos...", end="")
                    preguntas_creadas = self._generar_preguntas_atomicas(mc_obj, cantidad=3)
                    
                    if preguntas_creadas:
                        print(f" ✅ ({preguntas_creadas} preguntas)")
                        total_preguntas += preguntas_creadas
                    else:
                        print(f" ❌ Falló generación")
                    
                    time.sleep(1) # Respetar rate limits

            # Finalizar
            curso.cantidad_preguntas = total_preguntas
            curso.activo = True
            curso.save()
            
            print(f"\n🚀 [FIN] Curso '{curso.nombre}' creado con {total_preguntas} preguntas.")
            return f"Curso creado ID: {curso.id}"

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"🔥 Error Fatal: {str(e)}"

    def _generar_preguntas_atomicas(self, mc_obj, cantidad=3):
        """
        Genera preguntas específicas para una MicroCompetencia.
        """
        prompt_preguntas = f"""
        Eres un Experto Evaluador.
        Crea {cantidad} preguntas de selección múltiple PARA VALIDAR ESTA COMPETENCIA:
        
        COMPETENCIA: "{mc_obj.nombre}"
        DEFINICIÓN: "{mc_obj.definicion_atomica}"
        CRITERIO ÉXITO: "{mc_obj.criterio_exito}"
        
        FORMATO JSON (Array de objetos):
        [
          {{
            "texto": "¿Pregunta situacional?",
            "opciones": {{"A": "Mal", "B": "Bien", "C": "Mal", "D": "Mal"}},
            "respuesta_correcta": "B",
            "explicacion": "Por qué B es correcta basada en la definición.",
            "dificultad": 3
          }}
        ]
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt_preguntas,
                config={"response_mime_type": "application/json"}
            )
            preguntas_json = json.loads(response.text)
            
            count = 0
            for p_data in preguntas_json:
                Pregunta.objects.create(
                    micro_competencia=mc_obj, # VINCULACIÓN DIRECTA AL ÁTOMO
                    texto=p_data['texto'],
                    opciones=p_data['opciones'],
                    respuesta_correcta=p_data['respuesta_correcta'],
                    explicacion=p_data['explicacion'],
                    dificultad=p_data.get('dificultad', 3)
                )
                count += 1
            return count
            
        except Exception as e:
            print(f"Error generando preguntas: {e}")
            return 0