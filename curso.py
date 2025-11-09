from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Usuario, Tema, Curso, Pregunta

# Este script se ejecuta con: python manage.py seed_db

class Command(BaseCommand):
    help = 'Puebla la base de datos con un curso de prueba y 10 preguntas.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Iniciando el poblamiento de la base de datos...'))

        # --- 1. Crear Tema ---
        tema, created = Tema.objects.get_or_create(
            nombre="Pruebas de Python",
            defaults={'descripcion': 'Tema para el curso de prueba de Python Básico.'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Tema creado: {tema.nombre}'))
        else:
            self.stdout.write(self.style.WARNING(f'Tema ya existía: {tema.nombre}'))

        # --- 2. Crear Curso ---
        curso, created = Curso.objects.get_or_create(
            nombre="Python Básico CDCV-A",
            tema=tema,
            defaults={
                'nivel': 1,
                'descripcion': 'Curso de prueba para validar el flujo completo de certificación.',
                'idioma': 'es'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Curso creado: {curso.nombre}'))
        else:
            self.stdout.write(self.style.WARNING(f'Curso ya existía: {curso.nombre}'))

        # --- 3. Limpiar preguntas antiguas de este curso (opcional) ---
        Pregunta.objects.filter(curso=curso).delete()
        self.stdout.write(self.style.NOTICE(f'Preguntas antiguas del curso "{curso.nombre}" eliminadas.'))

        # --- 4. Crear las 10 Preguntas ---
        preguntas_data = [
            {
                "texto": "¿Cuál es el resultado de 'print(1 + \"1\")'?",
                "opciones": {
                    "A": {"texto": "2", "justificacion": "Incorrecto, no se pueden sumar un entero y una cadena de esta forma."},
                    "B": {"texto": "11", "justificacion": "Incorrecto, ese sería el resultado de '\"1\" + \"1\"'."},
                    "C": {"texto": "TypeError", "justificacion": "Correcto, Python no puede sumar (add) un 'int' y un 'str'."}
                },
                "respuesta_correcta": "C"
            },
            {
                "texto": "¿Qué función se usa para obtener la longitud de una lista o cadena?",
                "opciones": {
                    "A": {"texto": "count()", "justificacion": "Incorrecto, count() se usa para contar ocurrencias de un elemento."},
                    "B": {"texto": "len()", "justificacion": "Correcto, len() (length) devuelve el número de elementos."},
                    "C": {"texto": "size()", "justificacion": "Incorrecto, size() es común en otras librerías (Pandas) pero no en Python base para esto."}
                },
                "respuesta_correcta": "B"
            },
            {
                "texto": "¿Cuál es el tipo de dato de 'True'?",
                "opciones": {
                    "A": {"texto": "bool", "justificacion": "Correcto, 'True' y 'False' son de tipo booleano."},
                    "B": {"texto": "str", "justificacion": "Incorrecto, 'True' no es una cadena de texto."},
                    "C": {"texto": "int", "justificacion": "Incorrecto, aunque True equivale a 1, su tipo es 'bool'."}
                },
                "respuesta_correcta": "A"
            },
            {
                "texto": "Dada la lista 'mi_lista = [10, 20, 30]', ¿qué devuelve 'mi_lista[1]'?",
                "opciones": {
                    "A": {"texto": "10", "justificacion": "Incorrecto, 10 es el índice 0."},
                    "B": {"texto": "20", "justificacion": "Correcto, Python usa indexación basada en cero."},
                    "C": {"texto": "IndexError", "justificacion": "Incorrecto, el índice 1 está dentro de los límites."}
                },
                "respuesta_correcta": "B"
            },
            {
                "texto": "¿Qué estructura de datos almacena pares 'clave: valor'?",
                "opciones": {
                    "A": {"texto": "list", "justificacion": "Incorrecto, las listas almacenan elementos ordenados."},
                    "B": {"texto": "tuple", "justificacion": "Incorrecto, las tuplas son listas inmutables."},
                    "C": {"texto": "dict", "justificacion": "Correcto, un diccionario (dict) almacena pares clave-valor."}
                },
                "respuesta_correcta": "C"
            },
            {
                "texto": "¿Qué símbolo se usa para escribir comentarios de una sola línea en Python?",
                "opciones": {
                    "A": {"texto": "//", "justificacion": "Incorrecto, esto es común en lenguajes como C++ o Java."},
                    "B": {"texto": "#", "justificacion": "Correcto, el símbolo de numeral inicia un comentario."},
                    "C": {"texto": "/* ... */", "justificacion": "Incorrecto, esto es para comentarios multilínea en otros lenguajes."}
                },
                "respuesta_correcta": "B"
            },
            {
                "texto": "¿Qué método se usa para añadir un elemento al final de una lista?",
                "opciones": {
                    "A": {"texto": ".add()", "justificacion": "Incorrecto, .add() es para 'sets' (conjuntos)."},
                    "B": {"texto": ".push()", "justificacion": "Incorrecto, .push() es de JavaScript."},
                    "C": {"texto": ".append()", "justificacion": "Correcto, .append() añade el elemento al final de la lista."}
                },
                "respuesta_correcta": "C"
            },
            {
                "texto": "¿Qué palabra clave se usa para definir una función en Python?",
                "opciones": {
                    "A": {"texto": "def", "justificacion": "Correcto, se usa 'def nombre_funcion():'."},
                    "B": {"texto": "function", "justificacion": "Incorrecto, 'function' es de JavaScript y otros lenguajes."},
                    "C": {"texto": "fun", "justificacion": "Incorrecto, 'fun' es de Kotlin o Swift."}
                },
                "respuesta_correcta": "A"
            },
            {
                "texto": "¿Cuál es el operador para 'igualdad' (comparación)?",
                "opciones": {
                    "A": {"texto": "=", "justificacion": "Incorrecto, '=' es el operador de asignación (para guardar un valor en una variable)."},
                    "B": {"texto": "==", "justificacion": "Correcto, '==' compara si dos valores son iguales."},
                    "C": {"texto": "!=", "justificacion": "Incorrecto, '!=' es el operador de 'diferente a'."}
                },
                "respuesta_correcta": "B"
            },
            {
                "texto": "¿Qué hace la construcción 'if __name__ == \"__main__\":'?",
                "opciones": {
                    "A": {"texto": "Define la función principal 'main'.", "justificacion": "Incorrecto, solo es una comprobación, no define nada."},
                    "B": {"texto": "Comprueba si el script se está ejecutando directamente.", "justificacion": "Correcto, el código dentro de este bloque solo se ejecuta si el archivo es corrido como script principal, no si es importado."},
                    "C": {"texto": "Inicia un hilo (thread) principal.", "justificacion": "Incorrecto, no tiene relación con multithreading."}
                },
                "respuesta_correcta": "B"
            }
        ]

        for data in preguntas_data:
            Pregunta.objects.create(
                curso=curso,
                texto=data['texto'],
                opciones=data['opciones'],
                respuesta_correcta=data['respuesta_correcta'],
                nivel=1,
                idioma='es'
            )
        
        self.stdout.write(self.style.SUCCESS(f'¡Éxito! {len(preguntas_data)} preguntas fueron creadas.'))