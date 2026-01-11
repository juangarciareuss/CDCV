import json  # <--- 1. AGREGADO: Faltaba esta librería esencial
import os
import time
import re
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
            partes = nicho_mercado.split(":")
            tema_principal = partes[0].strip().title()
            sub_tema = partes[1].strip().title()
            nombre_estandar = f"{tema_principal}: {sub_tema}"
        else:
            sufijo = niveles_map.get(nivel_dificultad, "Especializado")
            nombre_estandar = f"{nicho_mercado.title()} {sufijo}"
        
        # 2. Materializar Curso en BD
        curso = Curso.objects.create(
            nombre=nombre_estandar,
            descripcion=plan['curso']['descripcion'],
            precio_usd=plan['curso'].get('precio_usd', 9.99),
            nivel=nivel_dificultad,
            activo=False
        )
        
        total_preguntas = 0
        reglas_seleccion = []
        orden_global = 1 

       # 3. Iterar Módulos
        for t_data in plan['temas']:
            
            # --- AUTO-CORRECCIÓN DE TAXONOMÍA ---
            nombre_tema_raw = t_data.get('nombre', 'General')
            if ":" not in nombre_tema_raw:
                herramienta_base = nicho_mercado.split(":")[0].strip().title()
                nombre_tema_final = f"{herramienta_base}: {nombre_tema_raw.strip()}"
            else:
                nombre_tema_final = nombre_tema_raw.strip()

            print(f"   -> Tema procesado: {nombre_tema_final}")

            # Buscamos o creamos el TEMA MAESTRO
            tema_slug = slugify(nombre_tema_final)
            tema_obj, _ = Tema.objects.get_or_create(
                nombre=nombre_tema_final, 
                defaults={'slug': tema_slug}
            )
            curso.temas.add(tema_obj)
            
            # Bucle de Micro-Competencias
            for mc_data in t_data.get('micro_competencias', []):
                slug_intencional = mc_data.get('slug_seo', mc_data['nombre'])
                slug_final = slugify(slug_intencional)

                # Crear MicroCompetencia
                mc_obj, _ = MicroCompetencia.objects.get_or_create(
                    nombre=mc_data['nombre'],
                    defaults={
                        'slug': slug_final,
                        'definicion_atomica': mc_data.get('definicion', ''),
                        'criterio_exito': mc_data.get('criterio', ''),
                        'icono': "🔹"
                    }
                )
                
                # Conexiones
                mc_obj.temas.add(tema_obj) 
                CursoMicroCompetencia.objects.get_or_create(
                    curso=curso,
                    competencia=mc_obj,
                    defaults={'orden': orden_global}
                )
                orden_global += 1
                
                # Generar Reactivos (Aquí se crean en BD)
                self._generar_preguntas(mc_obj, nivel_dificultad)
                time.sleep(0.5)

            # ------------------------------------------------------------------
            # 🛡️ FIX DE INGENIERÍA: AUDITORÍA REAL DE LA BASE DE DATOS
            # ------------------------------------------------------------------
            # En lugar de sumar variables en memoria, contamos cuántas preguntas 
            # REALMENTE quedaron guardadas y verificadas en la BD para este tema.
            
            cant_real_bd = Pregunta.objects.filter(
                micro_competencia__temas=tema_obj,
                micro_competencia__cursomicrocompetencia__curso=curso,
                verificado=True
            ).count()

            print(f"      📊 Auditoría Tema '{tema_obj.nombre}': {cant_real_bd} preguntas verificadas.")

            if cant_real_bd > 0:
                # Solo agregamos la regla si hay stock real
                reglas_seleccion.append({
                    "tema_nombre": tema_obj.nombre,
                    "cantidad": max(1, int(cant_real_bd * 0.5)), # Regla del 50%
                    "dificultad_objetivo": nivel_dificultad
                })
                total_preguntas += cant_real_bd
            else:
                print(f"      ⚠️ ALERTA: Tema '{tema_obj.nombre}' vacío. Omitiendo regla.")
            # ------------------------------------------------------------------

        # 4. Finalizar Configuración
        curso.cantidad_preguntas = total_preguntas
        curso.estructura_examen = {
            "reglas_seleccion": reglas_seleccion,
            "nota_aprobacion": 70,
            "nivel_tecnico": nivel_dificultad
        }
        curso.activo = True
        curso.save()
        
        print(f"✅ [BUILDER] Curso '{curso.nombre}' finalizado con {orden_global-1} competencias y {total_preguntas} preguntas.")
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
                    verificado=True # <--- IMPORTANTE: Nacen listas para usar
                )
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
                    "temperature": 0.2
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
            print(f"🔴 JSON ROTO: {e}") 
            print(f"   CONTENIDO RECIBIDO: {texto_raw[:100]}...") 
            return None