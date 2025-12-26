# agents/ai_services.py

from .builder_agent import BuilderAgent

class CDCVOrchestrator:
    """
    [LEGACY ADAPTER]
    Esta clase actúa como puente entre las vistas antiguas y la nueva arquitectura.
    Si usas el botón viejo, este orquestador redirige el trabajo al BuilderAgent nuevo.
    """
    
    def __init__(self):
        self.builder = BuilderAgent()

    def crear_nuevo_producto(self, nicho):
        """
        Recibe la orden de la vista antigua y la delega al nuevo Agente Constructor.
        """
        print(f"🔄 [ORCHESTRATOR] Redirigiendo solicitud legacy para: {nicho}")
        try:
            # Llamamos al método nuevo del modelo Spotify
            resultado = self.builder.construir_curso(nicho)
            return f"✅ Orquestado con éxito: {resultado}"
        except Exception as e:
            return f"❌ Error en orquestación: {str(e)}"

    def curar_curso_roto(self, curso_id):
        """
        Este método era para reparar cursos. Por ahora lo dejamos en mantenimiento
        hasta que creemos el 'DoctorAgent'.
        """
        return {
            "status": "warning",
            "message": "🛠️ El Agente Curador está en mantenimiento por migración a V2."
        }