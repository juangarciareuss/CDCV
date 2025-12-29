import io
import os
import base64
import json
import qrcode
from django.db.models import Q
from django.db.models import Count
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from core.models import Curso

# 👇 AGREGAMOS MicroCompetencia AQUI
from core.models import Curso, Examen, Certificado, InsigniaUsuario, MicroCompetencia
#from core.logic import analytics
from agents.ai_services import CDCVOrchestrator

# --- PÚBLICO (VITRINA COMERCIAL) ---
def homepage(request):
    """
    Portada Comercial Renovada ($300K Look)
    """
    
    # A. LOS PRODUCTOS (SOLO ACTIVOS)
    # 🔴 CORRECCIÓN: Usamos .filter(activo=True) en lugar de .all()
    # Esto hace que si desmarcas el tic "Activo" en el admin (o lo borras), desaparezca de aquí.
    cursos = Curso.objects.filter(activo=True).order_by('nivel')

    # B. EL GANCHO (Micro-Competencias)
    try:
        retos = MicroCompetencia.objects.annotate(
            num_preguntas=Count('preguntas_banco')
        ).filter(num_preguntas__gte=3).order_by('?')[:6]
    except Exception:
        # Si falla (ej: tabla no existe aún), mostramos lista vacía
        retos = []

    # C. ESTADÍSTICAS (CON IMPORTACIÓN TARDÍA Y SEGURA)
    try:
        # 1. Intentamos importar el archivo AQUÍ dentro
        from core.logic import analytics
        
        # 2. Si importa bien, pedimos los datos
        stats = analytics.obtener_stats_comerciales()
        
    except Exception as e:
        # 3. Si falla CUALQUIER cosa (No existe archivo, falta __init__, DB vacía, etc.)
        print(f"⚠️ Aviso: No se pudieron cargar las stats: {e}")
        stats = {
            "total_cursos": 0,
            "total_examenes": 0,
            "total_certificados": 0
        }

    context = {
        "cursos": cursos,
        "retos": retos,
        **stats
    }
    return render(request, "core/homepage.html", context)


# --- ÁREA PRIVADA ---
@login_required
def perfil_usuario(request):
    """
    Muestra el portafolio del usuario:
    1. Medallero (Insignias de micro-competencias ganadas).
    2. Certificaciones Oficiales (Diplomas de cursos).
    """
    # 1. Insignias (Gamificación)
    insignias = InsigniaUsuario.objects.filter(
        usuario=request.user
    ).select_related('competencia').order_by('-fecha_obtenida')

    # 2. Certificados (Diplomas Oficiales)
    certificados = Certificado.objects.filter(
        usuario=request.user
    ).order_by('-fecha_emision')

    return render(request, 'core/perfil_usuario.html', {
        'usuario': request.user,
        'insignias': insignias,
        'certificaciones': certificados,
        # Agregamos contadores simples por si el template los necesita directo
        'examenes': Examen.objects.filter(usuario=request.user).order_by('-fecha') 
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
    
    # IMPORTACIÓN TARDÍA
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
    # OJO: Si quieres que cualquiera use el buscador, comenta o borra la siguiente línea.
    # Si la dejas, solo tú (staff) podrás usar el buscador del home.
    # if not request.user.is_staff: return JsonResponse({"status": "error", "message": "No autorizado"}, status=403)

    if request.method == "POST":
        try:
            # CORRECCIÓN 1: Intentamos leer primero del formulario HTML normal
            # En tu HTML el input se llama 'tema', así que lo buscamos así:
            nicho = request.POST.get('tema')

            # CORRECCIÓN 2: Si viene vacío, intentamos leer JSON (por si usas Postman/API)
            if not nicho and request.body:
                try:
                    data = json.loads(request.body)
                    nicho = data.get('nicho')
                except:
                    pass # Si falla el JSON, simplemente seguimos

            if not nicho:
                return JsonResponse({"status": "error", "message": "Debes escribir un tema para buscar."}, status=400)

            # Ejecutamos el orquestador
            orchestrator = CDCVOrchestrator()
            mensaje = orchestrator.crear_nuevo_producto(nicho)
            
            # NOTA DE UX: Como esto viene de un formulario HTML, devolver un JSON 
            # mostrará un texto feo en el navegador del usuario. 
            # Idealmente deberías redirigir a la página del curso creado, 
            # pero por ahora dejemos que funcione la lógica.
            return JsonResponse({"status": "success", "message": mensaje})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

@login_required
def endpoint_curar_con_ia(request, curso_id):
    return JsonResponse({"status": "warning", "message": "Usa el nuevo dashboard"})

@login_required
def guardar_nombre_legal(request):
    """
    Vista auxiliar para guardar Nombre y Apellido si el usuario no los tiene,
    necesario para emitir certificados válidos.
    """
    if request.method == "POST":
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        if first_name and last_name:
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()
            messages.success(request, "✅ Datos actualizados. Tu certificado está listo.")
        else:
            messages.error(request, "⚠️ Debes ingresar nombre y apellido para el certificado.")
    
    # Redirigir a la página desde donde vino (probablemente resultados del examen)
    return redirect(request.META.get('HTTP_REFERER', '/'))

def buscar_cursos(request):
    query = request.GET.get('tema', '') # Obtenemos lo que escribió el usuario
    resultados = []

    if query:
        # Filtramos: Busca si el nombre O la descripción contienen el texto
        resultados = Curso.objects.filter(
            Q(nombre__icontains=query) | 
            Q(descripcion__icontains=query)
        ).distinct()

    context = {
        'query': query,
        'cursos': resultados
    }
    # Reutilizamos tu template de inicio o uno nuevo de resultados
    return render(request, 'core/resultados_busqueda.html', context)