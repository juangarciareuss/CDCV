import os
from dotenv import load_dotenv
from google import genai
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Lista los modelos disponibles sin filtros complejos'

    def handle(self, *args, **kwargs):
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            self.stdout.write(self.style.ERROR("Falta GEMINI_API_KEY"))
            return

        client = genai.Client(api_key=api_key)

        self.stdout.write("--- LISTA DE MODELOS REALES ---")
        
        try:
            # Listamos todo lo que hay
            for m in client.models.list():
                # En la versión nueva SDK, el nombre suele estar en 'name' o es un string directo
                nombre = getattr(m, 'name', str(m))
                
                # Solo nos interesan los que empiezan con 'models/' o 'gemini'
                if 'gemini' in str(nombre):
                    self.stdout.write(self.style.SUCCESS(f"-> {nombre}"))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error crítico: {e}"))