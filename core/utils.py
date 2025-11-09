# core/utils.py

import random, os, uuid
from io import BytesIO
from .models import Pregunta, Certificado, Examen 

from django.core.files.base import ContentFile
from django.conf import settings

# --- Librerías de PDF y QR ---
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch


def generar_sets_examen(curso_id, num_sets=3, preguntas_por_set=3):
    """
    Obtiene TODOS los IDs de preguntas de un curso y genera 'num_sets'
    listas aleatorias de IDs de preguntas.
    """
    print(f"Buscando IDs para curso: {curso_id}")
    try:
        # --- ESTA ES LA LÍNEA CORREGIDA ---
        # Usamos values_list para obtener solo los IDs (números)
        banco_ids = list(Pregunta.objects.filter(curso_id=curso_id).values_list('id', flat=True))
        
        if len(banco_ids) < preguntas_por_set:
            print(f"Error: No hay suficientes preguntas. Se necesitan {preguntas_por_set}, se encontraron {len(banco_ids)}")
            return []
        
        exam_sets_ids = []
        for _ in range(num_sets):
            # random.sample ahora trabaja sobre una lista de números
            set_ids = random.sample(banco_ids, preguntas_por_set)
            exam_sets_ids.append(set_ids)
            
        print(f"Sets generados: {exam_sets_ids}")
        return exam_sets_ids
        
    except Exception as e:
        print(f"Error al generar sets de examen: {e}")
        return []


def calcular_resultados(respuestas_usuario, preguntas_set):
    """
    Compara las respuestas del usuario con las preguntas correctas.
    'preguntas_set' es una lista de OBJETOS Pregunta.
    """
    resultados = []
    total_correctas = 0
    total_preguntas = len(preguntas_set)

    for p in preguntas_set:
        id_pregunta_str = f'pregunta_{p.id}'
        respuesta_usr = respuestas_usuario.get(id_pregunta_str, 'N/A')
        es_correcta = (respuesta_usr == p.respuesta_correcta)
        
        justificacion = "Respuesta incorrecta."
        if es_correcta:
            total_correctas += 1
            justificacion = p.opciones.get(p.respuesta_correcta, {}).get('justificacion', 'Respuesta correcta.')
        else:
            justificacion_opcion_marcada = p.opciones.get(respuesta_usr, {}).get('justificacion')
            if justificacion_opcion_marcada:
                justificacion = justificacion_opcion_marcada
            elif not p.opciones.get(respuesta_usr):
                justificacion = "Opción no válida o sin respuesta."

        resultados.append({
            'pregunta': p.texto,
            'respuesta_usuario': f"{respuesta_usr}. {p.opciones.get(respuesta_usr, {}).get('texto', 'Sin respuesta')}",
            'correcta': es_correcta,
            'justificacion': justificacion
        })

    porcentaje = (total_correctas / total_preguntas) * 100 if total_preguntas > 0 else 0
    return resultados, round(porcentaje, 2), total_correctas, total_preguntas


def generar_certificado_pdf(examen):
    """
    Genera un Certificado (con PDF y QR) para un Examen aprobado.
    """
    print(f"Iniciando generación de certificado para Examen ID: {examen.id}...")
    
    certificado, created = Certificado.objects.get_or_create(
        examen=examen,
        defaults={
            'usuario': examen.usuario,
            'curso': examen.curso,
        }
    )
    
    if not created and certificado.archivo_pdf:
        print(f"Certificado para Examen ID: {examen.id} ya existía.")
        return certificado

    # TODO: Cambia 'tu-dominio.com' por '127.0.0.1:8000' para pruebas locales
    url_verificacion = f"http://127.0.0.1:8000/verificar/{certificado.codigo_verificacion}/"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url_verificacion)
    qr.make(fit=True)
    qr_img = qr.make_image(fill='black', back_color='white')
    
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_filename = f'qr_{certificado.codigo_verificacion}.png'
    certificado.codigo_qr.save(qr_filename, ContentFile(qr_buffer.getvalue()), save=True)
    print(f"Código QR guardado en: {certificado.codigo_qr.path}")

    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter 

    try:
        # Verifica que esta ruta sea correcta
        ruta_plantilla = os.path.join(settings.MEDIA_ROOT, 'plantillas', 'plantilla.png') 
        c.drawImage(ruta_plantilla, 0, 0, width=width, height=height, preserveAspectRatio=True, anchor='c')
    except Exception as e:
        print(f"ADVERTENCIA: No se encontró plantilla.PDF en blanco. Error: {e}")
        c.drawString(inch, height - inch, "Certificado (Sin Plantilla)")

    # Ajusta estas coordenadas
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2.0, height / 2.0 + 50, f"{examen.usuario.first_name} {examen.usuario.last_name}")
    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2.0, height / 2.0 + 10, "ha completado exitosamente la certificación de:")
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2.0, height / 2.0 - 30, examen.curso.nombre)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2.0, height / 2.0 - 80, f"Emitido el: {certificado.fecha_emision.strftime('%d/%m/%Y')}")
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(inch, inch, f"ID Verificación: {certificado.codigo_verificacion}")

    qr_path_en_disco = certificado.codigo_qr.path
    c.drawImage(qr_path_en_disco, width - 2 * inch, inch, width=1.5*inch, height=1.5*inch)

    c.showPage()
    c.save()

    pdf_filename = f'cert_{certificado.codigo_verificacion}.pdf'
    certificado.archivo_pdf.save(pdf_filename, ContentFile(pdf_buffer.getvalue()), save=True)
    print(f"Certificado PDF guardado en: {certificado.archivo_pdf.path}")

    return certificado