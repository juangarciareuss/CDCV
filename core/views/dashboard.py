from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import modelformset_factory, NumberInput  # <--- NUEVO: Para la tabla de precios
from core.models import Curso, Usuario
from core.logic import analytics
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# Importamos el Agente
from agents.builder_agent import BuilderAgent 

# EN: core/views/dashboard.py
#

@login_required
def dashboard_crear(request):
    """
    Vista para crear cursos.
    Captura Nicho, Nivel y Precio directamente del formulario y ejecuta el Agente.
    """
    if not request.user.is_staff: return redirect('core:homepage')

    if request.method == 'POST':
        nicho = request.POST.get('nicho')
        nivel_raw = request.POST.get('nivel')
        precio_raw = request.POST.get('precio')

        # Verificación simple de que llegaron datos
        if not nicho or not nivel_raw or not precio_raw:
            messages.error(request, "⚠️ Todos los campos son obligatorios.")
            return render(request, 'core/dashboard_crear.html', {'active_tab': 'crear'})

        try:
            # Conversión de tipos directa
            nivel = int(nivel_raw)
            precio = float(precio_raw)
            
            # Instanciamos al Agente
            agente = BuilderAgent()
            
            # Construimos la estructura base
            curso = agente.construir_curso(nicho, nivel_dificultad=nivel) 
            
            if curso:
                # Actualizamos el precio con lo que ingresó el usuario
                curso.precio_usd = precio
                curso.save()
                
                messages.success(request, f"✅ Curso '{curso.nombre}' creado. Precio: ${precio} USD.")
                return redirect('core:dashboard_administrar')
            else:
                messages.error(request, "⚠️ El agente IA no devolvió un curso válido.")

        except ValueError:
            messages.error(request, "❌ Error de formato en Nivel o Precio.")
        except Exception as e:
            messages.error(request, f"❌ Error del sistema: {str(e)}")

    return render(request, 'core/dashboard_crear.html', {
        'active_tab': 'crear' 
    })


# --- PESTAÑA 2: LA BODEGA (Administrar + Smart Resizing + Toggle + ELIMINAR) ---
@login_required
def dashboard_administrar(request):
    """
    Lista TODOS los cursos y permite:
    1. Editar la cantidad total de preguntas (Smart Resizing).
    2. Activar/Desactivar cursos (Toggle).
    3. ELIMINAR cursos (Funcionalidad Nueva).
    """
    if not request.user.is_staff: return redirect('core:homepage')
    
    if request.method == 'POST':
        # --- CASO 1: CAMBIAR ESTADO (TU CÓDIGO ORIGINAL) ---
        if request.POST.get('accion') == 'toggle_estado':
            curso_id = request.POST.get('curso_id')
            curso = get_object_or_404(Curso, id=curso_id)
            
            # Invertimos el estado
            curso.activo = not curso.activo
            curso.save()
            
            # Feedback visual según la acción
            if curso.activo:
                messages.success(request, f"🟢 Curso '{curso.nombre}' ahora está PÚBLICO.")
            else:
                messages.warning(request, f"🔴 Curso '{curso.nombre}' ahora está OCULTO (Borrador).")
            
            return redirect('core:dashboard_administrar')

        # --- CASO 2: ELIMINAR CURSO (NUEVO BLOQUE AGREGADO) ---
        elif request.POST.get('accion') == 'eliminar_curso':
            curso_id = request.POST.get('curso_id')
            curso = get_object_or_404(Curso, id=curso_id)
            try:
                nombre_backup = curso.nombre
                curso.delete()
                messages.success(request, f"🗑️ Curso '{nombre_backup}' eliminado definitivamente.")
            except Exception as e:
                # Protección de integridad
                messages.error(request, f"⛔ No se puede eliminar '{curso.nombre}' porque tiene datos históricos (alumnos/ventas) asociados.")
            
            return redirect('core:dashboard_administrar')

        # --- CASO 3: ACTUALIZAR TOTAL PREGUNTAS (TU CÓDIGO ORIGINAL) ---
        elif 'actualizar_total' in request.POST:
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
                curso.save()
                
                messages.success(request, f"✅ Curso '{curso.nombre}' re-calculado a {nuevo_total} preguntas.")
                
            except ValueError:
                messages.error(request, "❌ Error: Debes ingresar un número válido.")
            except Exception as e:
                messages.error(request, f"❌ Error al actualizar: {str(e)}")
                
            return redirect('core:dashboard_administrar')

    # --- GET: MOSTRAR TABLA (TU CÓDIGO ORIGINAL) ---
    cursos = Curso.objects.all().order_by('-created_at')
    
    return render(request, 'core/dashboard_administrar.html', {
            'cursos': cursos,
            'active_tab': 'administrar'
        })

# --- PESTAÑA 3: CONFIGURACIÓN DE PRECIOS (NUEVA FUNCIONALIDAD) ---
@login_required
def dashboard_precios(request):
    """
    Permite editar masivamente el precio (USD) de todos los cursos activos.
    Usa un ModelFormSet para crear una tabla editable.
    """
    if not request.user.is_staff: return redirect('core:homepage')

    # 1. Definimos la 'Fábrica de Formularios' (FormSet)
    # Esto le dice a Django: "Quiero editar el campo 'precio_usd' de muchos Cursos a la vez"
    PrecioFormSet = modelformset_factory(
        Curso,
        fields=('precio_usd',),  # Asegúrate de que este campo exista en tu models.py
        extra=0,                 # No mostrar filas vacías para crear nuevos
        widgets={
            'precio_usd': NumberInput(attrs={
                'class': 'border border-gray-300 rounded px-3 py-2 w-32 text-right focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',  # Permite decimales
                'min': '0.50'    # Precio mínimo de seguridad
            })
        }
    )

    # 2. Procesar Guardado (POST)
    if request.method == 'POST' and 'btn_actualizar_precios' in request.POST:
        formset = PrecioFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            messages.success(request, "💰 ¡Precios actualizados correctamente para todos los cursos!")
            return redirect('core:dashboard_precios') # Recarga limpia (PRG pattern)
        else:
            messages.error(request, "❌ Error al guardar. Revisa que los valores sean números válidos.")

    # 3. Cargar Datos (GET)
    # Solo mostramos cursos activos, ordenados por nombre para facilitar la búsqueda
    queryset = Curso.objects.filter(activo=True).order_by('nombre')
    formset_precios = PrecioFormSet(queryset=queryset)

    return render(request, 'core/dashboard_precios.html', {
        'formset_precios': formset_precios,
        'active_tab': 'precios'  # Identificador para resaltar la pestaña en el HTML
    })


# --- PESTAÑA 4: DASHBOARD LEGACY (KPIs) ---
@login_required
def dashboard_kpi(request):
    if not request.user.is_staff: return redirect('core:homepage')
    data = analytics.obtener_diagnostico_completo()
    data['active_tab'] = 'kpi' 
    return render(request, "core/dashboard.html", data)


# --- PESTAÑA 5: USUARIOS ---
@login_required
def dashboard_usuarios(request):
    if not request.user.is_staff: return redirect('core:homepage')
    
    usuarios = Usuario.objects.all().order_by('-date_joined')
    
    return render(request, 'core/dashboard_usuarios.html', {
        'usuarios': usuarios,
        'active_tab': 'usuarios'
    })
