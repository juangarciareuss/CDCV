# core/logic/gateways.py
import paypalrestsdk
from django.urls import reverse
from django.conf import settings
from core.models import Examen, Certificado
from core.utils import generar_certificado_pdf

def preparar_pago_paypal(request, examen):
    """
    Crea la intención de pago en PayPal con el precio REAL del curso.
    """
    # 1. Obtener precio dinámico y convertir a string con 2 decimales
    # Esto evita errores si el precio es 19.9900002 o float.
    precio_real = examen.curso.precio_usd
    precio_str = "{:.2f}".format(precio_real)

    # 2. Construir el objeto de pago
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            # Construimos las URLs completas (https://...) para que PayPal sepa dónde volver
            "return_url": request.build_absolute_uri(reverse('core:pago_exitoso')),
            "cancel_url": request.build_absolute_uri(reverse('core:pago_cancelado'))
        },
        "transactions": [{
            # Detalle del producto (Item List)
            "item_list": {
                "items": [{
                    "name": f"Certificación: {examen.curso.nombre}",
                    "sku": f"CDCV-{examen.id}",
                    "price": precio_str,     # <--- PRECIO DINÁMICO CORREGIDO
                    "currency": "USD",
                    "quantity": 1
                }]
            },
            # Monto total a cobrar (Debe coincidir con la suma de items)
            "amount": {
                "total": precio_str,         # <--- TOTAL DINÁMICO CORREGIDO
                "currency": "USD"
            },
            "description": f"Emisión de certificado para el examen {examen.id} del usuario {examen.usuario.username}.",
            "custom": str(examen.id) # Guardamos el ID del examen para recuperarlo al volver
        }]
    })

    return payment

def ejecutar_pago_y_certificar(payment_id, payer_id):
    """Ejecuta el pago y genera el PDF."""
    payment = paypalrestsdk.Payment.find(payment_id)
    if payment.execute({"payer_id": payer_id}):
        examen_id = int(payment.transactions[0].custom)
        examen = Examen.objects.get(id=examen_id)
        certificado = generar_certificado_pdf(examen)
        return certificado, None
    return None, payment.error