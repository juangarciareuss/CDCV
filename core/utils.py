# core/utils.py

import random, os, uuid
from io import BytesIO
# AÑADIMOS: Curso y Tema para la nueva lógica de generación
from .models import Pregunta, Certificado, Examen, Curso, Tema 

from django.core.files.base import ContentFile
from django.conf import settings

# --- Librerías de PDF y QR ---
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch


# --- FUNCIÓN REFACTORIZADA (SPRINT 5) ---
def generar_sets_examen(curso_id, num_sets=3):
    """
    Genera 'num_sets' de IDs de preguntas basándose en la 'receta'
    definida en el campo JSON 'estructura_examen' del Curso.
    """
    print(f"Iniciando generación de sets para Curso ID: {curso_id} usando la nueva estructura robusta.")
    
    try:
        curso = Curso.objects.get(id=curso_id)
        
        # 1. Validar la "receta" (estructura_examen)
        receta = curso.estructura_examen
        if not receta or 'reglas_seleccion' not in receta or 'total_preguntas' not in receta:
            print(f"Error: El Curso ID {curso_id} no tiene una 'estructura_examen' (receta) válida.")
            return []

        reglas = receta.get('reglas_seleccion', [])
        total_preguntas_requeridas = receta.get('total_preguntas', 0)
        
        banco_ids_final = set() # Usamos un set para evitar duplicados si una pregunta cumple múltiples reglas

        # 2. Iterar sobre cada regla de la receta y construir el banco de preguntas
        for regla in reglas:
            try:
                # Obtenemos los IDs de los temas (tags)
                # La receta puede usar 'tema_id' o 'tema_nombre'
                tema_obj = None
                if 'tema_id' in regla:
                    tema_obj = Tema.objects.get(id=regla['tema_id'])
                elif 'tema_nombre' in regla:
                    tema_obj = Tema.objects.get(nombre=regla['tema_nombre'])
                else:
                    raise KeyError("La regla debe contener 'tema_id' o 'tema_nombre'")

                dificultad_min = regla.get('dificultad_min', 1) # Default 1
                dificultad_max = regla.get('dificultad_max', 5) # Default 5
                cantidad = regla['cantidad']
                
                # Buscamos IDs de preguntas que cumplan TODOS los criterios
                ids_encontrados = list(Pregunta.objects.filter(
                    temas=tema_obj, # Filtra por el Tag (Tema)
                    dificultad__gte=dificultad_min, # Filtra por dificultad
                    dificultad__lte=dificultad_max
                ).values_list('id', flat=True))
                
                if len(ids_encontrados) < cantidad:
                    print(f"Advertencia: No hay suficientes preguntas para la regla '{tema_obj.nombre}' (Dificultad {dificultad_min}-{dificultad_max}). Se necesitan {cantidad}, se encontraron {len(ids_encontrados)}.")
                    # Si faltan, añadimos las que hay
                    banco_ids_final.update(ids_encontrados)
                else:
                    # Si sobran, seleccionamos aleatoriamente la cantidad exacta
                    banco_ids_final.update(random.sample(ids_encontrados, cantidad))

            except Tema.DoesNotExist:
                print(f"Error en la receta: El Tema (Tag) '{regla.get('tema_nombre') or regla.get('tema_id')}' no existe en la DB.")
                continue
            except KeyError as e:
                print(f"Error en la receta: Falta la llave {e} en una de las reglas.")
                continue

        # 3. Validar el banco final y generar los sets
        banco_ids_list = list(banco_ids_final)
        
        if len(banco_ids_list) < total_preguntas_requeridas:
            print(f"Error: No se pudo construir un examen completo. Se requieren {total_preguntas_requeridas} preguntas, pero solo se recolectaron {len(banco_ids_list)} preguntas únicas que cumplen las reglas.")
            return []
        
        exam_sets_ids = []
        for _ in range(num_sets):
            # Seleccionamos aleatoriamente del banco final
            # Nos aseguramos de no pedir más preguntas de las que tenemos
            k = min(total_preguntas_requeridas, len(banco_ids_list))
            set_ids = random.sample(banco_ids_list, k)
            exam_sets_ids.append(set_ids)
            
        print(f"Sets generados (basados en 'estructura_examen'): {exam_sets_ids}")
        return exam_sets_ids
        
    except Curso.DoesNotExist:
        print(f"Error fatal: El Curso ID {curso_id} no existe.")
        return []
    except Exception as e:
        print(f"Error inesperado al generar sets de examen: {e}")
        return []


def calcular_resultados(respuestas_usuario, preguntas_set):
    """
    (Esta función no necesita cambios, ya que opera sobre el objeto Pregunta)
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
    (Esta función no necesita cambios)
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