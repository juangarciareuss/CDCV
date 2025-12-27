# core/logic/ai_services/orchestrator.py
import time
from .builder_agent import BuilderAgent
from .refiller_agent import RefillerAgent
from core.models import Curso

class CDCVOrchestrator:
    """
    Coordinador central de la fuerza laboral de IA.
    Recibe órdenes de alto nivel y delega a los agentes especialistas.
    """
    def __init__(self):
        # Inicializamos los agentes especialistas
        self.builder = BuilderAgent()
        self.refiller = RefillerAgent()

    def curar_curso_roto(self, curso_id):
        """
        Analiza un curso existente, detecta faltantes y llama al Refiller.
        Se usa desde el botón 'Curar con IA' del Dashboard.
        """
        try:
            curso = Curso.objects.get(id=curso_id)
            config = curso.estructura_examen or {}
            reglas = config.get('reglas_seleccion', [])
            
            reporte_acciones = []

            for regla in reglas:
                tema_nombre = regla.get('tema_nombre')
                cantidad_necesaria = regla.get('cantidad', 5)
                
                # Delegamos al Refiller la tarea de generar preguntas para este tema
                # Nota: El Refiller es inteligente, tú le pides X cantidad y él genera calidad.
                resultado = self.refiller.poblar_tema(tema_nombre, cantidad=cantidad_necesaria)
                reporte_acciones.append(f"{tema_nombre}: {resultado}")

                # --- 2. EL FRENO DE MANO ---
                # Esperamos 10 segundos entre cada petición para no saturar a Google
                # (El plan gratuito suele permitir 2-4 peticiones por minuto de forma segura)
                time.sleep(10)

            return {
                "status": "success", 
                "message": f"Orquestación completada para {curso.nombre}",
                "detalles": reporte_acciones
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

def crear_nuevo_producto(self, nicho_mercado, nivel):
        """
        Llama al Builder para crear un curso.
        El argumento 'nivel' es requerido estrictamente.
        """
        # Pasamos el nivel explícitamente. Si falta, explota aquí.
        return self.builder.construir_curso(nicho_mercado, nivel_dificultad=nivel)