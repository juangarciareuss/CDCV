from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Curso, Tema, Pregunta

class Command(BaseCommand):
    help = 'Crea un curso de Seguridad Informática con temas y preguntas de ejemplo.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando la creación de datos de ejemplo...'))

        # --- CREACIÓN DEL CURSO ---
        # Usamos get_or_create para no duplicar el curso si el script se ejecuta de nuevo.
        curso, created = Curso.objects.get_or_create(
            nombre="Seguridad Informática Básica",
            defaults={
                "descripcion": "Aprende los conceptos fundamentales para proteger tu información en el mundo digital."
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Curso "{curso.nombre}" creado.'))
        else:
            self.stdout.write(self.style.WARNING(f'Curso "{curso.nombre}" ya existía. Se intentará añadir contenido nuevo.'))

        # --- CREACIÓN DEL TEMA ---
        tema, tema_created = Tema.objects.get_or_create(
            nombre="Contraseñas Seguras",
            curso=curso
        )

        if not tema_created:
            self.stdout.write(self.style.WARNING(f'Tema "{tema.nombre}" ya existía. No se añadirán nuevas preguntas para este tema para evitar duplicados.'))
            self.stdout.write(self.style.SUCCESS('Proceso finalizado.'))
            return # Salimos si el tema ya existe para no duplicar preguntas

        self.stdout.write(self.style.SUCCESS(f'Tema "{tema.nombre}" creado.'))

        # --- LISTA DE PREGUNTAS ---
        preguntas_data = [
            {
                "texto": "¿Cuál de las siguientes contraseñas es más segura?",
                "opciones": {
                    "a": {"texto": "12345678", "justificacion": "Incorrecto. Es una secuencia numérica muy común y fácil de adivinar."},
                    "b": {"texto": "miperroFirulais", "justificacion": "Incorrecto. Aunque es larga, usa palabras comunes y es predecible."},
                    "c": {"texto": "Tr@v3l!ng#2024", "justificacion": "¡Correcto! Combina mayúsculas, minúsculas, números y símbolos."}
                },
                "respuesta_correcta": "c"
            },
            {
                "texto": "¿Qué es la autenticación de dos factores (2FA)?",
                "opciones": {
                    "a": {"texto": "Usar dos contraseñas diferentes para la misma cuenta.", "justificacion": "Incorrecto. 2FA no se trata de tener dos contraseñas."},
                    "b": {"texto": "Un método de seguridad que requiere dos formas de verificación para acceder.", "justificacion": "¡Correcto! Generalmente es 'algo que sabes' (contraseña) y 'algo que tienes' (tu teléfono)."},
                    "c": {"texto": "Un software que recuerda tus contraseñas por ti.", "justificacion": "Incorrecto. Eso describe un gestor de contraseñas."}
                },
                "respuesta_correcta": "b"
            },
            {
                "texto": "¿Es una buena práctica de seguridad reutilizar la misma contraseña en múltiples sitios web?",
                "opciones": {
                    "a": {"texto": "Sí, porque es más fácil de recordar.", "justificacion": "Incorrecto. Si un sitio es vulnerado, todas tus cuentas están en riesgo."},
                    "b": {"texto": "No, porque si una cuenta es comprometida, todas las demás también lo estarán.", "justificacion": "¡Correcto! Siempre usa contraseñas únicas para cada servicio."},
                    "c": {"texto": "Depende del sitio web.", "justificacion": "Incorrecto. Nunca es una buena práctica."}
                },
                "respuesta_correcta": "b"
            }
        ]

        # --- CREACIÓN DE LAS PREGUNTAS EN LA BASE DE DATOS ---
        num_preguntas_creadas = 0
        for data in preguntas_data:
            Pregunta.objects.create(
                curso=curso,
                tema=tema,
                texto=data["texto"],
                opciones=data["opciones"],
                respuesta_correcta=data["respuesta_correcta"]
            )
            num_preguntas_creadas += 1

        self.stdout.write(self.style.SUCCESS(f'Se crearon {num_preguntas_creadas} preguntas para el tema "{tema.nombre}".'))
        self.stdout.write(self.style.SUCCESS('¡Proceso completado exitosamente!'))
