from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from core.views import gamification

# AHORA IMPORTAMOS LOS 3 MÓDULOS NUEVOS EN LUGAR DE 'views'
from core.views import dashboard, exam, tools 

app_name = 'core'

urlpatterns = [
    # --- 1. PÚBLICO Y USUARIO (Módulo: tools) ---
    path('', tools.homepage, name='homepage'),
    path('perfil/', tools.perfil_usuario, name='perfil_usuario'),
    path('accounts/', include('allauth.urls')), # Login de Google intacto
    path('guardar-nombre/', tools.guardar_nombre_legal, name='guardar_nombre_legal'),

    # --- 2. EXÁMENES Y PAGOS (Módulo: exam) ---
    path('examen/<int:curso_id>/', exam.examen, name='examen'),
    path('crear-pago/<int:examen_id>/', exam.crear_pago_paypal, name='crear_pago_paypal'),
    path('pago-exitoso/', exam.pago_exitoso, name='pago_exitoso'),
    path('pago-cancelado/', exam.pago_cancelado, name='pago_cancelado'),

    # --- 3. CERTIFICACIÓN (Módulo: tools) ---
    path('verificar/<uuid:codigo_verificacion>/', tools.verificar_certificado, name='verificar_certificado'),
    # Mantenemos el nombre 'descargar_certificado' para que tu botón PDF siga funcionando
    path('descargar-certificado/<str:codigo>/', tools.generar_pdf_certificado, name='descargar_certificado'),

    # --- 4. NUEVO DASHBOARD MODULAR (Módulo: dashboard) ---
    # Rutas nuevas para tu Fábrica de Cursos
    path('dashboard/crear/', dashboard.dashboard_crear, name='dashboard_crear'),
    path('dashboard/administrar/', dashboard.dashboard_administrar, name='dashboard_administrar'),
    
    # Ruta Legacy de KPI (Mantenida por si acaso)
    path('dashboard-kpi/', dashboard.dashboard_kpi, name='dashboard_kpi'),

    # --- 5. HERRAMIENTAS ADMINISTRATIVAS / API (Módulo: tools) ---
    # Estas rutas las usa tu JavaScript (Legacy), las mantenemos apuntando a tools
    path('dashboard/curar-ia/<int:curso_id>/', tools.endpoint_curar_con_ia, name='curar_ia'),
    path('dashboard/crear-curso/', tools.endpoint_crear_curso_ia, name='crear_curso_ia'), # Legacy API
    path('dashboard/toggle-status/<int:curso_id>/', tools.toggle_estado_curso, name='toggle_status'),
    path('dashboard/eliminar-curso/<int:curso_id>/', tools.eliminar_curso, name='eliminar_curso'),
    path('dashboard/usuarios/', dashboard.dashboard_usuarios, name='dashboard_usuarios'),

    path('buscar/', tools.buscar_cursos, name='buscar_cursos'),





    
]

# --- 6. MEDIA FILES (Mantenido intacto) ---
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),


# 🔥 EL GANCHO DE MARKETING
    path('reto/<slug:slug_competencia>/', gamification.reto_microcompetencia, name='reto_microcompetencia'),

]