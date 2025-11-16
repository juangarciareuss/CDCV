import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404
# Importamos los modelos de la nueva estructura robusta
from core.models import Curso, Pregunta, Tema, PreguntaTema 

class Command(BaseCommand):
    help = 'Importa preguntas (y sus relaciones con Temas) desde un archivo JSON estructurado.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', 
            type=str, 
            help='Ruta al archivo JSON que contiene las preguntas.',
            required=True
        )

    @transaction.atomic # Envolvemos toda la operación en una transacción
    def handle(self, *args, **options):
        file_path = options['file']
        
        # --- 1. Validación del Archivo ---
        if not os.path.exists(file_path):
            raise CommandError(f"El archivo no fue encontrado en la ruta: '{file_path}'")
        
        self.stdout.write(self.style.NOTICE(f'Iniciando importación desde: {file_path}'))

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise CommandError("El archivo JSON debe contener una lista (array) de preguntas.")
        except json.JSONDecodeError as e:
            raise CommandError(f"Error: El archivo no tiene un formato JSON válido. {e}")
        except Exception as e:
            raise CommandError(f"Error al leer o parsear el archivo: {e}")
        
        preguntas_creadas = 0
        preguntas_actualizadas = 0
        relaciones_creadas = 0
        
        # --- 2. Procesamiento de Preguntas ---
        for q_data in data:
            
            # Validamos la estructura mínima de la pregunta
            required_fields = ['texto', 'opciones', 'respuesta_correcta', 'dificultad', 'temas']
            if not all(field in q_data for field in required_fields):
                self.stdout.write(self.style.WARNING(f"Advertencia: Pregunta incompleta (falta un campo requerido). Texto: {q_data.get('texto', 'N/A')}. Se omite."))
                continue

            try:
                # Extraemos los datos de los temas (la relación)
                temas_data = q_data.pop('temas')
                
                # Preparamos los datos de la pregunta (el resto de q_data)
                pregunta_defaults = {
                    'opciones': q_data['opciones'],
                    'respuesta_correcta': q_data['respuesta_correcta'],
                    'dificultad': q_data['dificultad'],
                    'idioma': q_data.get('idioma', 'es'),
                    'nivel': q_data.get('dificultad', 1) # Mapeamos dificultad a nivel legacy
                }

                # Creamos o actualizamos la pregunta basándonos en el 'texto'
                pregunta_obj, created = Pregunta.objects.update_or_create(
                    texto=q_data['texto'],
                    defaults=pregunta_defaults
                )
                
                if created:
                    preguntas_creadas += 1
                else:
                    preguntas_actualizadas += 1

                # --- 3. Procesamiento de Relaciones (Modelo Intermediario) ---
                # Aquí es donde tus agentes de IA interactúan
                
                for tema_info in temas_data:
                    tema_id = tema_info.pop('tema_id') # Extraemos el ID del Tema
                    
                    # Verificamos que el Tema (Tag) exista
                    tema_obj = Tema.objects.get(id=tema_id)
                    
                    # 'tema_info' ahora solo contiene {'relevancia_score': ..., 'revisado_por_agente': ...}
                    # Usamos update_or_create para la relación
                    relacion, rel_created = PreguntaTema.objects.update_or_create(
                        pregunta=pregunta_obj,
                        tema=tema_obj,
                        defaults=tema_info # Pasamos el score y el flag de revisión
                    )
                    
                    if rel_created:
                        relaciones_creadas += 1

            except Tema.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Error: El Tema ID {tema_id} no existe. La pregunta '{q_data['texto']}' no se pudo asociar."))
                continue # Continuamos con la siguiente pregunta
            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Error de Integridad (quizás un duplicado?): {e}"))
                continue
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error inesperado procesando pregunta '{q_data['texto']}': {e}"))
                continue

        self.stdout.write(self.style.SUCCESS('--- Importación finalizada ---'))
        self.stdout.write(self.style.SUCCESS(f'Preguntas Creadas: {preguntas_creadas}'))
        self.stdout.write(self.style.SUCCESS(f'Preguntas Actualizadas: {preguntas_actualizadas}'))
        self.stdout.write(self.style.SUCCESS(f'Relaciones Creadas/Actualizadas: {relaciones_creadas}'))