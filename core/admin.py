from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
import json

# Importamos TODOS los modelos expuestos en __init__.py
from .models import (
    Usuario, 
    MicroCompetencia, 
    Tema, 
    Curso, 
    CursoMicroCompetencia, # <--- IMPORTANTE PARA EL ORDEN
    Pregunta, 
    Examen, 
    Certificado,
    ProgresoCompetencia,   # <--- NUEVO
    PerfilMicroCompetencia # <--- NUEVO (ELO)
)

# --- 1. USUARIO (Con sus insignias visibles si quisieras) ---
class CustomUserAdmin(UserAdmin):
    model = Usuario
    list_display = ['username', 'email', 'is_staff', 'date_joined']
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('idioma',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {'fields': ('idioma',)}),)

admin.site.register(Usuario, CustomUserAdmin)


# --- 2. EL ÁTOMO: MicroCompetencia ---

# Permitir crear preguntas directamente desde la pantalla de la competencia
class PreguntaInline(admin.StackedInline):
    model = Pregunta
    extra = 0
    fields = ('texto', 'respuesta_correcta', 'dificultad', 'opciones', 'justificacion')
    show_change_link = True
    classes = ['collapse'] 

@admin.register(MicroCompetencia)
class MicroCompetenciaAdmin(admin.ModelAdmin):
    list_display = ('icono', 'nombre', 'slug', 'total_preguntas', 'temas_asociados')
    search_fields = ('nombre', 'definicion_atomica')
    prepopulated_fields = {'slug': ('nombre',)}
    
    # Asignación de Temas (Etiquetas)
    filter_horizontal = ('temas',) 
    
    # Muestra las preguntas hijas
    inlines = [PreguntaInline] 
    
    def total_preguntas(self, obj):
        count = obj.preguntas_banco.count()
        color = "green" if count >= 10 else "orange" if count > 0 else "red"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, count)
    total_preguntas.short_description = "Stock Preguntas"

    def temas_asociados(self, obj):
        return ", ".join([t.nombre for t in obj.temas.all()])


# --- 3. LA PLAYLIST: Tema ---
@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ('icono', 'nombre', 'slug')
    search_fields = ('nombre',)
    prepopulated_fields = {'slug': ('nombre',)}


# --- 4. EL PRODUCTO: Curso (Ahora con Ordenamiento) ---

# Esta es la magia para ordenar el curso átomo por átomo
class ContenidoCursoInline(admin.TabularInline):
    model = CursoMicroCompetencia
    extra = 1
    autocomplete_fields = ['competencia'] # Vital si tienes miles de competencias
    verbose_name = "Habilidad del Curso"
    verbose_name_plural = "Playlist de Habilidades (Ordenable)"

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nivel', 'activo', 'cantidad_preguntas', 'precio_usd')
    list_filter = ('activo', 'nivel', 'created_at')
    search_fields = ('nombre',)
    prepopulated_fields = {'slug': ('nombre',)}
    
    # Etiquetas Macro
    filter_horizontal = ('temas',)
    
    # Aquí definimos el contenido exacto
    inlines = [ContenidoCursoInline] 

    fieldsets = (
        ('Información Comercial', {
            'fields': ('nombre', 'slug', 'descripcion', 'precio_usd', 'activo', 'idioma')
        }),
        ('Configuración Técnica', {
            'fields': ('nivel', 'cantidad_preguntas', 'estructura_examen', 'temas')
        }),
    )


# --- 5. LA MUNICIÓN: Pregunta ---
@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('id', 'texto_corto', 'micro_competencia', 'dificultad', 'verificado')
    list_filter = ('dificultad', 'verificado', 'idioma', 'micro_competencia')
    search_fields = ('texto', 'micro_competencia__nombre')
    autocomplete_fields = ['micro_competencia'] # Carga rápida
    
    readonly_fields = ('opciones_formateadas',) 
    
    fieldsets = (
        ('Contexto', {
            'fields': ('micro_competencia', 'dificultad', 'verificado')
        }),
        ('Contenido', {
            'fields': ('texto', 'opciones', 'opciones_formateadas', 'respuesta_correcta', 'justificacion')
        }),
    )

    def opciones_formateadas(self, obj):
        try:
            opciones_str = json.dumps(obj.opciones, indent=2, ensure_ascii=False)
            return format_html("<pre>{}</pre>", opciones_str)
        except TypeError:
            return "Error en formato JSON"
    opciones_formateadas.short_description = "Vista Previa"

    def texto_corto(self, obj):
        return obj.texto[:80] + "..." if len(obj.texto) > 80 else obj.texto
    texto_corto.short_description = "Enunciado"


# --- 6. OPERACIONES Y AUDITORÍA ---
@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'curso', 'puntaje', 'aprobado', 'fecha')
    list_filter = ('aprobado', 'fecha')
    readonly_fields = ('preguntas_set', 'respuestas_usuario') # JSONs complejos mejor solo lectura

@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ('codigo_verificacion', 'usuario', 'curso', 'fecha_emision')
    readonly_fields = ('fecha_emision', 'codigo_verificacion', 'archivo_pdf', 'codigo_qr')
    search_fields = ('codigo_verificacion', 'usuario__email')


# --- 7. INTELIGENCIA DE DATOS (NUEVO) ---
# Esto es vital para ver si tu "Scalable Hive" está funcionando bien

@admin.register(ProgresoCompetencia)
class ProgresoCompetenciaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'competencia', 'estado', 'intentos')
    list_filter = ('estado', 'ultima_actualizacion')
    search_fields = ('usuario__username', 'competencia__nombre')

@admin.register(PerfilMicroCompetencia)
class PerfilELOAdmin(admin.ModelAdmin):
    """
    Monitor del Algoritmo ELO. 
    Permite ver si un usuario se vuelve experto o si una pregunta es muy difícil.
    """
    list_display = ('usuario', 'micro_competencia', 'nivel_actual', 'racha_actual', 'aciertos')
    list_filter = ('nivel_actual',)
    search_fields = ('usuario__username', 'micro_competencia__nombre')


# Configuración del Header
admin.site.site_header = "CertUfy AI Command Center"
admin.site.site_title = "Admin"
admin.site.index_title = "Gestión de Activos y Agentes"