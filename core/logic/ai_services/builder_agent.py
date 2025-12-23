import json
import os
import time
import math
from google import genai
from dotenv import load_dotenv
from core.models import Curso, Tema
from .refiller_agent import RefillerAgent

load_dotenv()

class BuilderAgent:
    """
    Agente Constructor V4 (Industrial).
    Características:
    - Garantía matemática de 30 preguntas (Corrige a la IA si falla la suma).
    - Seguimiento visual en consola por lotes.
    - Estrategia de Chunking (Lotes de 5) para estabilidad total.
    """
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = "gemini-2.5-flash" 
        self.refiller = RefillerAgent()

    def construir_negocio(self, nicho_mercado):
        print(f"\n🏗️  [INICIO] Diseñando Plan Maestro para: '{nicho_mercado}'")

        # --- PASO 1: EL ARQUITECTO (Diseño) ---
        prompt_arquitecto = f"""
        Eres un Arquitecto de Soluciones Educativas.
        Diseña la estructura de un curso para: '{nicho_mercado}'.
        
        REGLAS OBLIGATORIAS:
        1. Estructura el curso en 3 a 5 Temas.
        2. La suma TOTAL de preguntas de todos los temas debe ser EXACTAMENTE 30.
        3. Define rangos de dificultad (1-5).

        Responde SOLO con este JSON:
        {{
          "nombre_comercial": "Título Vendedor",
          "descripcion_marketing": "Descripción corta",
          "receta": [
            {{
                "tema_nombre": "Tema A", 
                "cantidad": 10, 
                "dificultad_min": 1, 
                "dificultad_max": 3
            }}
          ]
        }}
        """

        try:
            # 1. Generación del Diseño
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt_arquitecto,
                config={"response_mime_type": "application/json", "temperature": 0}
            )
            
            data = json.loads(response.text)
            if not data: return "❌ Error: Diseño vacío."

            # --- VALIDACIÓN MATEMÁTICA (El "Ajuste de Cuentas") ---
            # A veces la IA dice 30 pero pone 10+10+8 = 28. Aquí lo arreglamos.
            suma_ia = sum(item['cantidad'] for item in data['receta'])
            diferencia = 30 - suma_ia
            
            if diferencia != 0:
                print(f"⚠️  [AJUSTE] La IA planeó {suma_ia} preguntas. Ajustando {diferencia} para llegar a 30.")
                # Le sumamos (o restamos) la diferencia al primer tema para cuadrar
                data['receta'][0]['cantidad'] += diferencia

            # 2. Guardar el Cascarón en BD
            curso = Curso.objects.create(
                nombre=data['nombre_comercial'],
                descripcion=data['descripcion_marketing'],
                estructura_examen={"reglas_seleccion": data['receta']},
                activo=False # Se activa solo al terminar
            )
            
            print(f"✅  [DISEÑO APROBADO] Curso: {curso.nombre}. Meta: 30 Preguntas.")

            # --- PASO 2: LA FÁBRICA (Producción con Seguimiento) ---
            total_global = 0
            start_time = time.time()
            
            for index, item in enumerate(data['receta']):
                tema = item['tema_nombre']
                meta_tema = item['cantidad']
                
                # Crear Tema en BD
                Tema.objects.get_or_create(nombre=tema)
                
                print(f"\n   📂  TEMA {index + 1}/{len(data['receta'])}: {tema}")
                print(f"       Meta del Tema: {meta_tema} preguntas")
                print("       " + "-"*30)
                
                # --- BUCLE DE LOTES (Chunking) ---
                generadas_tema = 0
                lote_num = 1
                
                while generadas_tema < meta_tema:
                    # Cálculo del tamaño del lote (Máximo 5 para no saturar)
                    faltan = meta_tema - generadas_tema
                    tamano_lote = 5 if faltan >= 5 else faltan
                    
                    print(f"       ⚙️  [Lote {lote_num}] Generando {tamano_lote} preguntas...", end=" ")
                    
                    # LLAMADA AL OBRERO (Refiller)
                    resultado = self.refiller.poblar_tema(tema, cantidad=tamano_lote)
                    
                    if "✅" in resultado:
                        generadas_tema += tamano_lote
                        total_global += tamano_lote
                        print(f"✅ OK ({generadas_tema}/{meta_tema})")
                    else:
                        print(f"❌ FALLÓ. Reintentando...")
                        # Si falla, no sumamos generadas_tema, así el while lo intenta de nuevo
                        time.sleep(1) # Pausa de castigo
                        continue 
                    
                    lote_num += 1
                    time.sleep(1.5) # Pausa de respiración para Google

            # 3. Finalización
            tiempo_total = round(time.time() - start_time, 2)
            
            if total_global >= 30:
                curso.activo = True
                curso.save()
                mensaje_final = f"🚀 ¡MISIÓN CUMPLIDA! Curso '{curso.nombre}' LISTO.\n" \
                                f"📊 Total Generado: {total_global} preguntas.\n" \
                                f"⏱️ Tiempo: {tiempo_total}s."
                print(f"\n{mensaje_final}\n")
                return mensaje_final
            else:
                return f"⚠️ Curso creado incompleto ({total_global}/30 preguntas)."

        except Exception as e:
            print(f"🔥 ERROR FATAL: {str(e)}")
            return f"❌ Error Crítico: {str(e)}"