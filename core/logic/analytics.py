from django.db.models import Count, Q
from core.models import Curso, Pregunta, Examen, Certificado

def obtener_diagnostico_completo():
    """
    NUEVA VERSIÓN: Compara Oferta (BD) vs Demanda (JSON).
    Genera la lista 'analisis_reglas' que necesita tu nuevo HTML.
    """
    # Solo cursos que tienen configuración de examen (JSON)
    cursos = Curso.objects.filter(estructura_examen__isnull=False)
    detalle_cursos = []

    total_preguntas_sistema = Pregunta.objects.count()
    total_certificados = Certificado.objects.count()

    for curso in cursos:
        # 1. Leer la Receta (JSON)
        # Esto es lo que le faltaba a tu código anterior
        config = curso.estructura_examen or {} 
        reglas = config.get('reglas_seleccion', [])
        
        analisis_reglas = []
        es_saludable = True
        stock_total_curso = 0
        
        # 2. Iterar regla por regla (Lo que pide el examen)
        for regla in reglas:
            tema_nombre = regla.get('tema_nombre') # Ojo: debe coincidir con el tag en BD
            d_min = regla.get('dificultad_min', 1)
            d_max = regla.get('dificultad_max', 10)
            cantidad_pide = regla.get('cantidad', 0)

            # 3. Consultar a la BD: ¿Cuántas preguntas tengo EXACTAMENTE para esta regla?
            # Aquí está el truco: Filtramos por Tema Y por Rango de Dificultad
            cantidad_tengo = Pregunta.objects.filter(
                temas__nombre=tema_nombre,
                dificultad__gte=d_min,
                dificultad__lte=d_max
            ).count()

            stock_total_curso += cantidad_tengo

            # 4. Veredicto: ¿Alcanza o no?
            cumple = cantidad_tengo >= cantidad_pide
            
            if not cumple:
                es_saludable = False # Si falla una sola regla, el curso se marca roto

            # Guardamos el detalle para pintarlo en la tabla del HTML
            analisis_reglas.append({
                'regla': f"Tema: {tema_nombre} (Nivel {d_min}-{d_max})",
                'pide': cantidad_pide,
                'tengo': cantidad_tengo,
                'status': 'OK' if cumple else 'FAIL'
            })

        # 5. Empaquetamos todo para la vista
        detalle_cursos.append({
            'id': curso.id,
            'nombre': curso.nombre,
            'activo': curso.activo,
            'analisis_reglas': analisis_reglas, # <--- La clave para tu nueva tabla
            'es_saludable': es_saludable,
            'stock_total': stock_total_curso,
            'preguntas_rotas': 0, # Ya no es tan relevante si validamos reglas, pero puedes dejarlo
            
            # Mantenemos esto por si tu HTML antiguo usa 'desglose', 
            # pero el nuevo HTML usa 'analisis_reglas'
            'desglose': {}, 
        })

    return {
        'total_preguntas': total_preguntas_sistema,
        'total_cursos': cursos.count(),
        'total_certificados': total_certificados,
        'detalle_cursos': detalle_cursos # Variable clave para el loop del HTML
    }

def obtener_stats_comerciales():
    # Esta déjala igual, está bien para contadores simples
    return {
        "total_cursos": Curso.objects.filter(estructura_examen__isnull=False).count(),
        "total_examenes": Examen.objects.count(),
        "total_certificados": Certificado.objects.count()
    }