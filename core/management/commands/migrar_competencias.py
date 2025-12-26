import os
from google import genai  # <--- Tu import moderno correcto
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Curso, MicroCompetencia, CursoMicroCompetencia

class Command(BaseCommand):
    help = 'Usa Gemini (SDK Moderno) para transformar Cursos antiguos en Micro-Competencias'

    def handle(self, *args, **kwargs):
        cursos = Curso.objects.all()
        
        if not cursos.exists():
            self.stdout.write(self.style.WARNING("No hay cursos para migrar."))
            return

        # 1. Instanciamos el CLIENTE (Así funciona la nueva librería)
        # Asegúrate de que settings.GEMINI_API_KEY tenga tu clave
        client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

        self.stdout.write(f"Encontrados {cursos.count()} cursos. Iniciando Agente con SDK Moderno...")

        for curso in cursos:
            self.stdout.write(f"Procesando: {curso.nombre}...")
            
            prompt = f"""
            Actúa como un Arquitecto de Educación Experto. Analiza este curso:
            TÍTULO: {curso.nombre}
            DESCRIPCIÓN: {curso.descripcion}
            
            TU TAREA:
            Desglosa este curso en 5 a 10 "Micro-Competencias" atómicas.
            
            FORMATO DE SALIDA (Estricto):
            Debes responder SOLO con líneas separadas por pipes (|) en este formato exacto:
            Nombre Técnico Corto | Descripción Humana | Criterio de Éxito Binario
            
            EJEMPLO:
            excel_suma_simple | Sumar celdas contiguas | El usuario usa la función SUMA correctamente en un rango.
            excel_formato_fecha | Aplicar formato fecha | El usuario cambia la celda de General a Fecha Corta.
            
            Genera las competencias ahora:
            """

            try:
                # 2. Llamada con la sintaxis NUEVA (client.models.generate_content)
                # Nota: Si 'gemini-2.5-flash' te da error de "no encontrado", prueba 'gemini-2.0-flash-exp' o 'gemini-1.5-flash'
                response = client.models.generate_content(
                    model='gemini-2.5-flash', # Ajusta a tu versión exacta si tienes acceso a la 2.5
                    contents=prompt
                )
                
                # En la nueva SDK, el texto suele estar en response.text directamente
                if not response.text:
                    self.stdout.write(self.style.WARNING(f"   -> Gemini no devolvió texto para {curso.nombre}"))
                    continue

                lines = response.text.strip().split('\n')
                orden_contador = 1

                for line in lines:
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            nombre = parts[0].strip()
                            desc = parts[1].strip()
                            criterio = parts[2].strip()

                            mc, created = MicroCompetencia.objects.get_or_create(
                                nombre=nombre,
                                defaults={
                                    'definicion_atomica': desc,
                                    'criterio_exito': criterio,
                                    'prompt_validacion': f"Valida si el usuario cumple: {criterio}"
                                }
                            )

                            CursoMicroCompetencia.objects.get_or_create(
                                curso=curso,
                                competencia=mc,
                                defaults={'orden': orden_contador}
                            )
                            
                            estado = "CREADA" if created else "VINCULADA"
                            self.stdout.write(f"   -> {estado}: {nombre}")
                            orden_contador += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error procesando {curso.nombre}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS("¡Migración Inteligente completada!"))