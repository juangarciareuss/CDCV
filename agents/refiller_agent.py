import json
import os
import time
import random
from google import genai
from django.db.models import Count
from core.models import Tema, Pregunta, MicroCompetencia

class RefillerAgent:
    """
    AGENTE ESCRITOR (Refiller V4.0)
    ---------------------------------------------------
    Rol: Obrero Especializado / Fábrica de Contenido.
    Misión: Generar preguntas técnicas de alta calidad siguiendo órdenes estrictas.
    Capacidades:
    1. Modo Automático (Gap Analysis): Detecta qué falta y lo rellena.
    2. Modo Quirúrgico (Sniper): Recibe una orden específica ("Crea 3 preguntas de X") y la ejecuta.
    """
    
    def __init__(self):
        # Cliente oficial de Google GenAI (2025/2026)
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # Estrategia de Modelos:
        # Prioridad 1: Gemini 2.5 Flash (Velocidad y Calidad actual)
        # Prioridad 2: Gemini 2.0 Flash (Respaldo robusto)
        self.modelos = ["gemini-2.5-flash", "gemini-2.0-flash"]

    # --- MODO 1: AUTOMÁTICO (Gap Analysis) ---
    def poblar_tema(self, nombre_tema, cantidad=5):
        """
        Escanea un tema y decide autónomamente dónde generar preguntas.
        Útil para el botón "Curar Curso" o mantenimiento general.
        """
        try:
            tema_obj = Tema.objects.get(nombre=nombre_tema)
        except Tema.DoesNotExist:
            return f"❌ Error: El tema '{nombre_tema}' no existe."

        # 1. Análisis de Estado
        stats = MicroCompetencia.objects.filter(temas=tema_obj).annotate(
            num_preguntas=Count('pregunta')
        )
        
        # Clasificación
        mcs_vacias = [mc.nombre for mc in stats if mc.num_preguntas == 0]
        mcs_bajas = [mc.nombre for mc in stats if 0 < mc.num_preguntas < 5]
        mcs_llenas = [mc.nombre for mc in stats if mc.num_preguntas >= 10]
        
        # 2. Configuración del Prompt Inteligente
        prompt = f"""
        Eres un Arquitecto de Pruebas Técnicas.
        Objetivo: Crear {cantidad} nuevas preguntas para el tema: '{nombre_tema}'.
        
        ESTADO DEL SISTEMA:
        - PRIORIDAD ALTA (Están vacías): {json.dumps(mcs_vacias[:10])}
        - PRIORIDAD MEDIA (Necesitan refuerzo): {json.dumps(mcs_bajas[:10])}
        - PROHIBIDO (Ya están saturadas): {json.dumps(mcs_llenas)}
        
        INSTRUCCIONES:
        1. Si hay prioridades altas, atácalas primero.
        2. Si todo está lleno, CREA una nueva MicroCompetencia específica (Subtema avanzado).
        3. Dificultad variada (2 a 5).
        
        FORMATO JSON:
        [
            {{
                "microcompetencia": "Nombre exacto o Nuevo",
                "texto": "Pregunta...",
                "opciones": {{"a": "...", "b": "...", "c": "...", "d": "..."}},
                "correcta": "a",
                "dificultad": 3,
                "justificacion": "..."
            }}
        ]
        """
        
        return self._ejecutar_generacion(prompt, tema_obj)

    # --- MODO 2: QUIRÚRGICO (Sniper) ---
    def ejecutar_orden_quirurgica(self, tema_obj, orden):
        """
        Recibe una orden precisa del 'OperationsManager'.
        Ej: "Crea 3 preguntas para 'Excel: Macros' enfocadas en seguridad".
        """
        target_mc = orden.get('target_mc')
        cantidad = orden.get('cantidad', 3)
        instruccion = orden.get('instruccion_nivel', 'Nivel estándar')

        prompt = f"""
        ORDEN DE TRABAJO PRIORITARIA (MODO SNIPER).
        Tema Maestro: {tema_obj.nombre}
        
        OBJETIVO:
        Generar {cantidad} preguntas EXCLUSIVAMENTE para la competencia: '{target_mc}'.
        
        DIRECTRIZ TÉCNICA: {instruccion}
        
        REGLAS:
        1. No cambies el nombre de la microcompetencia.
        2. Asegura que las preguntas no sean triviales.
        
        FORMATO JSON:
        [
            {{
                "microcompetencia": "{target_mc}",
                "texto": "Pregunta...",
                "opciones": {{"a": "...", "b": "...", "c": "...", "d": "..."}},
                "correcta": "a",
                "dificultad": 4,
                "justificacion": "..."
            }}
        ]
        """
        
        # Reutilizamos el motor de generación, pero sabemos que el prompt es restringido
        return self._ejecutar_generacion(prompt, tema_obj)

    # --- MOTOR DE EJECUCIÓN (Privado) ---
    def _ejecutar_generacion(self, prompt, tema_obj):
        config_agente = {
            "temperature": 0.4, 
            "response_mime_type": "application/json",
        }

        try:
            # 1. Llamada a la IA con rotación de modelos
            response = self._llamar_ia_con_fallback(prompt, config_agente)
            if not response: 
                return "❌ Error: La IA no respondió (Timeout/Cuota)."

            # 2. Limpieza y Parseo
            raw_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw_text)
            
            creadas = 0
            
            # 3. Procesamiento y Guardado
            for item in data:
                # A. Deduplicación (Anti-Spam)
                if Pregunta.objects.filter(texto=item['texto']).exists():
                    continue 

                # B. Gestión de MicroCompetencia
                nombre_mc = item.get('microcompetencia', 'General').strip()
                
                # Buscar o Crear
                mc_obj, created = MicroCompetencia.objects.get_or_create(
                    nombre__iexact=nombre_mc,
                    defaults={'nombre': nombre_mc, 'icono': '⚡'}
                )
                
                # Si se creó recién o no estaba ligada, la ligamos al tema
                if created or not mc_obj.temas.filter(id=tema_obj.id).exists():
                    mc_obj.temas.add(tema_obj)

                # C. Crear Pregunta
                Pregunta.objects.create(
                    micro_competencia=mc_obj,
                    texto=item['texto'],
                    opciones=item['opciones'],
                    respuesta_correcta=item['correcta'],
                    dificultad=item.get('dificultad', 3),
                    justificacion=item.get('justificacion', 'Generada por IA'),
                    idioma='es'
                )
                creadas += 1

            return creadas # Retorna int para que el Manager sume totales

        except Exception as e:
            print(f"🔥 Error en Refiller: {e}")
            return 0

    def _llamar_ia_con_fallback(self, prompt, config):
        """Intenta con el modelo más rápido, si falla, usa el tanque."""
        for modelo in self.modelos:
            try:
                # print(f"🤖 Intentando con {modelo}...") 
                return self.client.models.generate_content(
                    model=modelo, contents=prompt, config=config
                )
            except Exception:
                time.sleep(1) # Pequeña pausa antes del reintento
                continue
        return None