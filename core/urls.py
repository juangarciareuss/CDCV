from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from django.views.generic import TemplateView # <--- Faltaba importar esto

# Importamos tus 4 módulos de vistas:
from core.views import dashboard, exam, tools, gamification

app_name = 'core'

urlpatterns = [
    # --- 1. PÚBLICO Y USUARIO (Módulo: tools) ---
    path('', tools.homepage, name='homepage'),
    path('perfil/', tools.perfil_usuario, name='perfil_usuario'),
    path('accounts/', include('allauth.urls')), # Login de Google
    path('guardar-nombre/', tools.guardar_nombre_legal, name='guardar_nombre_legal'),
    path('buscar/', tools.buscar_cursos, name='buscar_cursos'),

    # --- 2. EXÁMENES Y PAGOS (Módulo: exam) ---
    path('examen/<int:curso_id>/', exam.examen, name='examen'),
    path('crear-pago/<int:examen_id>/', exam.crear_pago_paypal, name='crear_pago_paypal'),
    path('pago-exitoso/', exam.pago_exitoso, name='pago_exitoso'),
    path('pago-cancelado/', exam.pago_cancelado, name='pago_cancelado'),

    # --- 3. CERTIFICACIÓN (Módulo: tools) ---
    path('verificar/<uuid:codigo_verificacion>/', tools.verificar_certificado, name='verificar_certificado'),
    path('descargar-certificado/<str:codigo>/', tools.generar_pdf_certificado, name='descargar_certificado'),

    # --- 4. DASHBOARD MODULAR (Módulo: dashboard) ---
    path('dashboard/crear/', dashboard.dashboard_crear, name='dashboard_crear'),
    path('dashboard/administrar/', dashboard.dashboard_administrar, name='dashboard_administrar'),
    path('dashboard/precios/', dashboard.dashboard_precios, name='dashboard_precios'),
    path('dashboard/usuarios/', dashboard.dashboard_usuarios, name='dashboard_usuarios'),
    path('dashboard-kpi/', dashboard.dashboard_kpi, name='dashboard_kpi'),

    # --- 5. HERRAMIENTAS ADMIN / API (Módulo: tools) ---
    path('dashboard/curar-ia/<int:curso_id>/', tools.endpoint_curar_con_ia, name='curar_ia'),
    path('dashboard/crear-curso/', tools.endpoint_crear_curso_ia, name='crear_curso_ia'),
    path('dashboard/toggle-status/<int:curso_id>/', tools.toggle_estado_curso, name='toggle_status'),
    path('dashboard/eliminar-curso/<int:curso_id>/', tools.eliminar_curso, name='eliminar_curso'),

    # --- 6. GAMIFICACIÓN / MARKETING (Módulo: gamification) ---
    path('reto/<slug:slug_competencia>/', gamification.reto_microcompetencia, name='reto_microcompetencia'),

    path('legal/terminos/', TemplateView.as_view(template_name="legal/terminos.html"), name='terminos'),
    path('legal/privacidad/', TemplateView.as_view(template_name="legal/privacidad.html"), name='privacidad'),
]

# --- 8. MEDIA FILES (Servir archivos subidos) ---
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]