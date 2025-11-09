from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Tema, Curso, Pregunta, Examen, Certificado

# --- Modelo de Usuario Personalizado ---
class CustomUserAdmin(UserAdmin):
    model = Usuario
    # Campos que se muestran en la lista de usuarios
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    # Campos editables en el formulario del usuario
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('idioma',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('idioma',)}),
    )

# --- Modelo de Pregunta (para ver opciones JSON) ---
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('texto_corto', 'curso', 'nivel', 'idioma')
    list_filter = ('curso', 'nivel', 'idioma')
    search_fields = ('texto',)
    
    # Muestra los campos JSON de solo lectura
    readonly_fields = ('opciones_formateadas',) 

    def opciones_formateadas(self, obj):
        # (Esto es un extra para que el JSON se vea bonito en el admin)
        import json
        from django.utils.html import format_html
        try:
            opciones_str = json.dumps(obj.opciones, indent=2, ensure_ascii=False)
            return format_html("<pre>{}</pre>", opciones_str)
        except TypeError:
            return obj.opciones
    opciones_formateadas.short_description = "Opciones (JSON)"

    def texto_corto(self, obj):
        return obj.texto[:75] + '...' if len(obj.texto) > 75 else obj.texto
    texto_corto.short_description = "Texto de la Pregunta"

# --- Modelo de Examen ---
class ExamenAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'curso', 'puntaje', 'aprobado', 'fecha')
    list_filter = ('aprobado', 'curso', 'fecha')
    search_fields = ('usuario__username', 'curso__nombre')

# --- Modelo de Certificado ---
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'curso', 'fecha_emision', 'codigo_verificacion')
    list_filter = ('curso', 'fecha_emision')
    search_fields = ('usuario__username', 'curso__nombre')
    readonly_fields = ('codigo_verificacion',)

# --- Registro de Modelos ---
admin.site.register(Usuario, CustomUserAdmin)
admin.site.register(Tema)
admin.site.register(Curso)
admin.site.register(Pregunta, PreguntaAdmin)
admin.site.register(Examen, ExamenAdmin)
admin.site.register(Certificado, CertificadoAdmin)


# --- ¡NUEVAS LÍNEAS! (La Solución Permanente) ---
# Esto personaliza el título y la cabecera del Admin
admin.site.site_header = "Administración de CDCV"
admin.site.site_title = "Panel de Control CDCV"
admin.site.index_title = "Bienvenido al Panel de Control"
admin.site.site_url = "/" # ¡Esta es la línea que añade el enlace "VER SITIO"!