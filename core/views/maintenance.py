from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils.text import slugify
from core.models import Tema, MicroCompetencia, Curso, Pregunta

# --- CONFIGURACIÓN CENTRAL: LISTA BLANCA (CATEGORÍAS) ---
# Estas son las "Etiquetas Maestras" para agrupar competencias
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
# 0. CLASE DE DIAGNÓSTICO (INTEGRITY DOCTOR)
# ==========================================
class IntegrityDoctor:
    """
    Clase encargada de diagnosticar y reparar la estructura de Cursos/Temas.
    Versión Blindada v2.
    """
    def diagnosticar(self):
        reporte = []
        cursos = Curso.objects.filter(activo=True)

        for curso in cursos:
            problemas = []
            
            # --- 1. SOLUCIÓN ROBUSTA PARA TEMAS (AttributeError) ---
            # Intentamos obtener los temas usando 'temas' (tu related_name)
            # Si falla, intentamos el default de Django 'tema_set'
            try:
                temas_queryset = curso.temas.all()
            except AttributeError:
                temas_queryset = curso.tema_set.all()

            if temas_queryset.count() == 0:
                problemas.append("⚠️ Curso vacío (Sin temas vinculados)")

            # --- 2. SOLUCIÓN ROBUSTA PARA PREGUNTAS (ValueError) ---
            # En lugar de una sola query compleja que falla, sumamos manualmente.
            # Esto es más seguro porque usa las relaciones directas.
            preguntas_count = 0
            
            for tema in temas_queryset:
                # Buscamos las microcompetencias del tema
                # Intentamos nombres comunes (microcompetencia_set o competencias)
                mcs = getattr(tema, 'microcompetencia_set', getattr(tema, 'competencias', None))
                
                if mcs:
                    for mc in mcs.all():
                        # Usamos 'preguntas_banco' que sabemos que existe por tus logs anteriores
                        preguntas_count += mc.preguntas_banco.count()

            if preguntas_count == 0:
                problemas.append("⚠️ Sin preguntas (No jugable)")

            # --- 3. Chequeo ESPECÍFICO (Excel) ---
            if "Excel" in curso.nombre:
                # Verificamos si existe el tema base crítico dentro del queryset que ya obtuvimos
                tema_base = temas_queryset.filter(nombre__icontains="Fundamentos").exists()
                if not tema_base:
                    problemas.append("🚨 FALTA TEMA CRÍTICO: 'Fundamentos'")

            if problemas:
                reporte.append({
                    'id': curso.id,
                    'nombre': curso.nombre,
                    'estado': 'CRÍTICO' if "CRÍTICO" in str(problemas) else 'ADVERTENCIA',
                    'problemas': problemas,
                })
        
        return reporte

    def reparar_estructura_excel(self, curso_id):
        # ... (Este método déjalo igual, funcionaba bien) ...
        try:
            curso = Curso.objects.get(id=curso_id)
            Tema.objects.get_or_create(
                curso=curso,
                nombre="Fundamentos y Manipulación de Datos",
                defaults={
                    'descripcion': 'Módulo base recuperado automáticamente por el Doctor.',
                    'orden': 1
                }
            )
            return True, f"Estructura de '{curso.nombre}' reparada exitosamente."
        except Exception as e:
            return False, f"Error técnico: {str(e)}"

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
    
    # Diagnóstico de Integridad (Nuevo)
    doctor = IntegrityDoctor()
    reporte_salud = doctor.diagnosticar()
    integrity_issues = len(reporte_salud)

    # Cálculo de Salud General (0 a 100)
    total_items = total_comps + total_temas or 1
    errores = slugs_rotos + temas_sucios + (integrity_issues * 5) # Penalizamos más los errores de integridad
    salud = max(0, int(100 - ((errores / total_items) * 100)))

    context = {
        'salud': salud,
        'slugs_rotos': slugs_rotos,
        'temas_sucios': temas_sucios,
        'integrity_issues': integrity_issues,
        'reporte_integridad': reporte_salud, # Pasamos el reporte completo al dashboard
        'total_comps': total_comps
    }
    return render(request, 'maintenance/dashboard.html', context)

# ==========================================
# 2. GESTOR DE SLUGS (Detalle)
# ==========================================
@staff_member_required
def slug_manager(request):
    items = []
    errores = 0
    
    for c in MicroCompetencia.objects.all():
        ideal = slugify(c.nombre)
        estado = 'OK'
        if c.slug != ideal:
            estado = 'ERROR'
            errores += 1
        items.append({'tipo': 'Competencia', 'nombre': c.nombre, 'actual': c.slug, 'ideal': ideal, 'estado': estado})

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
        # Busca 'competencias' (tu nombre probable) O 'microcompetencia_set' (default)
        manager = getattr(t, 'competencias', getattr(t, 'microcompetencia_set', None))
        habilidades_count = manager.count() if manager else 0

        if t.nombre in TEMAS_MAESTROS_OFICIALES:
            oficiales.append({'obj': t, 'count': habilidades_count})
        else:
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
        # 1. DETECTOR DE COMPETENCIAS (Tu relación segura)
        manager = getattr(sucio, 'competencias', getattr(sucio, 'microcompetencia_set', None))
        
        # 2. BUSCAR DESTINO
        destino_nombre = None
        for k, v in MAPA_LIMPIEZA.items():
            if k in sucio.nombre.lower():
                destino_nombre = v
                break
        
        # --- CAMBIO CLAVE AQUÍ ---
        # Si no encontramos destino y el tema TIENE contenido, 
        # lo mandamos a "Habilidades Generales" para poder borrar el tema viejo.
        if not destino_nombre:
            if "datos" in sucio.nombre.lower(): 
                destino_nombre = 'SQL & Datos'
            else:
                # VERTEDERO: Aquí caerá "Biología", "Power Query", etc.
                destino_nombre = 'Habilidades Generales' 
                Tema.objects.get_or_create(nombre=destino_nombre)

        # 3. EJECUTAR MIGRACIÓN Y BORRADO
        if manager and manager.count() > 0:
            # Si tiene cosas, las movemos
            target = Tema.objects.get(nombre=destino_nombre)
            for c in manager.all():
                c.temas.add(target)
                c.temas.remove(sucio)
                movidos += 1
            # Ahora que está vacío, lo borramos
            sucio.delete()
            borrados += 1
        else:
            # Si ya estaba vacío, lo borramos directo
            sucio.delete()
            borrados += 1

    messages.success(request, f"🧹 Limpieza: {movidos} habilidades migradas, {borrados} temas eliminados.")
    return redirect('core:maintenance_themes')

# ==========================================
# 4. REPARADOR DE INTEGRIDAD (NUEVO)
# ==========================================
@staff_member_required
def ejecutar_reparacion_integridad(request):
    """
    Recibe un POST desde el dashboard para reparar un curso específico.
    """
    if request.method == "POST":
        curso_id = request.POST.get('curso_id')
        tipo_accion = request.POST.get('accion') # ej: 'reparar_excel'
        
        doctor = IntegrityDoctor()
        
        if tipo_accion == 'reparar_excel':
            exito, msg = doctor.reparar_estructura_excel(curso_id)
            if exito:
                messages.success(request, f"✅ {msg}")
            else:
                messages.error(request, f"❌ {msg}")
        else:
            messages.warning(request, "Acción desconocida.")
            
    return redirect('core:maintenance_dashboard')