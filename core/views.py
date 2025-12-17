from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseBadRequest
import sys # <--- IMPORTANTE PARA LOGS

from .models import Curso, Pregunta, Examen, Certificado, Tema
from .utils import generar_sets_examen, calcular_resultados, generar_certificado_pdf 
import random

# Importar PayPal
import paypalrestsdk

def homepage(request):
    cursos_activos = Curso.objects.filter(estructura_examen__isnull=False).order_by('nivel') 
    
    total_cursos = cursos_activos.count()
    total_examenes = Examen.objects.count()
    total_certificados = Certificado.objects.count()

    context = {
        "cursos": cursos_activos,
        "total_cursos": total_cursos,
        "total_examenes": total_examenes,
        "total_certificados": total_certificados
    }
    
    return render(request, "core/homepage.html", context)

@login_required
def perfil_usuario(request):
    examenes = Examen.objects.filter(usuario=request.user).order_by('-fecha')
    certificados = Certificado.objects.filter(usuario=request.user).order_by('-fecha_emision')
    return render(request, 'core/perfil.html', {
        'examenes': examenes,
        'certificados': certificados
    })

# --- VISTA EXAMEN CON DIAGNÓSTICO (RAYOS X) ---
@login_required 
def examen(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    session_key = f'examen_set_{curso_id}'
    
    # Lógica GET
    if request.method == "GET":
        if session_key not in request.session:
            
            # --- INICIO DIAGNÓSTICO ---
            print(f"\n--- DIAGNÓSTICO EXAMEN (Curso: {curso.nombre}) ---", file=sys.stderr)
            
            preguntas_seleccionadas = []
            
            # 1. Validar si hay receta
            if not curso.estructura_examen or 'reglas_seleccion' not in curso.estructura_examen:
                print("ERROR: El curso no tiene 'reglas_seleccion' en su JSON.", file=sys.stderr)
                return render(request, "core/error.html", {"mensaje": "Error de configuración: El curso no tiene receta."})

            # 2. Procesar reglas manualmente para ver dónde falla
            todas_ok = True
            for regla in curso.estructura_examen['reglas_seleccion']:
                tema_nombre = regla.get('tema_nombre')
                cantidad = regla.get('cantidad', 0)
                dif_min = regla.get('dificultad_min', 0)
                dif_max = regla.get('dificultad_max', 10)
                
                print(f"--> Buscando: Tema '{tema_nombre}' | Cantidad: {cantidad} | Dif: {dif_min}-{dif_max}", file=sys.stderr)
                
                # Verificar Tema
                tema_obj = Tema.objects.filter(nombre=tema_nombre).first()
                if not tema_obj:
                    print(f"    FATAL: El tema '{tema_nombre}' NO EXISTE en la base de datos.", file=sys.stderr)
                    # Intentamos buscar parecidos para dar pistas
                    parecidos = Tema.objects.filter(nombre__icontains=tema_nombre[:5])
                    print(f"    ¿Quisiste decir?: {[t.nombre for t in parecidos]}", file=sys.stderr)
                    todas_ok = False
                    break

                # Contar Preguntas
                candidatas = Pregunta.objects.filter(
                    temas=tema_obj,
                    dificultad__gte=dif_min,
                    dificultad__lte=dif_max
                )
                total_encontradas = candidatas.count()
                print(f"    ENCONTRADAS: {total_encontradas} preguntas para este tema.", file=sys.stderr)
                
                if total_encontradas < cantidad:
                    print(f"    ERROR: Faltan preguntas. Pides {cantidad}, tienes {total_encontradas}.", file=sys.stderr)
                    todas_ok = False
                    break
                else:
                    seleccion = list(candidatas.order_by('?')[:cantidad])
                    preguntas_seleccionadas.extend(seleccion)

            if not todas_ok or not preguntas_seleccionadas:
                 print("--- FIN DIAGNÓSTICO: FALLIDO ---", file=sys.stderr)
                 return render(request, "core/error.html", {"mensaje": f"Error Diagnóstico: Revisa los logs de Render. Faltan preguntas para el tema '{tema_nombre}'."})

            # Si todo salió bien en el diagnóstico, guardamos los IDs
            preguntas_ids = [p.id for p in preguntas_seleccionadas]
            request.session[session_key] = preguntas_ids
            print(f"--- FIN DIAGNÓSTICO: ÉXITO ({len(preguntas_ids)} preguntas cargadas) ---", file=sys.stderr)
            # --- FIN DIAGNÓSTICO ---
            
        else:
            preguntas_ids = request.session[session_key]

        preguntas_set = list(Pregunta.objects.filter(id__in=preguntas_ids))
        if not preguntas_set:
             if session_key in request.session:
                del request.session[session_key]
             return render(request, "core/error.html", {"mensaje": "Error al cargar las preguntas. Inténtalo de nuevo."})
        
        # Ordenamos las preguntas según el ID guardado en la sesión
        preguntas_set.sort(key=lambda x: preguntas_ids.index(x.id))

        return render(request, "core/examen.html", {
            'curso': curso,
            'preguntas': preguntas_set
        })

    # --- Lógica POST (Sin cambios) ---
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

# --- VISTAS DE PAGO ---

@login_required
def crear_pago_paypal(request, examen_id):
    try:
        examen = get_object_or_404(Examen, id=examen_id)

        if examen.usuario != request.user:
            return HttpResponseBadRequest("No tienes permiso para pagar este examen.")
        if not examen.aprobado:
            return HttpResponseBadRequest("No puedes certificar un examen que no has aprobado.")
        if Certificado.objects.filter(examen=examen).exists():
             return HttpResponseBadRequest("Este examen ya tiene un certificado emitido.")

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
                    "details": {
                        "subtotal": "5.00",
                        "tax": "0.00",
                        "shipping": "0.00"
                    }
                },
                "description": f"Emisión de certificado para el examen ID {examen.id}.",
                "custom": str(examen.id)
            }]
        })

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


def verificar_certificado(request, codigo_verificacion):
    certificado = get_object_or_404(Certificado, codigo_verificacion=codigo_verificacion)
    return render(request, 'core/verificacion.html', {
        'certificado': certificado
    })