import time
from django.core.management.base import BaseCommand
from agents.orchestrator import CDCVOrchestrator
from core.models import Curso

class Command(BaseCommand):
    help = 'Crea un curso desde cero usando la arquitectura Multi-Agente (Builder + Hive Mind)'

    def add_arguments(self, parser):
        parser.add_argument('tema', type=str, help='El tema del curso (Ej: "Python para Data Science")')
        parser.add_argument('--nivel', type=int, default=3, help='Nivel de dificultad (1-5)')

    def handle(self, *args, **options):
        tema = options['tema']
        nivel = options['nivel']
        
        orc = CDCVOrchestrator()

        self.stdout.write(self.style.MIGRATE_HEADING(f"\n🚀 INICIANDO PROTOCOLO DE CREACIÓN: '{tema}' (Nvl {nivel})"))
        
        # PASO 1: EL ARQUITECTO (Builder)
        self.stdout.write("🏗️  Fase 1: Arquitectura y Estructura...")
        
        # Obtenemos el OBJETO CURSO directamente
        curso_creado = orc.crear_nuevo_curso(tema, nivel)

        # Validación: Si devolvió None, hubo error. Si devolvió objeto, seguimos.
        if not curso_creado:
            self.stdout.write(self.style.ERROR(f"❌ Error: El Builder no pudo crear el plan de estudios."))
            return

        # CORRECCIÓN AQUÍ: Accedemos con puntos (.), no con corchetes ['']
        curso_id = curso_creado.id
        total_mcs = curso_creado.micro_competencias.count()
        
        self.stdout.write(self.style.SUCCESS(f"   ✅ Estructura creada. ID: {curso_id} | Competencias base: {total_mcs}"))

        # PASO 2: LA MENTE COLMENA (Hive Mind & Refiller)
        self.stdout.write(f"\n🧠 Fase 2: Activando Hive Mind (Expansión y Relleno)...")
        self.stdout.write("   (Esto tomará unos minutos. Verás el progreso en vivo abajo.)")
        
        # Llamamos al orquestador (que ya tiene prints en tiempo real)
        orc.expandir_conocimiento_curso(curso_id)
        
        self.stdout.write(self.style.SUCCESS("\n✨ PROCESO FINALIZADO."))
        self.stdout.write(f"   Ejecuta 'python manage.py ver_progreso' para ver el reporte final.")