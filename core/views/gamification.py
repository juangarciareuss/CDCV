from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models import MicroCompetencia, Pregunta, InsigniaUsuario, Curso
import random

def reto_microcompetencia(request, slug_competencia):
    """
    Vista pública (Lead Magnet).
    Permite probar una habilidad específica en 2 minutos.
    """
    competencia = get_object_or_404(MicroCompetencia, slug=slug_competencia)
    
    # 1. GENERAR EL MINI-RETO (GET)
    if request.method == 'GET':
        # Buscamos preguntas SOLO de esta competencia
        preguntas_pool = list(competencia.preguntas_banco.all())
        
        # Validación de stock mínimo
        if len(preguntas_pool) < 3:
            return render(request, 'core/error.html', {'mensaje': 'Aún no hay suficientes preguntas para este reto.'})
        
        # Seleccionamos 3 al azar para el Sprint
        preguntas_reto = random.sample(preguntas_pool, 3)
        
        # ✅ CORRECCIÓN: Apuntamos a la carpeta 'gamification'
        return render(request, 'gamification/reto_sprint.html', {
            'competencia': competencia,
            'preguntas': preguntas_reto
        })

    # 2. CALIFICAR EL SPRINT (POST)
    if request.method == 'POST':

        puntaje = 0
        total = 0
        
        # Calificación simple
        for key, value in request.POST.items():
            if key.startswith('pregunta_'):
                total += 1
                pregunta_id = int(key.split('_')[1])
                respuesta_usuario = value
                
                # Validar contra BD
                try:
                    p = Pregunta.objects.get(id=pregunta_id)
                    if p.respuesta_correcta == respuesta_usuario:
                        puntaje += 1
                except Pregunta.DoesNotExist:
                    pass
        
        # LÓGICA DE GANADOR (Debe tener 100% en el sprint)
        es_ganador = (puntaje == total and total > 0)
        
        if es_ganador:
        # 🏅 AGREGAMOS CONDICIONAL: Solo guardamos si está logueado
         if request.user.is_authenticated:
            InsigniaUsuario.objects.get_or_create(
                usuario=request.user,
                competencia=competencia
            )
            
            # Buscar el curso padre para hacer Upselling (Venta Cruzada)
            curso_padre = None
            if competencia.temas.exists():
                tema = competencia.temas.first()
                if tema.cursos.exists():
                    curso_padre = tema.cursos.first()
            
            # ✅ CORRECCIÓN: Apuntamos a la carpeta 'gamification'
            return render(request, 'gamification/reto_ganador.html', {
                'competencia': competencia,
                'curso_sugerido': curso_padre
            })
        else:
            # ✅ CORRECCIÓN: Apuntamos a la carpeta 'gamification'
            return render(request, 'gamification/reto_perdedor.html', {
                'competencia': competencia
            })