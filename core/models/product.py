from django.db import models
from .content import Tema, MicroCompetencia
# Importamos Usuario desde el sistema de autenticación, o definimos Usuario aquí si prefieres mantenerlo junto.
# Generalmente Usuario se queda en un archivo base o auth. Vamos a asumir que Usuario está en un archivo `users.py` o lo importamos de `django.contrib.auth` si usas el default, pero como tienes un `Usuario` custom, lo pondremos en un archivo `users.py` o al inicio de `gamification.py` si prefieres.
# Para evitar líos de imports circulares, lo ideal es tener `Usuario` en su propio archivo `core/models/users.py`.
# PERO, para no crear 4 archivos, pondré Usuario en `gamification.py` ya que es el actor principal del progreso.

class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)

    # Relaciones
    temas = models.ManyToManyField(
        Tema, 
        related_name='cursos',
        help_text="Los módulos o temas que componen este curso."
    )
    micro_competencias = models.ManyToManyField(
        MicroCompetencia,
        through='CursoMicroCompetencia',
        related_name='cursos'
    )
    
    # Datos Comerciales
    precio_usd = models.DecimalField(max_digits=6, decimal_places=2, default=29.00)
    nivel = models.IntegerField(default=1) 
    descripcion = models.TextField(blank=True, null=True)
    idioma = models.CharField(max_length=10, default='es')
    activo = models.BooleanField(default=False, verbose_name="¿Visible en Catálogo?")
    
    # Datos de Examen y Calidad
    cantidad_preguntas = models.PositiveIntegerField(default=10, verbose_name="Preguntas por Examen")
    score = models.IntegerField(default=0, help_text="Puntaje de calidad (0-30)")
    status = models.CharField(max_length=20, default='PENDIENTE', help_text="Estado de curación")
    estructura_examen = models.JSONField(default=dict, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_preguntas_examen(self):
        if not self.estructura_examen:
            return 0
        reglas = self.estructura_examen.get('reglas_seleccion', [])
        return sum(r.get('cantidad', 0) for r in reglas)
    
    def __str__(self):
        return f"{self.nombre} - Nivel {self.nivel}"    

# --- Tabla Intermedia Curso-Competencia ---
class CursoMicroCompetencia(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    competencia = models.ForeignKey(MicroCompetencia, on_delete=models.CASCADE)
    orden = models.PositiveIntegerField(default=0, help_text="Orden en que se enseña")
    
    class Meta:
        ordering = ['orden']
        unique_together = ('curso', 'competencia')

# --- Certificado ---
# Nota: Necesitamos importar Usuario y Examen. Como Examen está en Gamification, aquí hay una dependencia circular potencial.
# TRUCO: Usar strings para las ForeignKey evita el import circular en tiempo de definición.
class Certificado(models.Model):
    examen = models.OneToOneField('core.Examen', on_delete=models.CASCADE)
    usuario = models.ForeignKey('core.Usuario', on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    
    archivo_pdf = models.FileField(upload_to='certificados/', null=True, blank=True)
    codigo_qr = models.FileField(upload_to='codigos_qr/', null=True, blank=True)
    codigo_verificacion = models.UUIDField(unique=True) 
    
    fecha_emision = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Certificado de {self.usuario.username} para {self.curso.nombre}"