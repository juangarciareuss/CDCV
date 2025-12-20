import random
import uuid
import os
import logging
from io import BytesIO

# Imports de Django
from django.core.files.base import ContentFile
from django.conf import settings

# Imports de Modelos (Asegúrate de que la ruta sea correcta)
from .models import Pregunta, Certificado, Examen, Curso

# --- Librerías de PDF y QR ---
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# Configuración de logger para debugging
logger = logging.getLogger(__name__)

def generar_sets_examen(curso_id, num_sets=3, preguntas_por_set=10):
    """
    Genera sets de examen seleccionando preguntas aleatorias del curso.
    """
    print(f"Buscando preguntas para curso ID: {curso_id}")
    try:
        # 1. LÓGICA ESTÁNDAR (Fallback robusto para MVP)
        # Busca preguntas vinculadas directamente al curso
        banco_ids = list(Pregunta.objects.filter(curso_id=curso_id).values_list('id', flat=True))
        
        # Validación de stock de preguntas
        if len(banco_ids) < preguntas_por_set:
            print(f"Error: No hay suficientes preguntas. Se necesitan {preguntas_por_set}, se encontraron {len(banco_ids)}")
            return []
        
        # Generación de combinaciones aleatorias
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
    Versión blindada: Funciona con diccionarios Y con texto simple.
    Arregla el error 'str object has no attribute get'.
    """
    resultados = []
    total_correctas = 0
    total_preguntas = len(preguntas_set)

    for p in preguntas_set:
        id_str = f'pregunta_{p.id}'
        
        # 1. Obtenemos la letra que eligió el usuario (A, B, C...)
        respuesta_usr = respuestas_usuario.get(id_str, 'N/A')
        
        # 2. Verificar si es correcta
        es_correcta = (respuesta_usr == p.respuesta_correcta)
        
        if es_correcta:
            total_correctas += 1

        # 3. RECUPERAR DATOS DE LA OPCIÓN (Aquí estaba el error)
        # Obtenemos el dato crudo (puede ser texto o diccionario)
        datos_opcion = p.opciones.get(respuesta_usr, "Opción no encontrada")
        
        texto_respuesta = ""
        justificacion_especifica = ""

        # Lógica Híbrida: ¿Es Diccionario o Texto?
        if isinstance(datos_opcion, dict):
            # Formato complejo (Diccionario)
            texto_respuesta = datos_opcion.get('texto', str(datos_opcion))
            justificacion_especifica = datos_opcion.get('justificacion', '')
        else:
            # Formato simple (Texto) -> Esto soluciona el crash
            texto_respuesta = str(datos_opcion)
            justificacion_especifica = ""

        # 4. Determinar la justificación a mostrar
        # Si la opción no tiene justificación específica, usamos la general de la pregunta
        justificacion_final = justificacion_especifica
        if not justificacion_final:
             justificacion_final = getattr(p, 'justificacion', 'Revisa el material de estudio.')

        # 5. Agregamos al reporte
        resultados.append({
            'pregunta': p,  # Objeto completo para el template
            'respuesta_usuario': {
                'key': respuesta_usr,
                'texto': texto_respuesta
            },
            'correcta': es_correcta,
            'justificacion': justificacion_final
        })

    # Cálculo final
    porcentaje = (total_correctas / total_preguntas) * 100 if total_preguntas > 0 else 0
    
    # Devolvemos los 4 valores exactos que espera tu views.py
    return resultados, round(porcentaje, 2), total_correctas, total_preguntas


def generar_certificado_pdf(examen):
    """
    Genera el PDF y QR.
    Maneja nombres vacíos, dominio dinámico y persistencia.
    """
    print(f"Iniciando generación de certificado para Examen ID: {examen.id}...")
    
    # Generamos UUID manualmente si no existe
    nuevo_uuid = uuid.uuid4()
    
    # Buscamos o creamos el certificado
    certificado, created = Certificado.objects.get_or_create(
        examen=examen,
        defaults={
            'usuario': examen.usuario,
            'curso': examen.curso,
            'codigo_verificacion': nuevo_uuid
        }
    )
    
    # Si ya existe y tiene PDF, lo retornamos (Evita re-generar)
    if not created and certificado.archivo_pdf:
        print("Certificado ya existía.")
        return certificado

    # --- Dominio Dinámico para el QR ---
    if settings.DEBUG:
        domain = "http://127.0.0.1:8000"
    else:
        domain = "https://cdcv.onrender.com"  # Dominio producción
        
    url_verificacion = f"{domain}/verificar/{certificado.codigo_verificacion}/"
    
    # 1. Generar QR
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url_verificacion)
    qr.make(fit=True)
    qr_img = qr.make_image(fill='black', back_color='white')
    
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_filename = f'qr_{certificado.codigo_verificacion}.png'
    
    # Guardar QR (save=False para no commitear todavía)
    certificado.codigo_qr.save(qr_filename, ContentFile(qr_buffer.getvalue()), save=False)

    # 2. Generar PDF con ReportLab
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter 

    try:
        # Intenta cargar plantilla de fondo
        ruta_plantilla = os.path.join(settings.MEDIA_ROOT, 'plantillas', 'plantilla.png')
        if os.path.exists(ruta_plantilla):
            c.drawImage(ruta_plantilla, 0, 0, width=width, height=height, preserveAspectRatio=True, anchor='c')
        else:
            # Fallback visual si no hay imagen
            c.drawString(inch, height - inch, "CERTIFICADO OFICIAL CDCV")
            c.line(inch, height - inch - 10, width - inch, height - inch - 10)
    except Exception as e:
        print(f"Error cargando plantilla: {e}")

    # --- Nombre del Usuario Seguro ---
    nombre_completo = f"{examen.usuario.first_name} {examen.usuario.last_name}".strip()
    if not nombre_completo:
        nombre_completo = examen.usuario.username.upper()
    else:
        nombre_completo = nombre_completo.upper()

    # Contenido del PDF (Textos)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2.0, height / 2.0 + 50, nombre_completo)
    
    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2.0, height / 2.0 + 10, "ha completado exitosamente la certificación de:")
    
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2.0, height / 2.0 - 30, examen.curso.nombre)
    
    c.setFont("Helvetica", 12)
    # Formato de fecha
    if certificado.fecha_emision:
        fecha_str = certificado.fecha_emision.strftime('%d/%m/%Y')
    else:
        # Fallback por si la fecha es None en creación
        from django.utils import timezone
        fecha_str = timezone.now().strftime('%d/%m/%Y')

    c.drawCentredString(width / 2.0, height / 2.0 - 80, f"Emitido el: {fecha_str}")
    
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(inch, inch, f"ID Verificación: {certificado.codigo_verificacion}")

    # Incrustar QR en el PDF
    try:
        qr_temp_path = os.path.join(settings.MEDIA_ROOT, 'temp_qr.png')
        with open(qr_temp_path, 'wb') as f:
            f.write(qr_buffer.getvalue())
        c.drawImage(qr_temp_path, width - 2.5 * inch, inch, width=1.5*inch, height=1.5*inch)
    except Exception as e:
        print(f"No se pudo dibujar QR en PDF: {e}")

    c.showPage()
    c.save()

    pdf_filename = f'cert_{certificado.codigo_verificacion}.pdf'
    
    # Guardamos el archivo PDF final
    certificado.archivo_pdf.save(pdf_filename, ContentFile(pdf_buffer.getvalue()), save=False)
    
    # GUARDADO FINAL EN BD
    certificado.save()
    
    print("Certificado generado y guardado correctamente.")
    return certificado