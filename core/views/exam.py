import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from core.models import Curso, Examen, Pregunta
from core.logic import engine, gateways

@login_required 
def examen(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    session_key = f'examen_set_{curso_id}'
    
    if request.method == "GET":
        if session_key not in request.session:
            preguntas_candidatas, error = engine.diagnosticar_y_pescar_preguntas(curso)
            if error: return render(request, "core/error.html", {"mensaje": error})
            
            limite = curso.cantidad_preguntas 
            if len(preguntas_candidatas) > limite:
                preguntas_seleccionadas = random.sample(preguntas_candidatas, limite)
            else:
                preguntas_seleccionadas = preguntas_candidatas
            
            request.session[session_key] = [p.id for p in preguntas_seleccionadas]
        
        ids = request.session[session_key]
        preguntas_set = list(Pregunta.objects.filter(id__in=ids))
        preguntas_set.sort(key=lambda x: ids.index(x.id))
        
        return render(request, "core/examen.html", {'curso': curso, 'preguntas': preguntas_set})

    if request.method == "POST":
        ids = request.session.get(session_key)
        if not ids: return render(request, "core/error.html", {"mensaje": "Sesión expirada."})
        
        respuestas = {k: v for k, v in request.POST.items() if k.startswith('pregunta_')}
        data, error = engine.finalizar_examen(request.user, curso, ids, respuestas)
        
        if session_key in request.session: del request.session[session_key]
        return render(request, "core/examen.html", {'curso': curso, **data})

# --- PAGOS PAYPAL ---
@login_required
def crear_pago_paypal(request, examen_id):
    examen_obj = get_object_or_404(Examen, id=examen_id)
    if examen_obj.usuario != request.user or not examen_obj.aprobado:
        return HttpResponseBadRequest("No autorizado.")
    
    payment = gateways.preparar_pago_paypal(request, examen_obj)
    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url": return redirect(str(link.href))
    return render(request, "core/error.html", {"mensaje": "Error en PayPal"})

@login_required
def pago_exitoso(request):
    payer_id = request.GET.get('PayerID')
    payment_id = request.GET.get('paymentId')
    
    certificado, error = gateways.ejecutar_pago_y_certificar(payment_id, payer_id)
    if error: return render(request, "core/error.html", {"mensaje": f"Error: {error}"})
    return redirect('perfil_usuario')

@login_required
def pago_cancelado(request):
    return render(request, 'core/pago_cancelado.html')