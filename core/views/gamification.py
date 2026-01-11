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
    
    # ---------------------------------------------------------
    # 1. LÓGICA DE RECLAMO (RETORNO DE GOOGLE)
    # Detectamos si el usuario viene de loguearse para "salvar" su insignia
    # ---------------------------------------------------------
    if request.method == 'GET' and request.GET.get('claim') == '1':
        # Solo si el usuario volvió logueado exitosamente
        if request.user.is_authenticated:
            # A. Guardar la insignia
            InsigniaUsuario.objects.get_or_create(
                usuario=request.user,
                competencia=competencia
            )
            
            # B. Buscar curso para venta (Upselling)
            curso_padre = None
            if competencia.temas.exists():
                tema = competencia.temas.first()
                if tema.cursos.exists():
                    curso_padre = tema.cursos.first()
            
            # C. Mostrar DIRECTAMENTE la pantalla de ganador (sin hacer el test de nuevo)
            return render(request, 'gamification/reto_ganador.html', {
                'competencia': competencia,
                'curso_sugerido': curso_padre,
                'es_usuario_anonimo': False # Ya no es anónimo
            })

    # ---------------------------------------------------------
    # 2. GENERAR EL MINI-RETO (GET NORMAL)
    # ---------------------------------------------------------
    if request.method == 'GET':
        # Buscamos preguntas SOLO de esta competencia
        preguntas_pool = list(competencia.preguntas_banco.all())
        
        # Validación de stock mínimo
        if len(preguntas_pool) < 3:
            return render(request, 'core/error.html', {'mensaje': 'Aún no hay suficientes preguntas para este reto.'})
        
        # Seleccionamos 3 al azar para el Sprint
        preguntas_reto = random.sample(preguntas_pool, 3)
        
        return render(request, 'gamification/reto_sprint.html', {
            'competencia': competencia,
            'preguntas': preguntas_reto
        })

    # ---------------------------------------------------------
    # 3. CALIFICAR EL SPRINT (POST)
    # ---------------------------------------------------------
    if request.method == 'POST':
        puntaje = 0
        total = 0
        
        # Procesar respuestas
        for key, value in request.POST.items():
            if key.startswith('pregunta_'):
                total += 1
                pregunta_id = int(key.split('_')[1])
                respuesta_usuario = value
                
                try:
                    p = Pregunta.objects.get(id=pregunta_id)
                    if p.respuesta_correcta == respuesta_usuario:
                        puntaje += 1
                except Pregunta.DoesNotExist:
                    pass
        
        # LÓGICA DE GANADOR (Debe tener 100% en el sprint)
        es_ganador = (puntaje == total and total > 0)
        
        if es_ganador:
            # 1. Intentar guardar SOLO si está logueado
            # (Si es anónimo, se salta esto, pero NO falla)
            if request.user.is_authenticated:
                InsigniaUsuario.objects.get_or_create(
                    usuario=request.user,
                    competencia=competencia
                )
            
            # 2. Buscar curso sugerido
            curso_padre = None
            if competencia.temas.exists():
                tema = competencia.temas.first()
                if tema.cursos.exists():
                    curso_padre = tema.cursos.first()
            
            # 3. Renderizar SIEMPRE (Esté logueado o no)
            # Pasamos 'es_usuario_anonimo' para que el HTML sepa si mostrar el botón de Google
            return render(request, 'gamification/reto_ganador.html', {
                'competencia': competencia,
                'curso_sugerido': curso_padre,
                'es_usuario_anonimo': not request.user.is_authenticated
            })
            
        else:
            # Si perdió
            return render(request, 'gamification/reto_perdedor.html', {
                'competencia': competencia
            })