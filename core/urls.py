from django.urls import path, include
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('examen/<int:curso_id>/', views.examen, name='examen'),
    path('crear-pago/<int:examen_id>/', views.crear_pago_paypal, name='crear_pago_paypal'),
    path('pago-exitoso/', views.pago_exitoso, name='pago_exitoso'),
    path('pago-cancelado/', views.pago_cancelado, name='pago_cancelado'),
    path('verificar/<uuid:codigo_verificacion>/', views.verificar_certificado, name='verificar_certificado'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('dashboard-kpi/', views.dashboard_kpi, name='dashboard_kpi'), #ruta al dashboard
    path('accounts/', include('allauth.urls')),
    path('dashboard/curar-ia/<int:curso_id>/', views.endpoint_curar_con_ia, name='curar_ia'),
    path('dashboard/crear-curso/', views.endpoint_crear_curso_ia, name='crear_curso_ia'),
    path('dashboard/toggle-status/<int:curso_id>/', views.toggle_estado_curso, name='toggle_status'),
]

