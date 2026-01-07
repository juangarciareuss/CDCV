import time
from django.core.management.base import BaseCommand
from django.db.models import Count
from core.models import Curso

class Command(BaseCommand):
    help = 'Muestra un reporte forense del último curso creado y su nivel de población por IA.'

    def handle(self, *args, **options):
        # 1. Buscar el último curso
        curso = Curso.objects.last()

        if not curso:
            self.stdout.write(self.style.ERROR("❌ No hay cursos en el sistema."))
            return

        self.stdout.write(self.style.SUCCESS(f"\n📊 TABLERO DE CONTROL: {curso.nombre}"))
        self.stdout.write(f"   ID: {curso.id} | Nivel Técnico: {curso.nivel}")
        self.stdout.write("-" * 60)

        # 2. Análisis de Competencias
        # Usamos 'preguntas_banco' que es el related_name que definimos en content.py
        mcs = curso.micro_competencias.annotate(
            total_preguntas=Count('preguntas_banco')
        ).order_by('-total_preguntas')

        if not mcs.exists():
            self.stdout.write(self.style.WARNING("⚠️ Este curso es un cascarón vacío (Sin competencias asignadas)."))
            return

        total_mcs = mcs.count()
        llenas = 0
        vacias = 0
        total_preguntas_sistema = 0

        self.stdout.write(f"🧩 Competencias Totales: {total_mcs}\n")

        # 3. Renderizado de Barras
        for mc in mcs:
            count = mc.total_preguntas
            total_preguntas_sistema += count
            
            # Lógica visual
            if count >= 5:
                barra = "🟩" * count
                estado = self.style.SUCCESS("LISTA")
                llenas += 1
            elif count > 0:
                barra = "🟨" * count
                estado = self.style.WARNING("EN PROCESO")
                vacias += 1
            else:
                barra = "⬜"
                estado = self.style.ERROR("VACÍA")
                vacias += 1
            
            # Limitamos la barra visual a 10 cuadros para que no rompa la pantalla
            if len(barra) > 10: barra = "🟩" * 10 + "+"

            self.stdout.write(f" {barra:<12} ({count}) {mc.nombre[:50]:<50} -> {estado}")

        self.stdout.write("-" * 60)
        
        # 4. KPI Finales
        completion_rate = (llenas / total_mcs) * 100
        self.stdout.write(f"📈 KPI DE PRODUCCIÓN:")
        self.stdout.write(f"   - Total Preguntas: {total_preguntas_sistema}")
        self.stdout.write(f"   - Tasa de Completitud: {completion_rate:.1f}%")
        
        if vacias > 0:
             self.stdout.write(self.style.WARNING(f"\n⚠️  ACCIÓN REQUERIDA: Faltan rellenar {vacias} competencias."))
             self.stdout.write("    Ejecuta el orquestador nuevamente para completar los huecos.")
        else:
             self.stdout.write(self.style.SUCCESS("\n✨ EXCELENTE: El curso está listo para producción."))