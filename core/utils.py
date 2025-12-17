import random
import uuid
import os
from io import BytesIO
from .models import Pregunta, Certificado, Examen, Curso, Tema

from django.core.files.base import ContentFile
from django.conf import settings

# --- Librerías de PDF y QR ---
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch


def generar_sets_examen(curso_id, num_sets=3, preguntas_por_set=10):
    """
    Genera sets de examen. Intenta usar la 'receta' avanzada si existe,
    si no, usa la lógica simple de compatibilidad.
    """
    print(f"Buscando preguntas para curso ID: {curso_id}")
    try:
        curso = Curso.objects.get(id=curso_id)
        
        # 1. LÓGICA AVANZADA (Si hay receta en estructura_examen)
        if curso.estructura_examen and 'reglas' in curso.estructura_examen:
            # (Aquí iría la lógica compleja de tu sprint 5 para filtrar por tags/dificultad)
            # Por ahora, para mantener la estabilidad del MVP, usamos un fallback inteligente
            # que podrías expandir luego.
            pass 

        # 2. LÓGICA ESTÁNDAR (Fallback robusto para MVP)
        # Busca preguntas vinculadas directamente al curso
        banco_ids = list(Pregunta.objects.filter(curso_id=curso_id).values_list('id', flat=True))
        
        if len(banco_ids) < preguntas_por_set:
            print(f"Error: No hay suficientes preguntas. Se necesitan {preguntas_por_set}, se encontraron {len(banco_ids)}")
            return []
        
        exam_sets_ids = []
        for _ in range(num_sets):
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
    """
    resultados = []
    total_correctas = 0
    total_preguntas = len(preguntas_set)

    for p in preguntas_set:
        id_str = f'pregunta_{p.id}'
        respuesta_usr = respuestas_usuario.get(id_str, 'N/A')
        es_correcta = (respuesta_usr == p.respuesta_correcta)
        
        justificacion = "Respuesta incorrecta."
        if es_correcta:
            total_correctas += 1
            justificacion = p.opciones.get(p.respuesta_correcta, {}).get('justificacion', '')
        else:
            justificacion = p.opciones.get(respuesta_usr, {}).get('justificacion', '')

        resultados.append({
            'pregunta': p.texto,
            'respuesta_usuario': f"{respuesta_usr}",
            'correcta': es_correcta,
            'justificacion': justificacion
        })

    porcentaje = (total_correctas / total_preguntas) * 100 if total_preguntas > 0 else 0
    return resultados, round(porcentaje, 2), total_correctas, total_preguntas


def generar_certificado_pdf(examen):
    """
    Genera el PDF y QR.
    CORREGIDO: Manejo de nombres vacíos, dominio dinámico y persistencia.
    """
    print(f"Iniciando generación de certificado para Examen ID: {examen.id}...")
    
    # Generamos UUID manualmente
    nuevo_uuid = uuid.uuid4()
    
    certificado, created = Certificado.objects.get_or_create(
        examen=examen,
        defaults={
            'usuario': examen.usuario,
            'curso': examen.curso,
            'codigo_verificacion': nuevo_uuid
        }
    )
    
    if not created and certificado.archivo_pdf:
        print("Certificado ya existía.")
        return certificado

    # --- ARREGLO 1: Dominio Dinámico para el QR ---
    # Si estamos en producción (Render), usa el dominio real. Si es local, usa localhost.
    if settings.DEBUG:
        domain = "http://127.0.0.1:8000"
    else:
        domain = "https://cdcv.onrender.com"  # <--- Tu dominio real
        
    url_verificacion = f"{domain}/verificar/{certificado.codigo_verificacion}/"
    
    # 1. Generar QR
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url_verificacion)
    qr.make(fit=True)
    qr_img = qr.make_image(fill='black', back_color='white')
    
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_filename = f'qr_{certificado.codigo_verificacion}.png'
    
    # save=False evita el guardado prematuro
    certificado.codigo_qr.save(qr_filename, ContentFile(qr_buffer.getvalue()), save=False)

    # 2. Generar PDF
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter 

    try:
        # Intenta cargar plantilla
        ruta_plantilla = os.path.join(settings.MEDIA_ROOT, 'plantillas', 'plantilla.png')
        if os.path.exists(ruta_plantilla):
            c.drawImage(ruta_plantilla, 0, 0, width=width, height=height, preserveAspectRatio=True, anchor='c')
        else:
            # Fallback visual si no hay imagen de fondo
            c.drawString(inch, height - inch, "CERTIFICADO OFICIAL CDCV")
            c.line(inch, height - inch - 10, width - inch, height - inch - 10)
    except Exception:
        pass

    # --- ARREGLO 2: Nombre del Usuario ---
    # Construimos el nombre. Si está vacío, usamos el username para que nunca salga en blanco.
    nombre_completo = f"{examen.usuario.first_name} {examen.usuario.last_name}".strip()
    if not nombre_completo:
        nombre_completo = examen.usuario.username.upper() # Fallback seguro
    else:
        nombre_completo = nombre_completo.upper()

    # Contenido del PDF
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2.0, height / 2.0 + 50, nombre_completo) # <--- Variable corregida
    
    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2.0, height / 2.0 + 10, "ha completado exitosamente la certificación de:")
    
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2.0, height / 2.0 - 30, examen.curso.nombre)
    
    c.setFont("Helvetica", 12)
    # Formato de fecha legible
    fecha_str = certificado.fecha_emision.strftime('%d/%m/%Y')
    c.drawCentredString(width / 2.0, height / 2.0 - 80, f"Emitido el: {fecha_str}")
    
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(inch, inch, f"ID Verificación: {certificado.codigo_verificacion}")

    # Incrustar QR
    try:
        # Usamos un archivo temporal seguro para el QR
        qr_temp_path = os.path.join(settings.MEDIA_ROOT, 'temp_qr.png')
        with open(qr_temp_path, 'wb') as f:
            f.write(qr_buffer.getvalue())
        c.drawImage(qr_temp_path, width - 2.5 * inch, inch, width=1.5*inch, height=1.5*inch)
    except Exception as e:
        print(f"No se pudo dibujar QR en PDF: {e}")

    c.showPage()
    c.save()

    pdf_filename = f'cert_{certificado.codigo_verificacion}.pdf'
    
    # Guardamos el archivo PDF (save=False)
    certificado.archivo_pdf.save(pdf_filename, ContentFile(pdf_buffer.getvalue()), save=False)
    
    # GUARDADO FINAL
    certificado.save()
    
    print("Certificado generado y guardado correctamente.")
    return certificado