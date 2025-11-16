import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

# --- Usuario (Sin cambios) ---
class Usuario(AbstractUser):
    idioma = models.CharField(max_length=10, default='es')
    # Añadimos los related_name para evitar conflictos con el admin
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
    
# --- Tema (MODIFICADO para Taxonomía) ---
class Tema(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    
    # AÑADIDO: Campo self-referential para la Taxonomía (padre/hijo o tema/subtema)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, # Usamos SET_NULL para no borrar subtemas si se borra el padre
        null=True, 
        blank=True, 
        related_name='subtemas', 
        help_text="Usado para crear subtemas o taxonomía."
    )
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.nombre} -> {self.nombre}"
        return self.nombre

# --- Curso (MODIFICADO para Receta de Examen) ---
class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    # MODIFICADO: Ahora el tema es el 'main_topic', pero puede ser nulo
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
    
    # AÑADIDO: Campo que define la "receta" de cómo se construye el examen
    estructura_examen = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="JSON que define la 'receta' del examen. Ej: {'total': 10, 'reglas': [{'tema_id': 1, 'dificultad': [1,2], 'cantidad': 5}, ...]}"
    )
    
    def __str__(self):
        return f"{self.nombre} - Nivel {self.nivel}"

# --- Pregunta (MODELO PRINCIPALMENTE MODIFICADO) ---
class Pregunta(models.Model):
    # ELIMINADO: curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    
    texto = models.TextField()
    opciones = models.JSONField() 
    respuesta_correcta = models.CharField(max_length=1) 
    
    # AÑADIDO: Nivel de dificultad para selección granular
    dificultad = models.IntegerField(
        default=1, 
        help_text="Nivel de dificultad objetivo (1=Básico, 5=Experto)"
    )
    
    # MODIFICADO: Relación Many-to-Many con Temas (usando el modelo intermedio PreguntaTema)
    temas = models.ManyToManyField(
        Tema, 
        through='PreguntaTema', 
        related_name='preguntas',
        help_text="Etiquetas reutilizables (Temas/Subtemas) para esta pregunta."
    )
    
    # ELIMINADO: 'nivel' (redundante con 'dificultad', pero lo mantenemos por ahora para compatibilidad)
    nivel = models.IntegerField(default=1, help_text="[Legacy] Usar 'dificultad' en su lugar.")
    idioma = models.CharField(max_length=10, default='es')
    
    def __str__(self):
        return f"Pregunta {self.id} (Dificultad: {self.dificultad})"

# --- NUEVO MODELO INTERMEDIARIO (Through-Model) ---
class PreguntaTema(models.Model):
    """
    Modelo intermedio para la relación Many-to-Many entre Pregunta y Tema.
    Aquí es donde los agentes de IA pueden añadir inteligencia a la relación.
    """
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE)
    
    # AÑADIDO: Campo de control específico de la relación (para la IA/ML futuro)
    relevancia_score = models.FloatField(
        default=1.0, 
        help_text="Puntaje (0.0 a 1.0) asignado por un agente de IA sobre la relevancia de esta pregunta para este tema."
    )
    
    # AÑADIDO: Campo de revisión (para agentes de revisión)
    revisado_por_agente = models.BooleanField(
        default=False, 
        help_text="Marcado como True si un agente de IA de revisión ha validado esta relación."
    )

    class Meta:
        # Asegura que una pregunta solo pueda estar asociada una vez a un tema
        unique_together = ('pregunta', 'tema')
        verbose_name = "Relación Pregunta-Tema"
        verbose_name_plural = "Relaciones Preguntas-Temas"

    def __str__(self):
        return f"[Pregunta {self.pregunta.id}] -> [Tema: {self.tema.nombre}] (Score: {self.relevancia_score})"


# --- Examen (Sin cambios críticos) ---
class Examen(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    
    # ... (el resto de los campos quedan igual que en el archivo original)
    preguntas_set = models.JSONField(
        help_text="Lista de IDs de Pregunta que se usaron", 
        default=list  
    ) 
    respuestas_usuario = models.JSONField(
        help_text="Respuestas enviadas por el usuario", 
        default=dict,
        null=True, 
        blank=True
    )
    
    puntaje = models.FloatField(default=0)
    aprobado = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Examen de {self.usuario.username} para {self.curso.nombre}"

# --- Certificado (Sin cambios) ---
class Certificado(models.Model):
    examen = models.OneToOneField(Examen, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    
    archivo_pdf = models.FileField(upload_to='certificados/', null=True, blank=True)
    codigo_qr = models.FileField(upload_to='codigos_qr/', null=True, blank=True)
    
    codigo_verificacion = models.UUIDField(unique=True, editable=False)
    
    fecha_emision = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk and not self.codigo_verificacion:
            self.codigo_verificacion = uuid.uuid4()
        super(Certificado, self).save(args, **kwargs)

    def __str__(self):
        return f"Certificado de {self.usuario.username} para {self.curso.nombre}"