# core/agents/builder_agent.py
import json
import os
import time
from google import genai
from django.utils.text import slugify
from core.models import Curso, Tema, MicroCompetencia, Pregunta

# --- CAMBIO CLAVE: Importación relativa desde la misma carpeta ---
from .prompts import prompt_plan_maestro, prompt_generacion_reactivos

class BuilderAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = "gemini-2.5-flash" 

    # --- CAMBIO CLAVE: Aceptamos nivel_dificultad ---
    def construir_curso(self, nicho_mercado, nivel_dificultad): 
        
        print(f"\n🏗️  [ARQUITECTO] Diseñando Nivel {nivel_dificultad} para: '{nicho_mercado}'...")

        # 1. Plan Maestro (Pasamos el nivel obligatorio)
        raw_prompt = prompt_plan_maestro(nicho_mercado, nivel=nivel_dificultad)
        
        plan = self._llamar_gemini_json(raw_prompt)
        
        if not plan: return None

        # 2. Crear Curso
        curso = Curso.objects.create(
            nombre=plan['curso']['nombre'],
            descripcion=plan['curso']['descripcion'],
            precio_usd=plan['curso'].get('precio_usd', 5.00),
            nivel=nivel_dificultad,  # Guardamos el nivel
            activo=False
        )
        
        total_preguntas = 0
        reglas_seleccion = []

        for t_data in plan['temas']:
            tema_slug = slugify(t_data['nombre']) or f"tema-{int(time.time())}"
            tema_obj, _ = Tema.objects.get_or_create(
                nombre=t_data['nombre'], defaults={'slug': tema_slug}
            )
            curso.temas.add(tema_obj)
            
            preguntas_tema = 0
            for mc_data in t_data['micro_competencias']:
                mc_obj, _ = MicroCompetencia.objects.get_or_create(
                    nombre=mc_data['nombre'],
                    defaults={
                        'definicion_atomica': mc_data['definicion'],
                        'criterio_exito': mc_data['criterio'],
                        'icono': "🔧"
                    }
                )
                tema_obj.micro_competencias.add(mc_obj)
                
                # Pasamos el nivel a la generación de preguntas
                creadas = self._generar_preguntas(mc_obj, tema_obj, nivel_dificultad)
                if creadas:
                    total_preguntas += creadas
                    preguntas_tema += creadas
                time.sleep(0.5)

            reglas_seleccion.append({
                "tema_nombre": tema_obj.nombre,
                "cantidad": max(1, int(preguntas_tema * 0.6)),
                "dificultad_min": nivel_dificultad, # Candado de nivel
                "dificultad_max": nivel_dificultad
            })

        curso.cantidad_preguntas = total_preguntas
        curso.estructura_examen = {
            "reglas_seleccion": reglas_seleccion,
            "nota_aprobacion": 70,
            "nivel_tecnico": nivel_dificultad
        }
        curso.activo = True
        curso.save()
        
        return curso

    def _generar_preguntas(self, mc_obj, tema_obj, nivel):
        # Usamos el prompt importado con el nivel correcto
        prompt = prompt_generacion_reactivos(mc_obj, nivel)
        preguntas_data = self._llamar_gemini_json(prompt)
        
        if not preguntas_data: return 0
        
        count = 0
        for p_data in preguntas_data:
            p = Pregunta.objects.create(
                micro_competencia=mc_obj,
                texto=p_data['texto'],
                opciones=p_data['opciones'],
                respuesta_correcta=p_data['respuesta_correcta'],
                justificacion=p_data.get('justificacion', 'IA'),
                dificultad=nivel
            )
            p.temas.add(tema_obj)
            count += 1
        return count

    def _llamar_gemini_json(self, prompt):
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except:
            return None