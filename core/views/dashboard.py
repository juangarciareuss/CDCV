from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models import Curso
from core.logic import analytics
from agents.builder_agent import BuilderAgent 

# --- PESTAÑA 1: LA FÁBRICA (Crear) ---
@login_required
def dashboard_crear(request):
    if not request.user.is_staff: return redirect('homepage')

    if request.method == 'POST':
        nicho = request.POST.get('nicho')
        if nicho:
            try:
                agente = BuilderAgent()
                resultado = agente.construir_curso(nicho) 
                messages.success(request, f"✅ ¡Éxito! {resultado}")
                return redirect('dashboard_administrar')
            except Exception as e:
                messages.error(request, f"❌ Error del Agente: {str(e)}")
        else:
            messages.warning(request, "⚠️ Debes escribir un nicho de mercado.")

    return render(request, 'core/dashboard_crear.html')

# --- PESTAÑA 2: LA BODEGA (Administrar) ---
@login_required
def dashboard_administrar(request):
    if not request.user.is_staff: return redirect('homepage')
    
    cursos = Curso.objects.all().order_by('-created_at')
    return render(request, 'core/dashboard_administrar.html', {'cursos': cursos})

# --- DASHBOARD LEGACY (KPIs) ---
@login_required
def dashboard_kpi(request):
    if not request.user.is_staff: return redirect('homepage')
    data = analytics.obtener_diagnostico_completo()
    return render(request, "core/dashboard.html", data)