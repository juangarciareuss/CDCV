import json
import random
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from core.models import Tema, Pregunta, PerfilEntrenamiento

@login_required
def gym_home(request, tema_slug):
    tema = get_object_or_404(Tema, slug=tema_slug)
    # Obtener o crear perfil persistente
    perfil, created = PerfilEntrenamiento.objects.get_or_create(
        user=request.user,
        tema=tema,
        defaults={'nivel_actual': 1.0}
    )
    
    return render(request, 'gym/gym_arena.html', {
        'tema': tema,
        'nivel_usuario': perfil.nivel_actual
    })

# --- API ---

@login_required
def api_get_pregunta(request, tema_id):
    tema = get_object_or_404(Tema, id=tema_id)
    perfil, _ = PerfilEntrenamiento.objects.get_or_create(user=request.user, tema=tema)
    
    # Historial de sesión (temporal para no repetir en racha inmediata)
    historial_sesion = request.session.get(f'gym_history_{tema.id}', [])
    
    # Lógica de Selección: Buscamos preguntas cercanas al nivel del usuario
    # Rango de tolerancia: +/- 1.5 niveles
    rango_min = max(0, perfil.nivel_actual - 1.5)
    rango_max = perfil.nivel_actual + 1.5
    
    preguntas = Pregunta.objects.filter(
        micro_competencia__temas=tema
    ).exclude(id__in=historial_sesion) # Excluir las de esta sesión

    # Intentar buscar en el rango de dificultad adecuado
    candidatas = preguntas.filter(dificultad__gte=rango_min, dificultad__lte=rango_max)
    
    # Si no hay (porque el usuario es muy pro o muy novato), buscar cualquiera
    if not candidatas.exists():
        candidatas = preguntas
        
    if not candidatas.exists():
         return JsonResponse({'error': 'No quedan preguntas disponibles.'}, status=404)

    pregunta = candidatas.order_by('?').first()
    
    return JsonResponse({
        'id': pregunta.id,
        'texto': pregunta.texto,
        'dificultad': pregunta.dificultad,
        'opciones': pregunta.opciones
    })

@login_required
@require_POST
def api_responder(request):
    try:
        data = json.loads(request.body)
        pregunta = get_object_or_404(Pregunta, id=data.get('pregunta_id'))
        tema = pregunta.micro_competencia.temas.first() # Asumimos conexión
        perfil, _ = PerfilEntrenamiento.objects.get_or_create(user=request.user, tema=tema)
        
        es_correcto = (data.get('respuesta') == pregunta.respuesta_correcta)
        
        # --- ALGORITMO DE VOLATILIDAD (K-FACTOR) ---
        # Si llevas pocas preguntas (<10), el sistema es muy volátil (salta rápido)
        # Si llevas muchas, se vuelve estable.
        if perfil.preguntas_respondidas < 5:
            k_factor = 0.8  # Volatilidad Extrema (sube/baja casi 1 punto entero)
        elif perfil.preguntas_respondidas < 15:
            k_factor = 0.4  # Volatilidad Media
        else:
            k_factor = 0.1  # Estabilidad (Afinamiento fino)

        # Cálculo del cambio
        if es_correcto:
            # Bonus si la pregunta era más difícil que tu nivel actual
            gap = max(0, pregunta.dificultad - perfil.nivel_actual)
            cambio = k_factor + (gap * 0.1) 
        else:
            # Penalización
            cambio = -k_factor
            
        # Aplicar y guardar
        nuevo_nivel = perfil.nivel_actual + cambio
        perfil.nivel_actual = max(1.0, round(nuevo_nivel, 2)) # Nunca menos de 1.0
        perfil.preguntas_respondidas += 1
        perfil.save()
        
        # Guardar historial sesión
        historial_key = f'gym_history_{tema.id}'
        historial = request.session.get(historial_key, [])
        historial.append(pregunta.id)
        request.session[historial_key] = historial

        return JsonResponse({
            'correcto': es_correcto,
            'justificacion': pregunta.justificacion,
            'nivel_nuevo': perfil.nivel_actual,
            'delta': cambio,
            'respuesta_correcta_key': pregunta.respuesta_correcta
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)