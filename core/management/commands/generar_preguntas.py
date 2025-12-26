import os
import json
import time
import re
from dotenv import load_dotenv
from google import genai
from django.core.management.base import BaseCommand
from core.models import MicroCompetencia, Pregunta

class Command(BaseCommand):
    help = 'Generador de Preguntas de Alta Precisión (Uno a Uno con Anti-Crash) V2'

    def handle(self, *args, **kwargs):
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            self.stdout.write(self.style.ERROR("⛔ Error: Falta GEMINI_API_KEY en .env"))
            return

        # USAMOS EL MODELO ESTABLE
        MODELO = 'gemini-3-flash-preview'
        client = genai.Client(api_key=api_key)

        # Buscar competencias vírgenes (sin preguntas)
        competencias = MicroCompetencia.objects.filter(preguntas_banco__isnull=True)
        total = competencias.count()
        
        self.stdout.write(self.style.SUCCESS(f"🎯 OBJETIVO: Generar preguntas para {total} competencias pendientes."))
        self.stdout.write("--------------------------------------------------")

        for i, mc in enumerate(competencias):
            index = i + 1
            curso = mc.cursos.first()
            nombre_curso = curso.nombre if curso else "General"

            self.stdout.write(f"\n🔹 [{index}/{total}] Procesando: {mc.nombre}")
            # self.stdout.write(f"   Contexto: {mc.definicion_atomica}") # Comentado para limpiar consola

            prompt = f"""
            ACTÚA COMO UN EXPERTO EXAMINADOR TÉCNICO.
            
            CONTEXTO: Curso "{nombre_curso}".
            COMPETENCIA: "{mc.nombre}"
            DEFINICIÓN: "{mc.definicion_atomica}"
            CRITERIO: "{mc.criterio_exito}"

            TU MISIÓN:
            Crea 2 preguntas de selección múltiple (Dificultad Media/Alta).
            - Deben evaluar si el usuario REALMENTE sabe hacer lo que dice la competencia.
            - Los distractores deben ser errores comunes, no respuestas absurdas.

            FORMATO DE SALIDA (JSON ARRAY PURO):
            [
              {{
                "texto": "¿Pregunta técnica...?",
                "opciones": {{
                    "A": "Distractor plausible",
                    "B": "Respuesta Correcta",
                    "C": "Error común",
                    "D": "Concepto relacionado pero incorrecto"
                }},
                "respuesta_correcta": "B",
                "explicacion": "Breve justificación técnica."
              }}
            ]
            """

            max_reintentos = 3
            exito = False
            
            for intento in range(max_reintentos):
                try:
                    # CORRECCIÓN AQUÍ: Usamos ending="" en lugar de end="" para Django
                    self.stdout.write(f"   ⏳ Generando... (Intento {intento+1})", ending=" ... ")
                    self.stdout.flush() # Forzamos que se muestre en pantalla
                    
                    response = client.models.generate_content(
                        model=MODELO,
                        contents=prompt,
                        config={'response_mime_type': 'application/json'}
                    )

                    # Limpieza de respuesta
                    if not response.text:
                         raise ValueError("Respuesta vacía de Gemini")

                    texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
                    data = json.loads(texto_limpio)

                    # Guardado en BD
                    for p in data:
                        Pregunta.objects.create(
                            micro_competencia=mc,
                            curso=curso,
                            texto=p['texto'],
                            opciones=p['opciones'],
                            respuesta_correcta=p['respuesta_correcta'],
                            dificultad=3
                        )
                    
                    self.stdout.write(self.style.SUCCESS(f"✅ HECHO"))
                    exito = True
                    
                    # PAUSA INTELIGENTE
                    time.sleep(4) 
                    break 

                except Exception as e:
                    error_msg = str(e)
                    # Si es error de cuota, esperar
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        self.stdout.write(self.style.WARNING(f"\n   ✋ ALTO: Rate Limit detectado."))
                        self.stdout.write("   💤 Esperando 30 segundos...")
                        time.sleep(30)
                    else:
                        # Si es otro error, lo mostramos pero no rompemos el loop inmediatamente
                        self.stdout.write(self.style.ERROR(f"\n   ❌ ERROR: {error_msg}"))
                        time.sleep(1) # Pequeña pausa antes de reintentar
            
            if not exito:
                self.stdout.write(self.style.ERROR(f"   💀 Se omitió {mc.nombre} tras {max_reintentos} fallos."))

        self.stdout.write(self.style.SUCCESS("\n✨ ¡PROCESO COMPLETADO! ✨"))