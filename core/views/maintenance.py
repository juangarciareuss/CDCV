from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils.text import slugify
from core.models import Tema, MicroCompetencia

# --- CONFIGURACIÓN CENTRAL: LISTA BLANCA ---
TEMAS_MAESTROS_OFICIALES = [
    'Microsoft Excel', 'Microsoft Word', 'SQL & Datos', 
    'Python & Código', 'Habilidades Blandas', 
    'Finanzas Personales', 'Gestión & Negocios', 'Medicina & Salud'
]

# MAPA DE INTELIGENCIA (Keyword -> Destino)
MAPA_LIMPIEZA = {
    'excel': 'Microsoft Excel', 'cálculos': 'Microsoft Excel', 'fórmulas': 'Microsoft Excel',
    'word': 'Microsoft Word', 'documentos': 'Microsoft Word', 'texto': 'Microsoft Word',
    'sql': 'SQL & Datos', 'datos': 'SQL & Datos', 'consultas': 'SQL & Datos',
    'neumonía': 'Medicina & Salud', 'diagnóstico': 'Medicina & Salud',
    'finanzas': 'Finanzas Personales', 'presupuestos': 'Finanzas Personales',
    'sinónimos': 'Habilidades Blandas', 'comunicación': 'Habilidades Blandas',
    'soft': 'Habilidades Blandas'
}

# ==========================================
# 1. DASHBOARD PRINCIPAL (Resumen KPI)
# ==========================================
@staff_member_required
def dashboard(request):
    # KPIs rápidos (Counts)
    total_comps = MicroCompetencia.objects.count()
    total_temas = Tema.objects.count()
    
    # Slugs Rotos (Estimación rápida)
    slugs_rotos = 0
    for c in MicroCompetencia.objects.all():
        if c.slug != slugify(c.nombre): slugs_rotos += 1
    
    # Temas Sucios (Estimación rápida)
    temas_sucios = Tema.objects.exclude(nombre__in=TEMAS_MAESTROS_OFICIALES).count()
    
    # Salud
    total_items = total_comps + total_temas or 1
    errores = slugs_rotos + temas_sucios
    salud = max(0, int(100 - ((errores / total_items) * 100)))

    context = {
        'salud': salud,
        'slugs_rotos': slugs_rotos,
        'temas_sucios': temas_sucios,
        'total_comps': total_comps
    }
    return render(request, 'maintenance/dashboard.html', context)

# ==========================================
# 2. GESTOR DE SLUGS (Detalle)
# ==========================================
@staff_member_required
def slug_manager(request):
    # Auditoría detallada de Competencias
    items = []
    errores = 0
    
    for c in MicroCompetencia.objects.all():
        ideal = slugify(c.nombre)
        estado = 'OK'
        if c.slug != ideal:
            estado = 'ERROR'
            errores += 1
        items.append({'tipo': 'Competencia', 'nombre': c.nombre, 'actual': c.slug, 'ideal': ideal, 'estado': estado})

    # Auditoría detallada de Temas
    for t in Tema.objects.all():
        ideal = slugify(t.nombre)
        estado = 'OK'
        if t.slug != ideal:
            estado = 'ERROR'
            errores += 1
        items.append({'tipo': 'Tema', 'nombre': t.nombre, 'actual': t.slug, 'ideal': ideal, 'estado': estado})

    return render(request, 'maintenance/slugs.html', {'items': items, 'errores': errores})

@staff_member_required
def ejecutar_reparacion_slugs(request):
    count = 0
    for model in [MicroCompetencia, Tema]:
        for obj in model.objects.all():
            ideal = slugify(obj.nombre)
            if obj.slug != ideal:
                obj.slug = ideal
                obj.save()
                count += 1
    messages.success(request, f"✅ {count} slugs reparados exitosamente.")
    return redirect('core:maintenance_slugs')

# ==========================================
# 3. GESTOR DE TEMAS (Arquitectura)
# ==========================================
@staff_member_required
def theme_manager(request):
    oficiales = []
    legacy = []
    
    all_temas = Tema.objects.all()
    
    for t in all_temas:
        habilidades_count = t.competencias.count()
        
        if t.nombre in TEMAS_MAESTROS_OFICIALES:
            oficiales.append({'obj': t, 'count': habilidades_count})
        else:
            # Predecir destino para mostrar en la tabla
            destino_predicho = "Desconocido (Se borrará)"
            nombre_lower = t.nombre.lower()
            for k, v in MAPA_LIMPIEZA.items():
                if k in nombre_lower:
                    destino_predicho = v
                    break
            
            legacy.append({
                'obj': t, 
                'count': habilidades_count, 
                'destino': destino_predicho
            })

    context = {
        'oficiales': oficiales,
        'legacy': legacy,
        'total_legacy': len(legacy)
    }
    return render(request, 'maintenance/themes.html', context)

@staff_member_required
def ejecutar_limpieza_temas(request):
    # 1. Asegurar Maestros
    for oficial in TEMAS_MAESTROS_OFICIALES:
        Tema.objects.get_or_create(nombre=oficial)
        
    movidos = 0
    borrados = 0
    
    # 2. Procesar Sucios
    sucios = Tema.objects.exclude(nombre__in=TEMAS_MAESTROS_OFICIALES)
    
    for sucio in sucios:
        destino_nombre = None
        # Buscar destino
        for k, v in MAPA_LIMPIEZA.items():
            if k in sucio.nombre.lower():
                destino_nombre = v
                break
        
        # Fallback genérico
        if not destino_nombre:
             if "datos" in sucio.nombre.lower(): destino_nombre = 'SQL & Datos'
        
        if destino_nombre:
            target = Tema.objects.get(nombre=destino_nombre)
            for c in sucio.competencias.all():
                c.temas.add(target)
                c.temas.remove(sucio)
                movidos += 1
            sucio.delete()
            borrados += 1
        else:
            # Si está vacío y no sabemos qué es, se va
            if sucio.competencias.count() == 0:
                sucio.delete()
                borrados += 1

    messages.success(request, f"🧹 Limpieza: {movidos} habilidades migradas, {borrados} temas eliminados.")
    return redirect('core:maintenance_themes')