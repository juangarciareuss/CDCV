import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from core.models import Curso, Examen, Pregunta
from core.logic import engine, gateways

@login_required 
def examen(request, curso_id):
    """
    Vista principal del examen.
    Maneja la generación (GET) y la calificación (POST).
    """
    curso = get_object_or_404(Curso, id=curso_id)
    session_key = f'examen_set_{curso_id}'
    
    # 1. Calculamos cuántas preguntas PIDE el examen (Configuración del Admin)
    # Usamos la propiedad que creamos en el modelo. Si no existe, usamos 10 por defecto.
    limite_configurado = getattr(curso, 'total_preguntas_examen', 10)
    if limite_configurado == 0: limite_configurado = 10 

    if request.method == "GET":
        # --- LÓGICA DE ACTUALIZACIÓN AUTOMÁTICA ---
        # Si ya existe una sesión, verificamos si coincide con la nueva configuración.
        if session_key in request.session:
            ids_actuales = request.session[session_key]
            # Si el admin cambió el total (ej: de 12 a 20), borramos la sesión vieja
            if len(ids_actuales) != limite_configurado:
                del request.session[session_key]

        # --- GENERACIÓN DE PREGUNTAS ---
        if session_key not in request.session:
            # Pedimos candidatos al motor (trae stock disponible)
            preguntas_candidatas, error = engine.diagnosticar_y_pescar_preguntas(curso)
            if error: return render(request, "core/error.html", {"mensaje": error})
            
            # FILTRADO INTELIGENTE:
            # Si hay más candidatos que el límite configurado, hacemos un sample.
            # (Idealmente esto debería respetar los cupos por tema, pero para mantener tu lógica actual
            #  usamos random.sample sobre el total, ajustado al límite que definiste).
            if len(preguntas_candidatas) > limite_configurado:
                preguntas_seleccionadas = random.sample(preguntas_candidatas, limite_configurado)
            else:
                # Si hay menos preguntas que las que pides (Stock bajo), usa todas las que haya.
                preguntas_seleccionadas = preguntas_candidatas
            
            # Guardamos en sesión
            request.session[session_key] = [p.id for p in preguntas_seleccionadas]
        
        # Recuperar objetos Pregunta desde la sesión
        ids = request.session[session_key]
        preguntas_set = list(Pregunta.objects.filter(id__in=ids))
        # Mantener el orden aleatorio original
        preguntas_set.sort(key=lambda x: ids.index(x.id))
        
        return render(request, "core/examen.html", {
            'curso': curso, 
            'preguntas': preguntas_set
        })

    if request.method == "POST":
        ids = request.session.get(session_key)
        if not ids: return render(request, "core/error.html", {"mensaje": "Sesión expirada. Por favor recarga."})
        
        # Filtrar solo campos que sean respuestas
        respuestas = {k: v for k, v in request.POST.items() if k.startswith('pregunta_')}
        
        # Calificar usando el motor
        data, error = engine.finalizar_examen(request.user, curso, ids, respuestas)
        
        # Limpiar sesión tras finalizar
        if session_key in request.session: del request.session[session_key]
        
        # Renderizar resultados (reusa examen.html pero con variable 'resultados')
        return render(request, "core/resultados_examen.html", {'curso': curso, **data})


# --- PAGOS PAYPAL (Sin cambios, mantenemos tu lógica) ---
@login_required
def crear_pago_paypal(request, examen_id):
    examen_obj = get_object_or_404(Examen, id=examen_id)
    
    # Seguridad: Solo el dueño y solo si aprobó
    if examen_obj.usuario != request.user or not examen_obj.aprobado:
        return HttpResponseBadRequest("No autorizado o examen no aprobado.")
    
    payment = gateways.preparar_pago_paypal(request, examen_obj)
    
    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url": return redirect(str(link.href))
    return render(request, "core/error.html", {"mensaje": "Error iniciando PayPal"})

@login_required
def pago_exitoso(request):
    payer_id = request.GET.get('PayerID')
    payment_id = request.GET.get('paymentId')
    
    certificado, error = gateways.ejecutar_pago_y_certificar(payment_id, payer_id)
    
    if error: return render(request, "core/error.html", {"mensaje": f"Error: {error}"})
    
    # Redirigir al perfil para ver el certificado
    return redirect('core:perfil_usuario') # Asegúrate que el name sea correcto en urls.py

@login_required
def pago_cancelado(request):
    return render(request, 'core/pago_cancelado.html')