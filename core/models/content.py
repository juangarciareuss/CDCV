from django.db import models
from django.utils.text import slugify

# --- Tema (Taxonomía Macro - ESTRUCTURA PLANA) ---
class Tema(models.Model):
    """
    Categorías Macro. Ej: Excel, Python, SQL, Habilidades Blandas.
    """
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    descripcion = models.TextField(blank=True, null=True)
    icono = models.CharField(max_length=50, default="📚", help_text="Emoji o clase FA") # ⬅️ AGREGAR ESTO
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

# --- MicroCompetencia (El Átomo - CEREBRO DE LA IA) ---
class MicroCompetencia(models.Model):
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)

    # 1. RELACIÓN CON TEMAS
    temas = models.ManyToManyField(
        Tema,
        related_name='competencias',
        help_text="Temas macro a los que pertenece esta habilidad."
    )

    # 2. CAMPOS DEL AGENTE AUDITOR
    definicion_atomica = models.TextField(
        help_text="Define el límite exacto. Ej: 'Solo suma de celdas contiguas'."
    )
    criterio_exito = models.TextField(
        help_text="Regla binaria para la IA."
    )
    prompt_validacion = models.TextField(
        blank=True, null=True,
        help_text="Instrucción base para evaluar esta competencia."
    )
    
    # 3. METADATA EXTRA
    icono = models.CharField(max_length=50, default="🏆", help_text="Emoji o URL")
    embedding_id = models.CharField(max_length=100, blank=True, null=True)

    def curso_sugerido(self):
        return self.cursos.filter(activo=True).first()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"MC: {self.nombre}"

# --- Pregunta (Con Agente Auditor Integrado) ---
class Pregunta(models.Model):
    texto = models.TextField()
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    
    #Vínculo con la Habilidad Específica
    micro_competencia = models.ForeignKey(
        MicroCompetencia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preguntas_banco',
        help_text="La competencia exacta que valida esta pregunta."
    )

    # Configuración
    opciones = models.JSONField() 
    respuesta_correcta = models.CharField(max_length=1) 
    
    justificacion = models.TextField(
        default="Respuesta basada en la definición de la competencia.",
        help_text="Explicación que se muestra al alumno si falla."
    )
    
    dificultad = models.IntegerField(default=1, help_text="1=Básico, 5=Experto")
    verificado = models.BooleanField(default=False, help_text="Validado por IA o Humano") # ⬅️ AGREGAR ESTO

    # Legacy (Mantener para no romper migraciones antiguas si existen datos)
    # Nota: Si estás seguro que no usas 'curso' en Pregunta, podrías borrarlo, pero pediste no borrar.
    # Para evitar import circular con Curso, usamos string 'core.Curso' o lo dejamos comentado si no se usa.
    # curso = models.ForeignKey('product.Curso', on_delete=models.CASCADE, null=True, blank=True) 
    
    nivel = models.IntegerField(default=1)
    idioma = models.CharField(max_length=10, default='es')

    def save(self, *args, **kwargs):
        if not self.justificacion and self.micro_competencia:
            self.justificacion = f"Concepto clave: {self.micro_competencia.definicion_atomica}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pregunta {self.id} (Dificultad: {self.dificultad})"
