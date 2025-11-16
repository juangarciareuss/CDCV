import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Curso, Tema

# Este comando se ejecuta con: python manage.py seed_taxonomy
class Command(BaseCommand):
    help = 'Crea la taxonomía inicial de Temas (Tags) y define la "Receta" (estructura_examen) para los cursos base.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando el seeding de la Taxonomía y las Recetas de Examen...'))

        # --- 1. CREACIÓN DE LA TAXONOMÍA DE EXCEL ---
        
        # 1.1. Tema Padre
        tema_padre_excel, created = Tema.objects.get_or_create(
            nombre="Análisis de Datos (Excel)",
            defaults={'descripcion': 'Categoría principal para todo el conocimiento relacionado con Excel.'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Tema Padre Creado: {tema_padre_excel.nombre}'))

        # 1.2. Sub-Temas (Tags Reutilizables)
        subtemas_excel = [
            "Funciones Básicas y Lógica",
            "Búsqueda y Referencia",
            "Tablas Dinámicas",
            "Funciones Avanzadas y Condicionales",
            "Análisis y Escenarios",
            "Funciones de Texto y Fecha",
            "Arrays Dinámicos",
            "Power Query (M)",
            "Visualización",
            "Auditoría y Seguridad"
        ]
        
        temas_creados_excel = 0
        for subtema_nombre in subtemas_excel:
            subtema, created = Tema.objects.get_or_create(
                nombre=subtema_nombre,
                defaults={'parent': tema_padre_excel}
            )
            if created:
                temas_creados_excel += 1
        
        self.stdout.write(self.style.SUCCESS(f'Se crearon {temas_creados_excel} nuevos Sub-Temas (Tags) para Excel.'))

        # --- 2. DEFINICIÓN DE LA "RECETA" DEL CURSO DE EXCEL ---
        
        # 2.1. Definimos la Receta para el Nivel Profesional (CDCV-P)
        # MODIFICAMOS: La receta para que coincida con la dificultad real de las preguntas
        receta_excel_pro = {
            "total_preguntas": 10,
            "reglas_seleccion": [
                # CORREGIDO: Nivel 2 (Búsqueda) tiene Dificultad 1.
                {
                    "tema_nombre": "Búsqueda y Referencia", 
                    "dificultad_min": 1, # Antes 2
                    "dificultad_max": 2, # Antes 3
                    "cantidad": 2
                },
                # CORREGIDO: Nivel 3 (Tablas Dinámicas) tiene Dificultad 2.
                {
                    "tema_nombre": "Tablas Dinámicas", 
                    "dificultad_min": 2, 
                    "dificultad_max": 3, # Antes 4
                    "cantidad": 3
                },
                # Nivel 5 (Análisis) tiene Dificultad 3. (Sin cambios)
                {
                    "tema_nombre": "Análisis y Escenarios", 
                    "dificultad_min": 3, 
                    "dificultad_max": 5, 
                    "cantidad": 3
                },
                # Nivel 8 (Power Query) tiene Dificultad 4. (Sin cambios)
                {
                    "tema_nombre": "Power Query (M)", 
                    "dificultad_min": 4, 
                    "dificultad_max": 5, 
                    "cantidad": 2 
                }
            ]
        }
        
        curso_excel, created = Curso.objects.update_or_create(
            nombre="Excel para Analistas (CDCV-P)", 
            defaults={
                'tema': tema_padre_excel,
                'nivel': 2,
                'descripcion': 'Curso completo de Excel para análisis de datos.',
                'idioma': 'es',
                'estructura_examen': receta_excel_pro 
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Curso Creado: {curso_excel.nombre} (Nivel {curso_excel.nivel})'))
        else:
            self.stdout.write(self.style.WARNING(f'Curso Actualizado: {curso_excel.nombre} (Receta aplicada)'))

        
        # --- 3. (NUEVO) CREACIÓN DE LA TAXONOMÍA DE IA ---

        # 3.1. Tema Padre
        tema_padre_ia, created = Tema.objects.get_or_create(
            nombre="Inteligencia Artificial",
            defaults={'descripcion': 'Categoría principal para prompts y modelos de IA.'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Tema Padre Creado: {tema_padre_ia.nombre}'))

        # 3.2. Sub-Temas (Tags Reutilizables)
        subtemas_ia = [
            "Conceptos Básicos de Prompts",
            "Zero-shot / Few-shot",
            "Chain-of-Thought (CoT)",
            "Roles y Formatos"
        ]
        
        temas_creados_ia = 0
        for subtema_nombre in subtemas_ia:
            subtema, created = Tema.objects.get_or_create(
                nombre=subtema_nombre,
                defaults={'parent': tema_padre_ia}
            )
            if created:
                temas_creados_ia += 1
        
        self.stdout.write(self.style.SUCCESS(f'Se crearon {temas_creados_ia} nuevos Sub-Temas (Tags) para IA.'))

        # --- 4. (NUEVO) DEFINICIÓN DE LA "RECETA" DEL CURSO DE IA ---

        receta_ia_associate = {
            "total_preguntas": 10,
            "reglas_seleccion": [
                # 4 preguntas de conceptos básicos (Dificultad 1-2)
                {
                    "tema_nombre": "Conceptos Básicos de Prompts", 
                    "dificultad_min": 1, 
                    "dificultad_max": 2, 
                    "cantidad": 4
                },
                # 3 preguntas de técnicas (Dificultad 1-3)
                {
                    "tema_nombre": "Zero-shot / Few-shot", 
                    "dificultad_min": 1, 
                    "dificultad_max": 3, 
                    "cantidad": 3
                },
                # 3 preguntas de roles (Dificultad 1-3)
                {
                    "tema_nombre": "Roles y Formatos", 
                    "dificultad_min": 1, 
                    "dificultad_max": 3, 
                    "cantidad": 3
                }
            ]
        }

        curso_ia, created = Curso.objects.update_or_create(
            nombre="Fundamentos de Prompts de IA (CDCV-A)", 
            defaults={
                'tema': tema_padre_ia,
                'nivel': 1,
                'descripcion': 'Conceptos básicos para crear prompts efectivos y comunicarse con modelos de lenguaje.',
                'idioma': 'es',
                'estructura_examen': receta_ia_associate # Asignamos la receta de IA
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Curso Creado: {curso_ia.nombre} (Nivel {curso_ia.nivel})'))
        else:
            self.stdout.write(self.style.WARNING(f'Curso Actualizado: {curso_ia.nombre} (Receta aplicada)'))

        self.stdout.write(self.style.SUCCESS('--- Seeding de Taxonomía y Recetas completado ---'))


        # --- 5. (NUEVO) CREACIÓN DE LA TAXONOMÍA DE PYTHON ---

        tema_padre_python, created = Tema.objects.get_or_create(
            nombre="Desarrollo con Python",
            defaults={'descripcion': 'Categoría principal para todo el conocimiento relacionado con Python.'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Tema Padre Creado: {tema_padre_python.nombre}'))

        # Definimos los Tags (Subtemas) para el curso básico
        subtemas_python = [
            "Sintaxis Básica (Python)",
            "Estructuras de Datos (Python)",
            "Funciones (Python)",
            "Conceptos Clave (Python)"
        ]
        
        temas_creados_python = 0
        for subtema_nombre in subtemas_python:
            subtema, created = Tema.objects.get_or_create(
                nombre=subtema_nombre,
                defaults={'parent': tema_padre_python}
            )
            if created:
                temas_creados_python += 1
        
        self.stdout.write(self.style.SUCCESS(f'Se crearon {temas_creados_python} nuevos Sub-Temas (Tags) para Python.'))

        # --- 6. (NUEVO) DEFINICIÓN DE LA "RECETA" DEL CURSO DE PYTHON ---

        receta_python_associate = {
            "total_preguntas": 10,
            "reglas_seleccion": [
                # 3 preguntas de Sintaxis (Dificultad 1-2)
                {
                    "tema_nombre": "Sintaxis Básica (Python)", 
                    "dificultad_min": 1, 
                    "dificultad_max": 2, 
                    "cantidad": 3
                },
                # 3 preguntas de Estructuras (Dificultad 1-3)
                {
                    "tema_nombre": "Estructuras de Datos (Python)", 
                    "dificultad_min": 1, 
                    "dificultad_max": 3, 
                    "cantidad": 3
                },
                # 4 preguntas de Funciones/Conceptos (Dificultad 2-3)
                {
                    "tema_nombre": "Funciones (Python)", 
                    "dificultad_min": 2, 
                    "dificultad_max": 3, 
                    "cantidad": 2
                },
                {
                    "tema_nombre": "Conceptos Clave (Python)", 
                    "dificultad_min": 2, 
                    "dificultad_max": 3, 
                    "cantidad": 2
                }
            ]
        }

        curso_python, created = Curso.objects.update_or_create(
            nombre="Python Básico (CDCV-A)", 
            defaults={
                'tema': tema_padre_python,
                'nivel': 1,
                'descripcion': 'Validación de los fundamentos de Python (Sintaxis, Estructuras y Funciones).',
                'idioma': 'es',
                'estructura_examen': receta_python_associate # Asignamos la receta de Python
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Curso Creado: {curso_python.nombre} (Nivel {curso_python.nivel})'))
        else:
            self.stdout.write(self.style.WARNING(f'Curso Actualizado: {curso_python.nombre} (Receta aplicada)'))


        self.stdout.write(self.style.SUCCESS('--- Seeding de Taxonomía y Recetas completado ---'))