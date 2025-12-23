import json
import os
import io
import base64
import random  # <--- AGREGADO
import qrcode
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

from core.models import Curso, Examen, Certificado, Pregunta, Tema 
from core.logic import engine, gateways, analytics
from core.logic.ai_services import CDCVOrchestrator


def homepage(request):
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

@login_required
def dashboard_kpi(request):
    if not request.user.is_staff: 
        return redirect('core:homepage')
    data = analytics.obtener_diagnostico_completo()
    return render(request, "core/dashboard.html", data)

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
    
    # Redirige al perfil para ver el certificado nuevo
    return redirect('core:perfil_usuario')

@login_required
def pago_cancelado(request):
    return render(request, 'core/pago_cancelado.html')

def verificar_certificado(request, codigo_verificacion):
    certificado = get_object_or_404(Certificado, codigo_verificacion=codigo_verificacion)
    return render(request, 'core/verificacion.html', {'certificado': certificado})

@login_required
def endpoint_curar_con_ia(request, curso_id):
    if not request.user.is_staff:
        return JsonResponse({"status": "error", "message": "Acceso denegado"}, status=403)
    try:
        orchestrator = CDCVOrchestrator()
        resultado = orchestrator.curar_curso_roto(curso_id)
        return JsonResponse(resultado)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
@login_required
def endpoint_crear_curso_ia(request):
    if not request.user.is_staff:
        return JsonResponse({"status": "error", "message": "Acceso denegado"}, status=403)
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nicho = data.get('nicho')
            if not nicho: return JsonResponse({"status": "error", "message": "Falta el nicho"})

            orchestrator = CDCVOrchestrator()
            mensaje = orchestrator.crear_nuevo_producto(nicho)
            return JsonResponse({"status": "success", "message": mensaje})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

@login_required
def toggle_estado_curso(request, curso_id):
    if not request.user.is_staff: return JsonResponse({"status": "error"}, status=403)
    curso = get_object_or_404(Curso, id=curso_id)
    curso.activo = not curso.activo
    curso.save()
    return JsonResponse({"status": "success", "nuevo_estado": curso.activo})

@login_required
def eliminar_curso(request, curso_id):
    if not request.user.is_staff: return JsonResponse({"status": "error"}, status=403)
    if request.method == "POST":
        curso = get_object_or_404(Curso, id=curso_id)
        curso.delete() 
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=405)

# --- GENERADOR DE PDF ---
# --- GENERADOR DE PDF PREMIUM (Versión Definitiva con Logo Incrustado) ---
@login_required
def generar_pdf_certificado(request, codigo):
    # 1. Buscar certificado
    certificado = get_object_or_404(Certificado, codigo_verificacion=codigo)
    
    # 2. Generar QR en memoria
    url_validacion = request.build_absolute_uri(f'/verificar/{certificado.codigo_verificacion}/')
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url_validacion)
    qr.make(fit=True)
    img_qr = qr.make_image(fill='black', back_color='white')
    
    buffer = io.BytesIO()
    img_qr.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    # 3. PROCESAR LOGO (El paso nuevo para que salga la foto)
    # Definimos la ruta exacta donde guardaste tu logo
    logo_file_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'core', 'img', 'logo_reducido.png')
    
    logo_b64 = ""
    try:
        with open(logo_file_path, "rb") as image_file:
            logo_b64 = base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        print(f"ERROR: No encontré el logo en {logo_file_path}")
        # Si no encuentra el logo, no se rompe, solo sale sin foto.

    # 4. Contexto para el HTML
    context = {
        'certificado': certificado,
        'qr_b64': qr_b64,     # El QR
        'logo_b64': logo_b64, # <--- LA FOTO DEL LOGO ENVIADA COMO CÓDIGO
    }

    # 5. Renderizar HTML
    html_string = render_to_string('core/certificate_pdf.html', context)
    
    # 6. Convertir a PDF
    response = HttpResponse(content_type='application/pdf')
    filename = f"Certificado_{certificado.codigo_verificacion}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    
    return response