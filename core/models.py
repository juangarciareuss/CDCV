import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

# --- Usuario ---
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
    
# --- Tema ---
class Tema(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.nombre

# --- Curso ---
class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE)
    nivel = models.IntegerField(default=1) 
    descripcion = models.TextField(blank=True, null=True)
    idioma = models.CharField(max_length=10, default='es')
    def __str__(self):
        return f"{self.nombre} - Nivel {self.nivel}"

# --- Pregunta ---
class Pregunta(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    texto = models.TextField()
    opciones = models.JSONField() 
    respuesta_correcta = models.CharField(max_length=1) 
    nivel = models.IntegerField(default=1)
    idioma = models.CharField(max_length=10, default='es')
    def __str__(self):
        return f"Pregunta {self.id} - Curso {self.curso.nombre}"

# --- Examen (MODELO CORREGIDO) ---
class Examen(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    
    # --- ¡ESTOS SON LOS CAMPOS CORREGIDOS CON DEFAULT! ---
    preguntas_set = models.JSONField(
        help_text="Lista de IDs de Pregunta que se usaron", 
        default=list  # Default para filas existentes
    ) 
    respuestas_usuario = models.JSONField(
        help_text="Respuestas enviadas por el usuario", 
        default=dict, # Default para filas existentes
        null=True, 
        blank=True
    )
    
    puntaje = models.FloatField(default=0)
    aprobado = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Examen de {self.usuario.username} para {self.curso.nombre}"

# --- Certificado ---
class Certificado(models.Model):
    examen = models.OneToOneField(Examen, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    
    archivo_pdf = models.FileField(upload_to='certificados/', null=True, blank=True)
    codigo_qr = models.FileField(upload_to='codigos_qr/', null=True, blank=True)
    
    # Quitamos 'default=uuid.uuid4'
    codigo_verificacion = models.UUIDField(unique=True, editable=False)
    
    fecha_emision = models.DateTimeField(auto_now_add=True)

    # Añadimos el método save() para generar el UUID
    def save(self, *args, **kwargs):
        # Si el objeto es nuevo (no tiene primary key) y no tiene código, genéralo.
        if not self.pk and not self.codigo_verificacion:
            self.codigo_verificacion = uuid.uuid4()
        super(Certificado, self).save(*args, **kwargs)

    def __str__(self):
        return f"Certificado de {self.usuario.username} para {self.curso.nombre}"