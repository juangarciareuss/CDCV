# core/logic/gateways.py
import paypalrestsdk
from django.urls import reverse
from core.models import Examen, Certificado
from core.utils import generar_certificado_pdf

def preparar_pago_paypal(request, examen):
    """Configura el objeto de pago de PayPal."""
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
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
            "amount": {"total": "5.00", "currency": "USD"},
            "description": f"Emisión de certificado para el examen ID {examen.id}.",
            "custom": str(examen.id)
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