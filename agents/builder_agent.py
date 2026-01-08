import json
import os
import time
from google import genai
from django.utils.text import slugify
# AGREGAMOS CursoMicroCompetencia a los imports
from core.models import Curso, Tema, MicroCompetencia, Pregunta, CursoMicroCompetencia
from .prompts import prompt_plan_maestro, prompt_generacion_reactivos

class BuilderAgent:
    """
    AGENTE ARQUITECTO (Creador de Cursos)
    Misión: Bootstrapping. Crea un curso desde cero, define su estructura
    y genera el contenido semilla inicial.
    """
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = "gemini-2.5-flash"

    def construir_curso(self, nicho_mercado, nivel_dificultad=3): 
        print(f"\n🏗️  [BUILDER] Diseñando Arquitectura Nivel {nivel_dificultad} para: '{nicho_mercado}'...")

        # 1. Generar el Plan Maestro (Estructura)
        raw_prompt = prompt_plan_maestro(nicho_mercado, nivel=nivel_dificultad)
        plan = self._llamar_gemini_json(raw_prompt)
        
        # Validación de seguridad: Si falla el JSON, cortamos aquí
        if not plan: 
            print("❌ Error: La IA no devolvió un plan válido.")
            return None
            
        if 'temas' not in plan:
            print("❌ Error: El JSON no contiene la clave 'temas'.")
            return None

        # 2. Materializar Curso en BD
        curso = Curso.objects.create(
            nombre=plan['curso']['nombre'],
            descripcion=plan['curso']['descripcion'],
            precio_usd=plan['curso'].get('precio_usd', 9.99),
            nivel=nivel_dificultad,
            activo=False # Nace inactivo hasta revisión
        )
        
        total_preguntas = 0
        reglas_seleccion = []
        orden_global = 1 # 🆕 Variable para controlar el orden de la playlist

     # 3. Iterar Módulos
        for t_data in plan['temas']:
            # -------------------------------------------------------
            # 🧠 LÓGICA DE PARSEO "AMAZON TAXONOMY"
            # Separamos "CATEGORÍA: Subtema" para el Gimnasio
            # -------------------------------------------------------
            nombre_completo = t_data.get('nombre', 'General: General')
            
            if ":" in nombre_completo:
                # Si cumple el formato "Excel: Tablas", separamos
                partes = nombre_completo.split(":")
                nombre_tema_maestro = partes[0].strip() # "Excel" (Para el Gym)
                contexto_subtema = partes[1].strip()    # "Tablas" (Para contexto)
            else:
                # Fallback si la IA olvida los dos puntos
                nombre_tema_maestro = nombre_completo.strip()
                contexto_subtema = nombre_completo.strip()

            print(f"   -> Procesando Área: {nombre_tema_maestro} | Contexto: {contexto_subtema}")

            tema_slug = slugify(nombre_tema_maestro)
            
            # Buscamos o creamos el TEMA MAESTRO (Ej: solo "Excel")
            tema_obj, _ = Tema.objects.get_or_create(
                nombre=nombre_tema_maestro, 
                defaults={'slug': tema_slug}
            )
            curso.temas.add(tema_obj)
            
            preguntas_tema_count = 0
            
            for mc_data in t_data.get('micro_competencias', []):
                # Crear MicroCompetencia
                mc_obj, _ = MicroCompetencia.objects.get_or_create(
                    nombre=mc_data['nombre'],
                    defaults={
                        'definicion_atomica': mc_data.get('definicion', ''),
                        'criterio_exito': mc_data.get('criterio', ''),
                        'icono': "🔹"
                    }
                )
                
                # Conexión Jerárquica: Tema <-> MicroCompetencia
                mc_obj.temas.add(tema_obj) 
                
                # 🚨 CAMBIO CRÍTICO AQUÍ 🚨
                # Vinculamos la competencia al CURSO explícitamente y con ORDEN
                CursoMicroCompetencia.objects.get_or_create(
                    curso=curso,
                    competencia=mc_obj,
                    defaults={'orden': orden_global}
                )
                orden_global += 1
                
                # Generar Reactivos (Preguntas)
                # Mantenemos tu lógica de generar algunas preguntas iniciales aquí
                creadas = self._generar_preguntas(mc_obj, nivel_dificultad)
                preguntas_tema_count += creadas
                
                # Rate limit suave para no saturar
                time.sleep(0.5) 

            total_preguntas += preguntas_tema_count
            
            # Regla de examen para este tema (Conservamos tu lógica intacta)
            reglas_seleccion.append({
                "tema_nombre": tema_obj.nombre,
                "cantidad": max(1, int(preguntas_tema_count * 0.5)), 
                "dificultad_objetivo": nivel_dificultad
            })

        # 4. Finalizar Configuración
        curso.cantidad_preguntas = total_preguntas
        curso.estructura_examen = {
            "reglas_seleccion": reglas_seleccion,
            "nota_aprobacion": 70,
            "nivel_tecnico": nivel_dificultad
        }
        curso.activo = True
        curso.save()
        
        print(f"✅ [BUILDER] Curso '{curso.nombre}' finalizado con {orden_global-1} competencias.")
        return curso

    def _generar_preguntas(self, mc_obj, nivel):
        try:
            prompt = prompt_generacion_reactivos(mc_obj, nivel)
            preguntas_data = self._llamar_gemini_json(prompt)
            
            if not preguntas_data: return 0
            
            count = 0
            for p_data in preguntas_data:
                Pregunta.objects.create(
                    micro_competencia=mc_obj,
                    texto=p_data['texto'],
                    opciones=p_data['opciones'],
                    respuesta_correcta=p_data['respuesta_correcta'],
                    justificacion=p_data.get('justificacion', 'Generada por IA'),
                    dificultad=nivel,
                    verificado=False # Por defecto requiere revisión
                )
                count += 1
            return count
        except Exception as e:
            print(f"⚠️ Error generando preguntas para {mc_obj.nombre}: {e}")
            return 0

    def _llamar_gemini_json(self, prompt):
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"❌ Error API Gemini: {e}")
            return None