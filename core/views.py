from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseBadRequest

from .models import Curso, Pregunta, Examen, Certificado, Tema
from .utils import generar_sets_examen, calcular_resultados, generar_certificado_pdf
import random

# Importar PayPal
import paypalrestsdk

# --- VISTA HOMEPAGE ---
def homepage(request):
    cursos = Curso.objects.all()
    return render(request, "core/homepage.html", {
        "cursos": cursos
    })

# --- VISTA PERFIL DE USUARIO ---
@login_required
def perfil_usuario(request):
    # Obtenemos todos los exámenes y certificados del usuario que ha iniciado sesión
    examenes = Examen.objects.filter(usuario=request.user).order_by('-fecha')
    certificados = Certificado.objects.filter(usuario=request.user).order_by('-fecha_emision')
    return render(request, 'core/perfil.html', {
        'examenes': examenes,
        'certificados': certificados
    })

# --- VISTA EXAMEN ---
@login_required 
def examen(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    session_key = f'examen_set_{curso_id}'
    
    # Lógica GET
    if request.method == "GET":
        if session_key not in request.session:
            sets_ids = generar_sets_examen(curso_id, num_sets=3, preguntas_por_set=10) 
            if not sets_ids:
                 return render(request, "core/error.html", {"mensaje": "No hay suficientes preguntas disponibles para este curso."})
            preguntas_ids = random.choice(sets_ids)
            request.session[session_key] = preguntas_ids
        else:
            preguntas_ids = request.session[session_key]

        preguntas_set = list(Pregunta.objects.filter(id__in=preguntas_ids))
        if not preguntas_set:
             if session_key in request.session:
                del request.session[session_key]
             return render(request, "core/error.html", {"mensaje": "Error al cargar las preguntas. Inténtalo de nuevo."})
        preguntas_set.sort(key=lambda x: preguntas_ids.index(x.id))

        return render(request, "core/examen.html", {
            'curso': curso,
            'preguntas': preguntas_set
        })

    # --- Lógica POST ---
    if request.method == "POST":
        preguntas_ids = request.session.get(session_key)
        if not preguntas_ids:
            return render(request, "core/error.html", {"mensaje": "Tu sesión ha expirado. Por favor, inténtalo de nuevo."})
        
        preguntas_set = list(Pregunta.objects.filter(id__in=preguntas_ids))
        preguntas_set.sort(key=lambda x: preguntas_ids.index(x.id))

        respuestas_usuario = {k: v for k, v in request.POST.items() if k.startswith('pregunta_')}
        resultados, porcentaje, total_correctas, total_preguntas = calcular_resultados(respuestas_usuario, preguntas_set)
        
        examen_aprobado = porcentaje >= 80.0
        
        examen_guardado = Examen.objects.create(
            usuario=request.user,
            curso=curso,
            preguntas_set=preguntas_ids,
            respuestas_usuario=respuestas_usuario,
            puntaje=porcentaje,
            aprobado=examen_aprobado
        )

        if session_key in request.session:
            del request.session[session_key]

        return render(request, "core/examen.html", {
            'curso': curso,
            'preguntas': preguntas_set,
            'resultados': resultados,
            'porcentaje': porcentaje,
            'total_correctas': total_correctas,
            'total_preguntas': total_preguntas,
            'examen': examen_guardado
        })

# --- VISTAS DE PAGO (CORREGIDAS) ---

@login_required
def crear_pago_paypal(request, examen_id):
    try:
        examen = get_object_or_404(Examen, id=examen_id)

        # (Chequeos de seguridad)
        if examen.usuario != request.user:
            return HttpResponseBadRequest("No tienes permiso para pagar este examen.")
        if not examen.aprobado:
            return HttpResponseBadRequest("No puedes certificar un examen que no has aprobado.")
        if Certificado.objects.filter(examen=examen).exists():
             return HttpResponseBadRequest("Este examen ya tiene un certificado emitido.")

        # --- INICIO DE CORRECCIÓN (VALIDATION_ERROR) ---
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": request.build_absolute_uri(reverse('core:pago_exitoso')),
                "cancel_url": request.build_absolute_uri(reverse('core:pago_cancelado'))
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": f"Certificación: {examen.curso.nombre}",
                        "sku": f"CDCV-{examen.id}",
                        "price": "5.00",
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": "5.00",
                    "currency": "USD",
                    # --- ¡ESTA ES LA CORRECCIÓN! ---
                    # Añadimos el desglose 'details' que PayPal requiere
                    "details": {
                        "subtotal": "5.00",
                        "tax": "0.00",
                        "shipping": "0.00"
                    }
                    # --- FIN DE LA CORRECCIÓN ---
                },
                "description": f"Emisión de certificado para el examen ID {examen.id}.",
                "custom": str(examen.id)
            }]
        })
        # --- FIN DE CORRECCIÓN ---

        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = str(link.href)
                    return redirect(approval_url) 
        else:
            print(f"Error al crear pago: {payment.error}")
            return render(request, "core/error.html", {"mensaje": f"Error al contactar a PayPal: {payment.error}"})

    except Exception as e:
        print(f"Error en crear_pago_paypal: {str(e)}")
        return render(request, "core/error.html", {"mensaje": f"Error: {str(e)}"})


@login_required
def pago_exitoso(request):
    payer_id = request.GET.get('PayerID')
    payment_id = request.GET.get('paymentId')

    if not payer_id or not payment_id:
        return render(request, "core/error.html", {"mensaje": "No se pudo procesar el pago (faltan PayerID o paymentId)."})

    try:
        payment = paypalrestsdk.Payment.find(payment_id)

        if payment.execute({"payer_id": payer_id}):
            custom_data = payment.transactions[0].custom
            examen_id = int(custom_data)
            examen = get_object_or_404(Examen, id=examen_id)

            if examen.usuario != request.user:
                 return HttpResponseBadRequest("Conflicto de usuario en el pago.")

            certificado = generar_certificado_pdf(examen)

            return redirect('core:verificar_certificado', codigo_verificacion=certificado.codigo_verificacion)

        else:
            print(f"Error al ejecutar pago: {payment.error}")
            return render(request, "core/error.html", {"mensaje": f"Error al ejecutar el pago en PayPal: {payment.error}"})

    except Exception as e:
        print(f"Error en pago_exitoso: {str(e)}")
        return render(request, "core/error.html", {"mensaje": f"Error al procesar el pago: {str(e)}"})


@login_required
def pago_cancelado(request):
    return render(request, 'core/pago_cancelado.html')


# --- VISTA VERIFICACIÓN ---
def verificar_certificado(request, codigo_verificacion):
    certificado = get_object_or_404(Certificado, codigo_verificacion=codigo_verificacion)
    return render(request, 'core/verificacion.html', {
        'certificado': certificado
    })