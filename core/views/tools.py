import io
import os
import base64
import json
import qrcode
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string

from core.models import Curso, Examen, Certificado
from core.logic import analytics
from agents.ai_services import CDCVOrchestrator

# --- PÚBLICO ---
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

def verificar_certificado(request, codigo_verificacion):
    certificado = get_object_or_404(Certificado, codigo_verificacion=codigo_verificacion)
    return render(request, 'core/verificacion.html', {'certificado': certificado})

# --- GENERADOR PDF (SILENCIOSO) ---
@login_required
def generar_pdf_certificado(request, codigo):
    certificado = get_object_or_404(Certificado, codigo_verificacion=codigo)
    
    # QR
    url_validacion = request.build_absolute_uri(f'/verificar/{certificado.codigo_verificacion}/')
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url_validacion)
    qr.make(fit=True)
    img_qr = qr.make_image(fill='black', back_color='white')
    buffer = io.BytesIO()
    img_qr.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    # LOGO
    logo_file_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'core', 'img', 'logo_reducido.png')
    logo_b64 = ""
    try:
        with open(logo_file_path, "rb") as image_file:
            logo_b64 = base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        pass

    context = {'certificado': certificado, 'qr_b64': qr_b64, 'logo_b64': logo_b64}
    html_string = render_to_string('core/certificate_pdf.html', context)
    
    response = HttpResponse(content_type='application/pdf')
    filename = f"Certificado_{certificado.codigo_verificacion}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # IMPORTACIÓN TARDÍA PARA EVITAR RUIDO EN CONSOLA
    from weasyprint import HTML 
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    return response

# --- HERRAMIENTAS STAFF (Legacy y Admin) ---
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

@login_required
def endpoint_crear_curso_ia(request):
    if not request.user.is_staff: return JsonResponse({"status": "error"}, status=403)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nicho = data.get('nicho')
            orchestrator = CDCVOrchestrator()
            mensaje = orchestrator.crear_nuevo_producto(nicho)
            return JsonResponse({"status": "success", "message": mensaje})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error"}, status=405)

@login_required
def endpoint_curar_con_ia(request, curso_id):
    # Endpoint dummy para no romper frontend legacy
    return JsonResponse({"status": "warning", "message": "Usa el nuevo dashboard"})