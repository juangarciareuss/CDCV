import json
import os
import time
import re # Agregamos re para limpieza extra si hace falta
from google import genai
from django.utils.text import slugify
from core.models import Curso, Tema, MicroCompetencia, Pregunta, CursoMicroCompetencia
from .prompts import prompt_arquitectura_curso, prompt_generacion_reactivos

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

        # 1. Generar el Plan Maestro (Estructura curso)
        raw_prompt = prompt_arquitectura_curso(nicho_mercado, nivel=nivel_dificultad)
        plan = self._llamar_gemini_json(raw_prompt)
        
        # Validación de seguridad
        if not plan: 
            print("❌ Error: La IA no devolvió un plan válido.")
            return None
            
        if 'temas' not in plan:
            print("❌ Error: El JSON no contiene la clave 'temas'.")
            return None

        # -------------------------------------------------------
        # 🧠 NUEVA LÓGICA DE NOMENCLATURA HÍBRIDA (B2B STANDARD)
        # -------------------------------------------------------
        niveles_map = {
            1: "Principiante",
            2: "Básico",
            3: "Intermedio",
            4: "Avanzado",
            5: "Experto"
        }

        # Detectamos si es una Especialización (Tiene ":") o General
        if ":" in nicho_mercado:
            # FORMATO B: Especialización (Ej: "Excel: Tablas Dinámicas")
            # Regla: Se conserva el subtema, SE OMITE la palabra del nivel.
            partes = nicho_mercado.split(":")
            tema_principal = partes[0].strip().title() # "Excel"
            sub_tema = partes[1].strip().title()       # "Tablas Dinámicas"
            nombre_estandar = f"{tema_principal}: {sub_tema}"
        else:
            # FORMATO A: General (Ej: "Excel Intermedio")
            # Regla: Se agrega el sufijo del nivel estandarizado.
            sufijo = niveles_map.get(nivel_dificultad, "Especializado")
            nombre_estandar = f"{nicho_mercado.title()} {sufijo}"
        
        # -------------------------------------------------------

        # 2. Materializar Curso en BD
        curso = Curso.objects.create(
            nombre=nombre_estandar,  # <--- Nombre limpio aplicado
            descripcion=plan['curso']['descripcion'],
            precio_usd=plan['curso'].get('precio_usd', 9.99),
            nivel=nivel_dificultad,
            activo=False # Nace inactivo hasta revisión
        )
        
        total_preguntas = 0
        reglas_seleccion = []
        orden_global = 1 

       # 3. Iterar Módulos
        for t_data in plan['temas']:
            
            # --- AUTO-CORRECCIÓN DE TAXONOMÍA ---
            nombre_tema_raw = t_data.get('nombre', 'General')
            
            # Si la IA olvidó poner "Python: Variables", nosotros lo forzamos usando el nicho.
            if ":" not in nombre_tema_raw:
                # Recuperamos la herramienta del nombre del curso (Ej: "Excel")
                herramienta_base = nicho_mercado.split(":")[0].strip().title()
                nombre_tema_final = f"{herramienta_base}: {nombre_tema_raw.strip()}"
            else:
                nombre_tema_final = nombre_tema_raw.strip()

            print(f"   -> Tema procesado: {nombre_tema_final}")

            # Buscamos o creamos el TEMA MAESTRO con slug simple
            tema_slug = slugify(nombre_tema_final)
            tema_obj, _ = Tema.objects.get_or_create(
                nombre=nombre_tema_final, 
                defaults={'slug': tema_slug}
            )
            curso.temas.add(tema_obj)
            
            preguntas_tema_count = 0
            
            for mc_data in t_data.get('micro_competencias', []):
                
                # --- AQUÍ CAPTURAMOS EL SLUG SEO ---
                # 1. Intentamos leer 'slug_seo' del JSON.
                # 2. Si no viene, usamos el nombre normal como plan B.
                slug_intencional = mc_data.get('slug_seo', mc_data['nombre'])
                
                # 3. Limpiamos para asegurar que sea URL válida (minúsculas, guiones)
                slug_final = slugify(slug_intencional)

                # Crear MicroCompetencia
                mc_obj, _ = MicroCompetencia.objects.get_or_create(
                    nombre=mc_data['nombre'],
                    defaults={
                        'slug': slug_final, # <--- ¡ESTO FALTABA! Antes no se guardaba.
                        'definicion_atomica': mc_data.get('definicion', ''),
                        'criterio_exito': mc_data.get('criterio', ''),
                        'icono': "🔹"
                    }
                )
                
                # Conexión Jerárquica
                mc_obj.temas.add(tema_obj) 
                
                # Vinculación al CURSO con ORDEN
                CursoMicroCompetencia.objects.get_or_create(
                    curso=curso,
                    competencia=mc_obj,
                    defaults={'orden': orden_global}
                )
                orden_global += 1
                
                # Generar Reactivos
                creadas = self._generar_preguntas(mc_obj, nivel_dificultad)
                preguntas_tema_count += creadas
                
                time.sleep(0.5)

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
            
            if not preguntas_data: 
                print(f"⚠️ Alerta: IA devolvió vacío para '{mc_obj.nombre}'")
                return 0
            
            count = 0
            for p_data in preguntas_data:
                Pregunta.objects.create(
                    micro_competencia=mc_obj,
                    texto=p_data['texto'],
                    opciones=p_data['opciones'],
                    respuesta_correcta=p_data['respuesta_correcta'],
                    justificacion=p_data.get('justificacion', 'Generada por IA'),
                    dificultad=nivel,
                    verificado=False 
                )
                # ✅ Confirmación visual
                print(f"   [+] Pregunta creada: {p_data['texto'][:40]}...")
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
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2 # <--- CAMBIO CRÍTICO: Hace a la IA más obediente con el JSON
                }
            )
            return self._limpiar_json(response.text)
        except Exception as e:
            print(f"❌ Error API Gemini: {e}")
            return None
        
    def _limpiar_json(self, texto_raw):
        """Limpia bloques markdown json y MUESTRA EL ERROR si falla"""
        if not texto_raw: return None
        texto_limpio = re.sub(r'^```json\s*', '', texto_raw, flags=re.MULTILINE)
        texto_limpio = re.sub(r'\s*```$', '', texto_limpio, flags=re.MULTILINE)
        try:
            return json.loads(texto_limpio)
        except json.JSONDecodeError as e:
            # 🔴 AQUÍ ESTÁ EL CAMBIO: Imprimimos el error para que lo veas
            print(f"🔴 JSON ROTO: {e}") 
            print(f"   CONTENIDO RECIBIDO: {texto_raw[:100]}...") 
            return None
        
