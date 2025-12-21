import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

# --- Usuario ---
class Usuario(AbstractUser):
    idioma = models.CharField(max_length=10, default='es')
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="custom_user_groups" 
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_permissions"
    )
    
# --- Tema (Taxonomía) ---
class Tema(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    
    # Campo self-referential para la Taxonomía (padre/hijo)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='subtemas', 
        help_text="Usado para crear subtemas o taxonomía."
    )
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.nombre} -> {self.nombre}"
        return self.nombre

# --- Curso (Con Receta de Examen) ---
class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    tema = models.ForeignKey(
        Tema, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="El tema principal o categoría de este curso."
    ) 
    nivel = models.IntegerField(default=1) 
    descripcion = models.TextField(blank=True, null=True)
    idioma = models.CharField(max_length=10, default='es')
    activo = models.BooleanField(default=False, verbose_name="¿Visible en Catálogo?")
    score = models.IntegerField(default=0, help_text="Puntaje de calidad (0-30)")
    status = models.CharField(max_length=20, default='PENDIENTE', help_text="Estado de curación")
    
    # Campo que define la "receta" de cómo se construye el examen
    estructura_examen = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="JSON que define la 'receta' del examen."
    )
    
    def __str__(self):
        return f"{self.nombre} - Nivel {self.nivel}"

# --- Pregunta (Modelo Robusto) ---
class Pregunta(models.Model):
    # Mantenemos 'curso' para compatibilidad con tus datos actuales y scripts
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, null=True, blank=True)
    texto = models.TextField()
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    opciones = models.JSONField() 
    respuesta_correcta = models.CharField(max_length=1) 
    
    # Nivel de dificultad granular (1=Básico, 5=Experto)
    dificultad = models.IntegerField(
        default=1, 
        help_text="Nivel de dificultad objetivo (1=Básico, 5=Experto)"
    )
    
    # Relación Many-to-Many con Temas (Etiquetas)
    temas = models.ManyToManyField(
        Tema, 
        through='PreguntaTema', 
        related_name='preguntas',
        help_text="Etiquetas reutilizables (Temas/Subtemas) para esta pregunta."
    )
    
    # Legacy field
    nivel = models.IntegerField(default=1, help_text="[Legacy] Usar 'dificultad' en su lugar.")
    idioma = models.CharField(max_length=10, default='es')
    
    def __str__(self):
        return f"Pregunta {self.id} (Dificultad: {self.dificultad})"

# --- Modelo Intermediario (IA/ML) ---
class PreguntaTema(models.Model):
    """
    Modelo intermedio para la relación Many-to-Many entre Pregunta y Tema.
    """
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE)
    
    relevancia_score = models.FloatField(
        default=1.0, 
        help_text="Puntaje (0.0 a 1.0) asignado por IA sobre la relevancia."
    )
    
    revisado_por_agente = models.BooleanField(
        default=False, 
        help_text="Marcado como True si un agente de IA ha validado esta relación."
    )

    class Meta:
        unique_together = ('pregunta', 'tema')
        verbose_name = "Relación Pregunta-Tema"
        verbose_name_plural = "Relaciones Preguntas-Temas"

    def __str__(self):
        return f"[{self.pregunta.id}] -> [{self.tema.nombre}] (Score: {self.relevancia_score})"

# --- Examen ---
class Examen(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    preguntas_set = models.JSONField(help_text="Lista de IDs de Pregunta que se usaron", default=list) 
    respuestas_usuario = models.JSONField(help_text="Respuestas enviadas por el usuario", default=dict, null=True, blank=True)
    puntaje = models.FloatField(default=0)
    aprobado = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Examen de {self.usuario.username} para {self.curso.nombre}"

# --- Certificado (CORREGIDO) ---
class Certificado(models.Model):
    examen = models.OneToOneField(Examen, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    
    archivo_pdf = models.FileField(upload_to='certificados/', null=True, blank=True)
    codigo_qr = models.FileField(upload_to='codigos_qr/', null=True, blank=True)
    
    # Eliminamos editable=False para poder asignar el UUID manualmente en utils.py
    codigo_verificacion = models.UUIDField(unique=True) 
    
    fecha_emision = models.DateTimeField(auto_now_add=True)

    # ¡IMPORTANTE! Método save() ELIMINADO para evitar conflicto con force_insert.
    # La lógica se maneja en utils.py

    def __str__(self):
        return f"Certificado de {self.usuario.username} para {self.curso.nombre}"