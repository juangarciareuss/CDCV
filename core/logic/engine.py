import sys
import random
from django.db.models import Q
from core.models import Tema, Pregunta, Examen
from core.utils import calcular_resultados 

def diagnosticar_y_pescar_preguntas(curso):
    """
    Motor de Selección Estricto con Diagnóstico Detallado.
    Si falla, devuelve un reporte técnico exacto de por qué falló.
    """
    debug_log = [] # Aquí acumularemos las pistas
    
    # 1. Validación de Estructura (JSON)
    if not curso.estructura_examen:
        return None, "❌ ERROR CRÍTICO: El campo 'estructura_examen' está VACÍO en la base de datos."
        
    if 'reglas_seleccion' not in curso.estructura_examen:
        return None, f"❌ ERROR DE FORMATO: El JSON existe pero no tiene la clave 'reglas_seleccion'. Contenido: {curso.estructura_examen}"

    reglas = curso.estructura_examen['reglas_seleccion']
    if not reglas:
        return None, "❌ ERROR DE LÓGICA: La lista 'reglas_seleccion' está vacía ([]). El Builder no guardó ninguna regla."

    preguntas_seleccionadas = []
    ids_ya_usados = set()

    # 2. Iteración Forense por Reglas
    for i, regla in enumerate(reglas):
        tema_nombre = regla.get('tema_nombre')
        cantidad_pedida = regla.get('cantidad', 0)
        
        # A. Buscar el Tema
        # Intentamos coincidencia exacta primero, luego insensible a mayúsculas
        tema_obj = Tema.objects.filter(nombre__iexact=tema_nombre).first()
        if not tema_obj:
            # Intento de fallback por si el nombre varía ligeramente
            tema_obj = Tema.objects.filter(nombre__icontains=tema_nombre).first()
        
        if not tema_obj:
            debug_log.append(f"⚠️ Regla #{i+1}: El tema '{tema_nombre}' NO EXISTE en la tabla 'core_tema'.")
            continue

        # B. Contar Preguntas VERIFICADAS (La causa más probable)
        candidatas = Pregunta.objects.filter(
            micro_competencia__temas=tema_obj,
            micro_competencia__cursomicrocompetencia__curso=curso,
            verificado=True  # <--- OJO AQUÍ
        ).exclude(id__in=ids_ya_usados)
        
        stock_real = candidatas.count()

        if stock_real == 0:
            # Diagnóstico profundo: ¿Es porque no hay preguntas o porque no están verificadas?
            total_sin_verificar = Pregunta.objects.filter(
                micro_competencia__temas=tema_obj,
                micro_competencia__cursomicrocompetencia__curso=curso
            ).count()
            
            if total_sin_verificar > 0:
                debug_log.append(f"⛔ Regla #{i+1} ({tema_nombre}): Hay {total_sin_verificar} preguntas pero 0 VERIFICADAS. (Falta verificado=True)")
            else:
                debug_log.append(f"💀 Regla #{i+1} ({tema_nombre}): NO EXISTEN preguntas en BD para este curso/tema.")
            continue

        # C. Selección
        if stock_real < cantidad_pedida:
            debug_log.append(f"⚠️ Regla #{i+1} ({tema_nombre}): Se pedían {cantidad_pedida}, solo hay {stock_real}. Se tomaron todas.")
            seleccion = list(candidatas)
        else:
            seleccion = random.sample(list(candidatas), cantidad_pedida)
            
        preguntas_seleccionadas.extend(seleccion)
        for p in seleccion:
            ids_ya_usados.add(p.id)

# 3. Resultado Final
    if not preguntas_seleccionadas:
        mensaje_error = "NO SE PUDO GENERAR EL EXAMEN.\n\nDiagnóstico Técnico:\n" + "\n".join(debug_log)
        
        # 👇 AGREGA ESTO PARA VERLO EN LA TERMINAL 👇
        print("\n" + "="*50)
        print("🚨 REPORTE FORENSE DE ERROR (ENGINE):")
        print(mensaje_error)
        print("="*50 + "\n")
        # 👆 --------------------------------------- 👆

        return None, mensaje_error

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