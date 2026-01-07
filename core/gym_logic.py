# core/gym_logic.py
import random
from core.models import Pregunta, PerfilMicroCompetencia, MicroCompetencia

def obtener_siguiente_pregunta(usuario, tema_id):
    """
    Selecciona la mejor pregunta para el usuario dentro de un TEMA.
    Estrategia: 60% reforzar debilidades, 40% exploración/azar.
    """
    # 1. Buscamos todas las competencias del tema
    competencias_tema = MicroCompetencia.objects.filter(temas__id=tema_id)
    
    # 2. Vemos cómo está el usuario en esas competencias
    perfiles = PerfilMicroCompetencia.objects.filter(
        usuario=usuario, 
        micro_competencia__in=competencias_tema
    )
    
    # Mapeamos: {competencia_id: nivel_actual}
    mapa_niveles = {p.micro_competencia.id: p.nivel_actual for p in perfiles}
    
    # 3. Decisión: ¿Qué competencia atacamos?
    # Buscamos la competencia con menor nivel (o una que no haya tocado aún)
    competencia_objetivo = None
    
    # A veces (30%) elegimos al azar para variar
    if random.random() < 0.3:
        competencia_objetivo = competencias_tema.order_by('?').first()
    else:
        # Prioridad: Las que tienen nivel más bajo
        # Si no tiene perfil, asumimos nivel 0
        competencia_objetivo = sorted(
            competencias_tema, 
            key=lambda c: mapa_niveles.get(c.id, 0.0)
        )[0] # Tomamos la primera (la más débil)

    if not competencia_objetivo:
        return None # No hay competencias en el tema

    # 4. Seleccionar Pregunta dentro de esa Competencia
    # Idealmente una cercana a su nivel (Zona de Desarrollo Próximo)
    nivel_user = mapa_niveles.get(competencia_objetivo.id, 1.0)
    dificultad_buscada = max(1, round(nivel_user / 2)) # Convertimos escala 10 a escala 5
    
    # Buscamos preguntas de esa dificultad, si no hay, cualquiera de la competencia
    preguntas = Pregunta.objects.filter(
        micro_competencia=competencia_objetivo,
        # Opcional: Excluir las que ya respondió hoy (requiere historial más complejo)
    )
    
    # Intentar match de dificultad exacta
    candidatas = preguntas.filter(dificultad=dificultad_buscada)
    if not candidatas.exists():
        # Si no hay de su nivel exacto, buscamos +/- 1
        candidatas = preguntas.filter(dificultad__range=(dificultad_buscada-1, dificultad_buscada+1))
        
    if not candidatas.exists():
        candidatas = preguntas # Fallback: cualquier pregunta sirve

    return candidatas.order_by('?').first()