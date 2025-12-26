from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
import json

from .models import (
    Usuario, 
    MicroCompetencia, 
    Tema, 
    Curso, 
    Pregunta, 
    Examen, 
    Certificado
)

# --- 1. Usuario Personalizado ---
class CustomUserAdmin(UserAdmin):
    model = Usuario
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('idioma',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {'fields': ('idioma',)}),)

admin.site.register(Usuario, CustomUserAdmin)

# --- MEJORA DE PRODUCTIVIDAD: Edición en línea ---
# Esto te permite agregar preguntas directamente dentro de la MicroCompetencia
class PreguntaInline(admin.StackedInline):
    model = Pregunta
    extra = 0
    fields = ('texto', 'respuesta_correcta', 'dificultad', 'opciones')
    show_change_link = True
    classes = ['collapse'] # Se mantiene cerrado para no ensuciar la vista si hay muchas

# --- 2. EL ÁTOMO: MicroCompetencia ---
@admin.register(MicroCompetencia)
class MicroCompetenciaAdmin(admin.ModelAdmin):
    list_display = ('icono', 'nombre', 'slug', 'total_preguntas')
    search_fields = ('nombre', 'definicion_atomica')
    prepopulated_fields = {'slug': ('nombre',)}
    
    # Agregamos el Inline aquí
    inlines = [PreguntaInline] 
    
    def total_preguntas(self, obj):
        count = obj.preguntas_banco.count()
        # Semáforo visual: Rojo si está vacío, Verde si tiene 10+
        color = "green" if count >= 10 else "orange" if count > 0 else "red"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, count)
    total_preguntas.short_description = "Banco Preguntas"

# --- 3. LA PLAYLIST: Tema ---
@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'parent', 'slug')
    list_filter = ('parent',)
    search_fields = ('nombre',)
    prepopulated_fields = {'slug': ('nombre',)}
    autocomplete_fields = ['parent']
    
    # Selector visual potente para agregar átomos a la playlist
    filter_horizontal = ('micro_competencias',) 

# --- 4. EL PRODUCTO: Curso ---
@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    # Aquí sí dejamos precio_usd porque decidiste mantenerlo en el modelo
    list_display = ('nombre', 'precio_usd', 'activo', 'cantidad_preguntas', 'created_at')
    list_filter = ('activo', 'created_at')
    search_fields = ('nombre',)
    prepopulated_fields = {'slug': ('nombre',)}
    
    # Selector visual potente para agregar playlists al producto
    filter_horizontal = ('temas',) 

# --- 5. EL REACTIVO: Pregunta ---
@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    # Eliminamos 'auditoria_calidad' para evitar errores
    list_display = ('texto_corto', 'micro_competencia', 'dificultad')
    list_filter = ('dificultad', 'micro_competencia')
    search_fields = ('texto', 'micro_competencia__nombre')
    
    readonly_fields = ('opciones_formateadas',) 
    
    fieldsets = (
        ('Contenido', {
            'fields': ('micro_competencia', 'texto', 'respuesta_correcta', 'dificultad')
        }),
        ('Detalles JSON', {
            'fields': ('opciones', 'opciones_formateadas', 'explicacion'),
            'classes': ('collapse',)
        }),
        # Eliminamos la sección de 'Control' por ahora (Auditoría)
    )

    def opciones_formateadas(self, obj):
        try:
            opciones_str = json.dumps(obj.opciones, indent=2, ensure_ascii=False)
            return format_html("<pre>{}</pre>", opciones_str)
        except TypeError:
            return obj.opciones
    opciones_formateadas.short_description = "Vista Previa Opciones"

    def texto_corto(self, obj):
        return obj.texto[:60] + "..." if obj.texto else "Sin texto"
    texto_corto.short_description = "Pregunta"

# --- 6. REGISTROS OPERATIVOS ---
@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'curso', 'puntaje', 'aprobado', 'fecha')
    list_filter = ('aprobado', 'fecha', 'curso')
    # Agregamos búsqueda para encontrar exámenes rápido
    search_fields = ('usuario__username', 'usuario__email', 'curso__nombre')

@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ('codigo_verificacion', 'usuario', 'curso', 'fecha_emision')
    readonly_fields = ('fecha_emision', 'codigo_verificacion')
    search_fields = ('codigo_verificacion', 'usuario__username')

admin.site.site_header = "Administración CDCV (Modelo Spotify)"
admin.site.site_title = "Panel de Control"
admin.site.index_title = "Gestión de Activos Educativos"