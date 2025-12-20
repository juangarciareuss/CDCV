from django.db.models import Count, Q
from core.models import Curso, Pregunta, Examen, Certificado

def obtener_kpis_globales():
    """
    Calcula la salud del inventario con desglose detallado por Dificultad.
    Esto nos permitirá ver por qué el examen no encuentra preguntas.
    """
    cursos = Curso.objects.all()
    reporte_cursos = []

    for curso in cursos:
        # 1. Total bruto de preguntas del curso
        queryset = Pregunta.objects.filter(curso=curso)
        total_stock = queryset.count()
        
        # 2. Desglose por Dificultad (La Radiografía)
        # Contamos cuántas hay de cada nivel (1=Básico, 5=Experto)
        niveles = {}
        for i in range(1, 6):
            count = queryset.filter(dificultad=i).count()
            niveles[f'Nivel {i}'] = count

        # 3. Detectar preguntas "Rotas" (Sin dificultad o dificultad 0)
        # Esto suele ser la causa de que los exámenes salgan cortos
        rotas = queryset.filter(Q(dificultad__isnull=True) | Q(dificultad=0)).count()

        # 4. Salud del Inventario
        es_saludable = total_stock >= 30
        
        reporte_cursos.append({
            'nombre': curso.nombre,
            'stock_total': total_stock,
            'desglose': niveles,   # Pasamos el diccionario al template
            'preguntas_rotas': rotas,
            'salud': 'SALUDABLE' if es_saludable else 'BAJO STOCK',
            'css_class': 'success' if es_saludable else 'warning'
        })

    return {
        'total_preguntas': Pregunta.objects.count(),
        'total_cursos': cursos.count(),
        'total_certificados': Certificado.objects.count(),
        'detalle_cursos': reporte_cursos
    }

def obtener_stats_comerciales():
    return {
        "total_cursos": Curso.objects.filter(estructura_examen__isnull=False).count(),
        "total_examenes": Examen.objects.count(),
        "total_certificados": Certificado.objects.count()
    }