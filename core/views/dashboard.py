from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models import Curso, Usuario
from core.logic import analytics

# Importamos el Agente (Asegúrate que la ruta sea correcta según tu estructura)
# Si usas Orchestrator, importa CDCVOrchestrator. Si usas directo el Agente:
from agents.builder_agent import BuilderAgent 

# --- PESTAÑA 1: LA FÁBRICA (Crear) ---
@login_required
def dashboard_crear(request):
    """
    Vista para invocar al Agente IA y crear nuevos cursos.
    Ahora soporta NIVEL DE DIFICULTAD (1-5).
    """
    if not request.user.is_staff: return redirect('core:homepage')

    if request.method == 'POST':
        nicho = request.POST.get('nicho')
        
        # 1. CAPTURAMOS EL NIVEL DEL FORMULARIO
        nivel_raw = request.POST.get('nivel')

        # 2. VALIDACIÓN OBLIGATORIA
        if not nivel_raw:
            messages.error(request, "⚠️ Error crítico: El Nivel de Profundidad es obligatorio.")
            return render(request, 'core/dashboard_crear.html', {'active_tab': 'crear'})

        try:
            nivel = int(nivel_raw)
        except ValueError:
            nivel = 3 # Fallback de seguridad

        if nicho:
            try:
                # Instanciamos al Agente Arquitecto
                agente = BuilderAgent()
                
                # 3. PASAMOS EL NIVEL A LA FUNCIÓN DE CONSTRUCCIÓN
                # Esto activará el prompt específico (Maestro vs Experto)
                resultado = agente.construir_curso(nicho, nivel_dificultad=nivel) 
                
                # Mensaje de éxito con detalles
                messages.success(request, f"✅ ¡Éxito! Curso '{nicho}' (Nivel {nivel}) creado correctamente.")
                return redirect('core:dashboard_administrar')
            
            except Exception as e:
                import traceback
                traceback.print_exc()
                messages.error(request, f"❌ Error del Agente: {str(e)}")
        else:
            messages.warning(request, "⚠️ Debes escribir un nicho de mercado.")

    return render(request, 'core/dashboard_crear.html', {
        'active_tab': 'crear' 
    })


# --- PESTAÑA 2: LA BODEGA (Administrar + Smart Resizing) ---
@login_required
def dashboard_administrar(request):
    """
    Lista los cursos y permite editar la cantidad total de preguntas del examen
    directamente desde la tabla (Lógica de redistribución proporcional).
    """
    if not request.user.is_staff: return redirect('core:homepage')
    
    # --- LÓGICA DE ACTUALIZACIÓN RÁPIDA (POST desde la tabla) ---
    if request.method == 'POST' and 'actualizar_total' in request.POST:
        try:
            curso_id = request.POST.get('curso_id')
            nuevo_total = int(request.POST.get('nuevo_total', 10))
            
            curso = get_object_or_404(Curso, id=curso_id)
            config = curso.estructura_examen or {}
            reglas = config.get('reglas_seleccion', [])
            
            # 1. Calcular el total actual configurado
            total_actual = sum(r.get('cantidad', 0) for r in reglas)
            if total_actual == 0: total_actual = 1 
            
            # 2. Calcular factor de escala
            factor = nuevo_total / total_actual
            
            # 3. Aplicar a cada tema proporcionalmente
            total_real_asignado = 0
            for regla in reglas:
                nueva_cant_tema = int(regla.get('cantidad', 0) * factor)
                if nueva_cant_tema < 1: nueva_cant_tema = 1 
                
                regla['cantidad'] = nueva_cant_tema
                total_real_asignado += nueva_cant_tema
                
            # 4. Ajuste fino (Cuadrar el redondeo)
            diferencia = nuevo_total - total_real_asignado
            
            if diferencia != 0 and reglas:
                reglas[0]['cantidad'] += diferencia
                if reglas[0]['cantidad'] < 1: reglas[0]['cantidad'] = 1

            # 5. Guardar cambios en la BD
            config['reglas_seleccion'] = reglas
            curso.estructura_examen = config
            curso.cantidad_preguntas = nuevo_total # Actualizamos el contador global también
            curso.save()
            
            messages.success(request, f"✅ Curso '{curso.nombre}' actualizado a {nuevo_total} preguntas.")
            
        except ValueError:
            messages.error(request, "❌ Error: Debes ingresar un número válido.")
        except Exception as e:
            messages.error(request, f"❌ Error al actualizar: {str(e)}")
            
        return redirect('core:dashboard_administrar')

    # --- GET: MOSTRAR TABLA ---
    # Mostramos cursos ordenados por creación reciente
    cursos = Curso.objects.filter(activo=True).order_by('-created_at')
    
    return render(request, 'core/dashboard_administrar.html', {
        'cursos': cursos,
        'active_tab': 'administrar'
    })


# --- PESTAÑA 3: DASHBOARD LEGACY (KPIs) ---
@login_required
def dashboard_kpi(request):
    if not request.user.is_staff: return redirect('core:homepage')
    data = analytics.obtener_diagnostico_completo()
    data['active_tab'] = 'kpi' 
    return render(request, "core/dashboard.html", data)


# --- PESTAÑA 4: USUARIOS ---
@login_required
def dashboard_usuarios(request):
    if not request.user.is_staff: return redirect('core:homepage')
    
    usuarios = Usuario.objects.all().order_by('-date_joined')
    
    return render(request, 'core/dashboard_usuarios.html', {
        'usuarios': usuarios,
        'active_tab': 'usuarios'
    })