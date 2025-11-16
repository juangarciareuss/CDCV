from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
# AÑADIMOS PreguntaTema
from .models import Usuario, Tema, Curso, Pregunta, Examen, Certificado, PreguntaTema

# --- Modelo de Usuario Personalizado (Sin cambios) ---
class CustomUserAdmin(UserAdmin):
    model = Usuario
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('idioma',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('idioma',)}),
    )

# --- INLINE para PreguntaTema (NUEVO) ---
# Esto permite a los agentes (o a ti) editar la relación y el score 
# directamente desde la página de la Pregunta.
class PreguntaTemaInline(admin.TabularInline):
    model = PreguntaTema
    extra = 1 # Muestra 1 campo vacío por defecto
    fields = ('tema', 'relevancia_score', 'revisado_por_agente') # Campos editables en el inline
    autocomplete_fields = ['tema'] # Optimización para muchos temas

# --- Modelo de Tema (MODIFICADO para Taxonomía) ---
class TemaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'parent', 'descripcion') # AÑADIDO: 'parent'
    list_filter = ('parent',) # AÑADIDO: filtro por 'parent'
    search_fields = ('nombre',)
    fields = ('nombre', 'parent', 'descripcion') # AÑADIDO: 'parent'
    autocomplete_fields = ['parent'] # Optimización

# --- Modelo de Pregunta (MODIFICADO para nueva estructura) ---
class PreguntaAdmin(admin.ModelAdmin):
    # ELIMINADO: 'curso'
    # AÑADIDO: 'dificultad'
    list_display = ('texto_corto', 'dificultad', 'idioma')
    # ELIMINADO: 'curso'
    # AÑADIDO: 'dificultad'
    list_filter = ('dificultad', 'idioma', 'temas') # AÑADIDO: 'temas'
    search_fields = ('texto', 'temas__nombre')
    
    # AÑADIDO: El inline para el modelo intermediario robusto
    inlines = [PreguntaTemaInline]

    # Campos editables en el formulario. Se añade dificultad
    # ELIMINADO: 'nivel' (campo legacy)
    fieldsets = (
        (None, {'fields': ('texto', 'opciones', 'respuesta_correcta', 'dificultad', 'idioma')}),
        ('Información de Opciones (JSON)', {'fields': ('opciones_formateadas',), 'classes': ('collapse',)})
    )
    readonly_fields = ('opciones_formateadas',) 

    def opciones_formateadas(self, obj):
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

# --- Modelo de Curso (MODIFICADO para Receta) ---
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tema', 'nivel', 'idioma', 'tiene_receta')
    list_filter = ('nivel', 'idioma', 'tema')
    search_fields = ('nombre', 'descripcion')
    # AÑADIDO: Campo editable para la estructura del examen
    fields = ('nombre', 'tema', 'nivel', 'descripcion', 'idioma', 'estructura_examen')
    autocomplete_fields = ['tema']
    
    def tiene_receta(self, obj):
        # Verifica que la receta exista y no esté vacía
        return bool(obj.estructura_examen)
    tiene_receta.boolean = True
    tiene_receta.short_description = "Receta Activa"

# --- Modelo de Examen (Sin cambios) ---
class ExamenAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'curso', 'puntaje', 'aprobado', 'fecha')
    list_filter = ('aprobado', 'curso', 'fecha')
    search_fields = ('usuario__username', 'curso__nombre')

# --- Modelo de Certificado (Sin cambios) ---
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'curso', 'fecha_emision', 'codigo_verificacion')
    list_filter = ('curso', 'fecha_emision')
    search_fields = ('usuario__username', 'curso__nombre')
    readonly_fields = ('codigo_verificacion',)

# --- Registro de Modelos ---
admin.site.register(Usuario, CustomUserAdmin)
# REEMPLAZADO: admin.site.register(Tema)
admin.site.register(Tema, TemaAdmin)
admin.site.register(Curso, CursoAdmin)
# REEMPLAZADO: admin.site.register(Pregunta)
admin.site.register(Pregunta, PreguntaAdmin)
admin.site.register(Examen, ExamenAdmin)
admin.site.register(Certificado, CertificadoAdmin)
# AÑADIDO: El nuevo modelo intermedio (aunque ya se gestiona con el inline, se puede registrar)
admin.site.register(PreguntaTema)


# --- Personalización del Admin (Sin cambios) ---
admin.site.site_header = "Administración de CDCV"
admin.site.site_title = "Panel de Control CDCV"
admin.site.index_title = "Bienvenido al Panel de Control"
admin.site.site_url = "/"