import time
import sys
from .builder_agent import BuilderAgent
from .refiller_agent import RefillerAgent
from core.models import Curso

class CDCVOrchestrator:
    """
    ORQUESTADOR V3 (MODO TRANSPARENTE)
    Muestra el progreso en tiempo real en la consola.
    """
    def __init__(self):
        self.builder = BuilderAgent()
        self.refiller = RefillerAgent()

    def crear_nuevo_curso(self, nicho, nivel):
        # Delegamos al Builder (este ya tiene sus propios prints internos)
        return self.builder.construir_curso(nicho, nivel)

    def expandir_conocimiento_curso(self, curso_id):
        """
        Recorre las competencias y muestra una barra de progreso real.
        """
        try:
            curso = Curso.objects.get(id=curso_id)
            mcs_del_curso = curso.micro_competencias.all()
            total_mcs = mcs_del_curso.count()
            
            print(f"\n📡 CONECTANDO CON HIVE MIND PARA: {curso.nombre}")
            print(f"   🎯 Objetivo: Analizar y poblar {total_mcs} micro-competencias.")
            print("   (Presiona Ctrl+C solo si deseas detener la emergencia)\n")

            if total_mcs == 0:
                print("⚠️  ALERTA: El curso no tiene competencias. Ejecuta el Builder primero.")
                return {"status": "warning", "message": "Sin competencias"}

            # ITERACIÓN EN TIEMPO REAL
            cambios_totales = 0
            
            for i, mc in enumerate(mcs_del_curso, 1):
                # 1. Diagnóstico Rápido
                num_preguntas = mc.preguntas_banco.count()
                
                # Formato visual: [ 1/15] Nombre de la competencia......
                prefix = f"[{i:02d}/{total_mcs:02d}] {mc.nombre[:40]:<40}"
                print(f"{prefix}", end=" ", flush=True)

                # 2. Toma de Decisión
                if num_preguntas < 5:
                    necesarias = 5 - num_preguntas
                    print(f"🔻 Faltan {necesarias}. Generando...", end=" ", flush=True)
                    
                    orden = {
                        "target_mc": mc.nombre,
                        "cantidad": necesarias,
                        "instruccion_nivel": f"Refuerzo nivel {curso.nivel}"
                    }
                    
                    tema_contexto = mc.temas.first()
                    
                    if tema_contexto:
                        # 3. Llamada a la API (Aquí es donde suele demorar 2-5 seg)
                        creadas = self.refiller.ejecutar_orden_quirurgica(tema_contexto, orden)
                        
                        if creadas > 0:
                            print(f"✅ +{creadas} preguntas.", flush=True)
                            cambios_totales += creadas
                        else:
                            print(f"❌ Error API.", flush=True)
                        
                        # Pausa de seguridad para no quemar la API Key
                        time.sleep(1.5) 
                    else:
                        print("⚠️ Sin Tema (Skip)", flush=True)
                else:
                    # Si ya está llena, pasamos rápido
                    print(f"👌 Completa ({num_preguntas}).", flush=True)

            print(f"\n✨ PROCESO TERMINADO. Se generaron un total de {cambios_totales} preguntas nuevas.")
            return {"status": "success", "detalles": []}

        except Exception as e:
            print(f"\n🔥 ERROR CRÍTICO EN ORQUESTADOR: {str(e)}")
            return {"status": "error", "message": str(e)}