import json
import os
import time
from google import genai
from django.db.models import Count
from core.models import Tema, MicroCompetencia

# Importamos a tu Obrero recién creado
from .refiller_agent import RefillerAgent

class HiveCEO:
    """
    EL DIRECTOR EJECUTIVO (The Hive Mind).
    Punto de entrada único. Coordina la expansión estratégica de un tema.
    """
    def __init__(self):
        self.taxonomist = TaxonomistManager()
        self.operations = OperationsManager()
        # QA Agent (Pendiente para V2)

    def ejecutar_estrategia_dominacion(self, tema_slug):
        """
        EL BOTÓN ROJO.
        1. Analiza el mapa (Taxónomo).
        2. Detecta debilidades y asigna recursos (Operaciones).
        3. Ejecuta la producción (Refiller).
        """
        try:
            tema = Tema.objects.get(slug=tema_slug)
        except Tema.DoesNotExist:
            return "❌ Error: El tema objetivo no existe."

        reporte = [f"🧠 HIVE MIND: Iniciando expansión de '{tema.nombre}'"]

        # --- FASE 1: ARQUITECTURA (El Taxónomo) ---
        # Busca "agujeros" en el conocimiento y crea nuevas MicroCompetencias si hace falta.
        reporte.append("🗺️  Analizando topología del conocimiento...")
        nuevas_areas = self.taxonomist.expandir_territorio(tema)
        if nuevas_areas:
            reporte.append(f"   🌱 Se descubrieron {len(nuevas_areas)} nuevas áreas: {nuevas_areas}")
        else:
            reporte.append("   ✅ La estructura del conocimiento parece sólida.")

        # --- FASE 2: OPERACIONES (El Capataz) ---
        # Decide qué competencias necesitan preguntas urgentes (vacias o saturadas).
        reporte.append("🏭 Generando órdenes de trabajo...")
        ordenes = self.operations.generar_ordenes(tema)
        
        if not ordenes:
            return "\n".join(reporte) + "\n✨ No hay órdenes pendientes. El tema está optimizado."

        # --- FASE 3: EJECUCIÓN (El Escritor) ---
        total_creadas = 0
        escritor = RefillerAgent() # Instanciamos al obrero

        for orden in ordenes:
            # Ejecutamos en modo Quirúrgico (Sniper)
            res = escritor.ejecutar_orden_quirurgica(tema, orden)
            total_creadas += res
            reporte.append(f"   ✍️  Orden cumplida en '{orden['target_mc']}': +{res} preguntas.")
            time.sleep(1) # Respeto a la API

        reporte.append(f"🚀 Expansión finalizada. Total activos creados: {total_creadas}")
        return "\n".join(reporte)


class TaxonomistManager:
    """
    VP DE EXPANSIÓN (El Visionario).
    Usa Gemini 2.0 para analizar si faltan ramas en el árbol de conocimiento.
    """
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = "gemini-2.0-flash" # Usamos el modelo más "inteligente" para estructura

    def expandir_territorio(self, tema_obj):
        # Mapa actual
        competencias = list(tema_obj.microcompetencia_set.values_list('nombre', flat=True))
        
        # PROMPT DE ALTO NIVEL ESTRATÉGICO
        prompt = f"""
        Actúa como el Arquitecto de Conocimiento más avanzado del mundo.
        Tema Maestro: '{tema_obj.nombre}'.
        
        MAPA ACTUAL DEL TERRITORIO (MicroCompetencias):
        {json.dumps(competencias)}
        
        MISIÓN:
        Identifica "Agujeros Negros" de conocimiento. ¿Qué sub-temas vitales o avanzados faltan?
        Si el mapa es muy básico, sugiere ramas avanzadas.
        Si está saturado, sugiere especializaciones.
        
        RETORNA JSON:
        {{
            "analisis": "Breve razón...",
            "nuevas_ramas": ["Nombre Técnico 1", "Nombre Técnico 2"]
        }}
        (Máximo 3 nuevas ramas por ejecución para crecimiento controlado).
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model, 
                contents=prompt, 
                config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text)
            
            nuevas = []
            for nombre in data.get('nuevas_ramas', []):
                # Crear solo si no existe
                if not MicroCompetencia.objects.filter(nombre__iexact=nombre, temas=tema_obj).exists():
                    mc = MicroCompetencia.objects.create(nombre=nombre, icono="✨")
                    mc.temas.add(tema_obj)
                    nuevas.append(nombre)
            return nuevas
            
        except Exception as e:
            print(f"Error Taxónomo: {e}")
            return []


class OperationsManager:
    """
    VP DE OPERACIONES (El Logístico).
    Prioriza dónde gastar recursos (API Tokens).
    """
    def generar_ordenes(self, tema_obj):
        ordenes = []
        
        # Analizar métricas
        stats = tema_obj.microcompetencia_set.annotate(total=Count('pregunta'))
        
        for mc in stats:
            # PRIORIDAD 1: Emergencia (Vacíos)
            if mc.total == 0:
                ordenes.append({
                    "target_mc": mc.nombre,
                    "cantidad": 5, 
                    "instruccion_nivel": "Fundamentos y conceptos clave (Nivel 1-3)"
                })
            # PRIORIDAD 2: Refuerzo (Poco contenido)
            elif mc.total < 5:
                ordenes.append({
                    "target_mc": mc.nombre,
                    "cantidad": 3,
                    "instruccion_nivel": "Casos de uso prácticos (Nivel 3-4)"
                })
            # PRIORIDAD 3: Maestría (Mucho contenido básico, falta experto)
            # (Aquí podríamos analizar el promedio de dificultad, pero por simplicidad...)
            elif mc.total > 10 and mc.total < 15:
                 ordenes.append({
                    "target_mc": mc.nombre,
                    "cantidad": 2,
                    "instruccion_nivel": "Casos de borde y escenarios complejos (Nivel 5)"
                })
        
        # Ordenar por urgencia (Los vacíos primero) y limitar lote
        # Lógica: Primero los que tienen 0 preguntas
        ordenes.sort(key=lambda x: x['cantidad'], reverse=True)
        return ordenes[:5] # Máximo 5 órdenes por ejecución para no bloquear el servidor