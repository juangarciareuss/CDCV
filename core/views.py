import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from core.models import Curso, Examen, Certificado, Pregunta, Tema 
from core.logic import engine, gateways, analytics
from core.logic.ai_services import CDCVOrchestrator


def homepage(request):
    # Usamos la lógica de analítica para las estadísticas
    cursos = Curso.objects.filter(estructura_examen__isnull=False, activo=True).order_by('nivel')
    context = {"cursos": cursos, **analytics.obtener_stats_comerciales()}
    return render(request, "core/homepage.html", context)

@login_required
def perfil_usuario(request):
    return render(request, 'core/perfil.html', {
        'examenes': Examen.objects.filter(usuario=request.user).order_by('-fecha'),
        'certificados': Certificado.objects.filter(usuario=request.user).order_by('-fecha_emision')
    })

@login_required 
def examen(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    session_key = f'examen_set_{curso_id}'
    
    if request.method == "GET":
        if session_key not in request.session:
            # Llamamos al motor de "Rayos X"
            preguntas, error = engine.diagnosticar_y_pescar_preguntas(curso)
            if error: return render(request, "core/error.html", {"mensaje": error})
            request.session[session_key] = [p.id for p in preguntas]
        
        ids = request.session[session_key]
        # Ahora Pregunta ya está importado correctamente
        preguntas_set = list(Pregunta.objects.filter(id__in=ids))
        preguntas_set.sort(key=lambda x: ids.index(x.id))
        return render(request, "core/examen.html", {'curso': curso, 'preguntas': preguntas_set})

    if request.method == "POST":
        ids = request.session.get(session_key)
        if not ids: return render(request, "core/error.html", {"mensaje": "Sesión expirada."})
        
        respuestas = {k: v for k, v in request.POST.items() if k.startswith('pregunta_')}
        # El motor procesa los resultados
        data, error = engine.finalizar_examen(request.user, curso, ids, respuestas)
        
        if session_key in request.session: del request.session[session_key]
        return render(request, "core/examen.html", {'curso': curso, **data})

# --- GESTIÓN DE KPIS (NUEVA VISTA) ---
@login_required
def dashboard_kpi(request):
    if not request.user.is_staff: 
        return redirect('core:homepage')
    
    # Obtenemos los datos desde nuestro módulo de analítica
    data = analytics.obtener_diagnostico_completo()
    return render(request, "core/dashboard.html", data)

# --- PASARELA DE PAGOS ---
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
    return redirect('core:verificar_certificado', codigo_verificacion=certificado.codigo_verificacion)

@login_required
def pago_cancelado(request):
    return render(request, 'core/pago_cancelado.html')

def verificar_certificado(request, codigo_verificacion):
    certificado = get_object_or_404(Certificado, codigo_verificacion=codigo_verificacion)
    return render(request, 'core/verificacion.html', {'certificado': certificado})

# --- ENDPOINTS DE IA (NUEVO) ---
@login_required
def endpoint_curar_con_ia(request, curso_id):
    """
    Recibe la petición del Dashboard para reparar un curso roto.
    """
    # Seguridad: Solo staff puede gastar tokens de IA
    if not request.user.is_staff:
        return JsonResponse({"status": "error", "message": "Acceso denegado"}, status=403)
    
    try:
        # 1. Llamamos al Orquestador
        orchestrator = CDCVOrchestrator()
        
        # 2. Ejecutamos la curación
        # Esto llamará internamente al RefillerAgent para crear preguntas
        resultado = orchestrator.curar_curso_roto(curso_id)
        
        # 3. Devolvemos el reporte al frontend
        return JsonResponse(resultado)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
@login_required
def endpoint_crear_curso_ia(request):
    """
    Recibe un POST con el tema (ej: 'Excel Avanzado') y crea el curso desde cero.
    """
    if not request.user.is_staff:
        return JsonResponse({"status": "error", "message": "Acceso denegado"}, status=403)
    
    if request.method == "POST":
        try:
            # Obtenemos el dato que envía el Javascript
            data = json.loads(request.body)
            nicho = data.get('nicho')

            if not nicho:
                return JsonResponse({"status": "error", "message": "Falta el nicho"})

            # --- LLAMADA AL ORQUESTADOR ---
            orchestrator = CDCVOrchestrator()
            mensaje = orchestrator.crear_nuevo_producto(nicho) # <--- Aquí trabaja el Builder
            
            return JsonResponse({"status": "success", "message": mensaje})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

@login_required
def toggle_estado_curso(request, curso_id):
    """Cambia el curso de Activo (1) a Inactivo (0) y viceversa"""
    if not request.user.is_staff:
        return JsonResponse({"status": "error"}, status=403)
    
    curso = get_object_or_404(Curso, id=curso_id)
    curso.activo = not curso.activo # Invierte el valor actual
    curso.save()
    
    return JsonResponse({
        "status": "success", 
        "nuevo_estado": curso.activo,
        "mensaje": "Curso ACTIVADO" if curso.activo else "Curso DESACTIVADO"
    })