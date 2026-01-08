import sys
import random
from django.db.models import Q
from core.models import Tema, Pregunta, Examen
from core.utils import calcular_resultados 

def diagnosticar_y_pescar_preguntas(curso):
    """
    Motor de Selección Estricto.
    Selecciona preguntas basándose EXCLUSIVAMENTE en la configuración del curso.
    """
    # Validación básica
    if not curso.estructura_examen or 'reglas_seleccion' not in curso.estructura_examen:
        return None, "Error: El curso no tiene una estructura de examen definida."

    preguntas_seleccionadas = []
    ids_ya_usados = set()

    # Iteramos por las reglas definidas en la base de datos
    for regla in curso.estructura_examen['reglas_seleccion']:
        tema_nombre = regla.get('tema_nombre')
        cantidad = regla.get('cantidad', 10)
        dif_min = regla.get('dificultad_min', 1)
        dif_max = regla.get('dificultad_max', 5)
        
        # 1. Buscamos el objeto Tema
        tema_obj = Tema.objects.filter(nombre__iexact=tema_nombre).first()
        if not tema_obj:
            tema_obj = Tema.objects.filter(nombre__icontains=tema_nombre).first()

        if not tema_obj:
            return None, f"Error de configuración: El tema '{tema_nombre}' no existe en la BD."

        # 2. Query Estricta (CORREGIDA)
        # Cambiamos 'temas=tema_obj' por 'micro_competencia__temas=tema_obj'
        candidatas = Pregunta.objects.filter(
            micro_competencia__temas=tema_obj, 
            dificultad__gte=dif_min,
            dificultad__lte=dif_max
        ).exclude(id__in=ids_ya_usados)
        
        # 3. Validación de Stock
        count_disponible = candidatas.count()
        if count_disponible < cantidad:
            # Si falta stock, intentamos rellenar con lo que haya para no romper el examen
            seleccion = list(candidatas.order_by('?'))
            preguntas_seleccionadas.extend(seleccion)
            for p in seleccion: ids_ya_usados.add(p.id)
            
            # Opcional: Podrías lanzar error si prefieres ser estricto
            # return [], f"Falta stock en '{tema_nombre}'. Hay {count_disponible}, se piden {cantidad}."
        else:
            # Selección al azar normal
            seleccion = list(candidatas.order_by('?')[:cantidad])
            preguntas_seleccionadas.extend(seleccion)
            for p in seleccion: ids_ya_usados.add(p.id)

    if not preguntas_seleccionadas:
        return None, "No se encontraron preguntas válidas para generar el examen."

    return preguntas_seleccionadas, None


def finalizar_examen(user, curso, preguntas_ids, respuestas_usuario):
    """
    Procesa las respuestas, calcula nota, genera el reporte detallado y guarda.
    """
    # 1. Recuperar preguntas
    preguntas_set = list(Pregunta.objects.filter(id__in=preguntas_ids))
    
    # 2. Reordenar según el orden original del examen
    preguntas_map = {p.id: p for p in preguntas_set}
    preguntas_ordenadas = []
    for pid in preguntas_ids:
        if pid in preguntas_map:
            preguntas_ordenadas.append(preguntas_map[pid])

    # 3. Calcular Resultados Matemáticos
    # (Asumimos que utils hace el cálculo crudo)
    resultados_raw, porcentaje, total_correctas, total_preguntas = calcular_resultados(respuestas_usuario, preguntas_ordenadas)
    
    # 4. CONSTRUCCIÓN DEL SOLUCIONARIO
    detalles_para_html = []
    
    for pregunta in preguntas_ordenadas:
        # ID de la respuesta del usuario (ej: 'a', 'b')
        key_post = f"pregunta_{pregunta.id}"
        respuesta_user_id = respuestas_usuario.get(key_post)
        
        # Texto de la respuesta del usuario
        texto_usuario = "Sin responder"
        if respuesta_user_id and respuesta_user_id in pregunta.opciones:
            texto_usuario = pregunta.opciones[respuesta_user_id]
            
        # Texto de la respuesta correcta
        correcta_id = pregunta.respuesta_correcta 
        texto_correcta = pregunta.opciones.get(correcta_id, "Error en datos")
        
        # Verificación individual
        es_correcta = (str(respuesta_user_id) == str(correcta_id))
        
        detalles_para_html.append({
            'texto_pregunta': pregunta.texto,
            'es_correcta': es_correcta,
            'respuesta_usuario_texto': texto_usuario,
            'respuesta_correcta_texto': texto_correcta,
            'justificacion': pregunta.justificacion
        })

    # 5. Determinamos aprobación
    umbral = curso.estructura_examen.get('nota_aprobacion', 70) if curso.estructura_examen else 70
    examen_aprobado = porcentaje >= umbral
    
    # 6. Guardar en BD
    examen_obj = Examen.objects.create(
        usuario=user,
        curso=curso,
        preguntas_set=preguntas_ids,
        respuestas_usuario=respuestas_usuario,
        puntaje=porcentaje,
        aprobado=examen_aprobado
    )
    
    # 7. RETORNO PARA EL TEMPLATE
    return {
        'aprobado': examen_aprobado,
        'puntaje': porcentaje,       
        'detalles': detalles_para_html, 
        'examen_id': examen_obj.id,  
        'curso': curso
    }, None