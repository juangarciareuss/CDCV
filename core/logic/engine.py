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
        dif_max = regla.get('dificultad_max', 5) # Aceptamos todo el rango por defecto
        
        # 1. Buscamos el objeto Tema
        tema_obj = Tema.objects.filter(nombre__iexact=tema_nombre).first()
        if not tema_obj:
            # Intento secundario por coincidencia parcial si el nombre exacto falla
            tema_obj = Tema.objects.filter(nombre__icontains=tema_nombre).first()

        if not tema_obj:
            return None, f"Error de configuración: El tema '{tema_nombre}' no existe en la base de datos."

        # 2. Query Estricta: Curso + Tema + Rango de Dificultad
        candidatas = Pregunta.objects.filter(
            temas=tema_obj,
            dificultad__gte=dif_min,
            dificultad__lte=dif_max
        ).exclude(id__in=ids_ya_usados)
        
        # 3. Validación de Stock
        count_disponible = candidatas.count()
        if count_disponible < cantidad:
            # En lugar de un print, construimos el reporte forense y retornamos ERROR
            mensaje_error = (
                f"⚠️ FALTA STOCK EN: '{tema_nombre}'\n\n"
                f"📉 Diagnóstico:\n"
                f"- El examen pide: {cantidad} preguntas.\n"
                f"- Nivel exigido: {dif_min} al {dif_max}.\n"
                f"- Stock encontrado: Solo {count_disponible} preguntas válidas.\n\n"
                f"💡 Solución: Ve al Dashboard -> 'Completar con IA' o usa la Shell para barajar dificultades."
            )
            return [], mensaje_error # <--- AQUÍ SE DETIENE Y TE AVISA

        # Si hay stock suficiente, seleccionamos al azar
        seleccion = list(candidatas.order_by('?')[:cantidad])
        
        preguntas_seleccionadas.extend(seleccion)
        
        # Guardamos IDs para no repetir en siguientes reglas
        for p in seleccion:
            ids_ya_usados.add(p.id)

    # Validación final
    if not preguntas_seleccionadas:
        return None, "No se encontraron preguntas válidas para generar el examen."

    return preguntas_seleccionadas, None


def finalizar_examen(user, curso, preguntas_ids, respuestas_usuario):
    """
    Procesa las respuestas, calcula la nota y guarda el registro.
    """
    # Recuperamos las preguntas de la BD
    preguntas_set = list(Pregunta.objects.filter(id__in=preguntas_ids))
    
    # Reordenamos para que coincidan con el orden en que se mostraron
    preguntas_map = {p.id: p for p in preguntas_set}
    preguntas_ordenadas = []
    for pid in preguntas_ids:
        if pid in preguntas_map:
            preguntas_ordenadas.append(preguntas_map[pid])

    # Calculamos resultados usando tu utilidad
    resultados, porcentaje, total_correctas, total_preguntas = calcular_resultados(respuestas_usuario, preguntas_ordenadas)
    
    # Determinamos aprobación
    umbral = curso.estructura_examen.get('nota_aprobacion', 70) if curso.estructura_examen else 70
    examen_aprobado = porcentaje >= umbral
    
    # Guardamos el intento
    examen_obj = Examen.objects.create(
        usuario=user,
        curso=curso,
        preguntas_set=preguntas_ids,
        respuestas_usuario=respuestas_usuario,
        puntaje=porcentaje,
        aprobado=examen_aprobado
    )
    
    return {
        'preguntas': preguntas_ordenadas,
        'resultados': resultados,
        'porcentaje': porcentaje,
        'total_correctas': total_correctas,
        'total_preguntas': total_preguntas,
        'examen': examen_obj
    }, None