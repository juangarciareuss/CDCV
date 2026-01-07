from django.db import models
from django.contrib.auth.models import AbstractUser
from .content import Tema, MicroCompetencia
from .product import Curso

# --- Usuario ---
class Usuario(AbstractUser):
    idioma = models.CharField(max_length=10, default='es')
    # Fix para conflictos de auth de Django por defecto
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name="custom_user_groups" 
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name="custom_user_permissions"
    )

# --- Examen ---
class Examen(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    preguntas_set = models.JSONField(help_text="Lista de IDs", default=list) 
    respuestas_usuario = models.JSONField(default=dict, null=True, blank=True)
    puntaje = models.FloatField(default=0)
    aprobado = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Examen de {self.usuario.username} para {self.curso.nombre}"

# --- ProgresoCompetencia (Estado Maestro) ---
class ProgresoCompetencia(models.Model):
    ESTADOS = [
        ('LOCKED', 'Bloqueado'),
        ('PENDING', 'Pendiente'),
        ('FAILED', 'Requiere Estudio'),
        ('VERIFIED', 'Validado'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    competencia = models.ForeignKey(MicroCompetencia, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, null=True)
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='LOCKED')
    intentos = models.PositiveIntegerField(default=0)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('usuario', 'competencia', 'curso')

    def __str__(self):
        return f"{self.usuario} - {self.competencia}: {self.estado}"

# --- Insignias ---
class InsigniaUsuario(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='insignias')
    competencia = models.ForeignKey(MicroCompetencia, on_delete=models.CASCADE)
    fecha_obtenida = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('usuario', 'competencia')
        verbose_name = "Insignia Ganada"
        verbose_name_plural = "Insignias Ganadas"

    def __str__(self):
        return f"🏅 {self.usuario.username} - {self.competencia.nombre}"

# --- Perfiles ELO y Gym ---
class PerfilMicroCompetencia(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    micro_competencia = models.ForeignKey(MicroCompetencia, on_delete=models.CASCADE)
    
    nivel_actual = models.FloatField(default=1.0)
    intentos_totales = models.PositiveIntegerField(default=0)
    aciertos = models.PositiveIntegerField(default=0)
    racha_actual = models.IntegerField(default=0)
    ultima_practica = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('usuario', 'micro_competencia')
        verbose_name = "Perfil de Habilidad (User)"

    @property
    def fase_calibracion(self):
        return self.intentos_totales < 5

    def actualizar_elo(self, acerto, dificultad_pregunta):
        k_factor = 1.5 if self.fase_calibracion else 0.2
        cambio = 0
        if acerto:
            dif_normalizada = dificultad_pregunta * 2 
            gap = max(0.1, dif_normalizada - self.nivel_actual) 
            cambio = k_factor * gap if gap > 0 else k_factor * 0.5
            
            self.aciertos += 1
            self.racha_actual = self.racha_actual + 1 if self.racha_actual > 0 else 1
        else:
            cambio = -(k_factor * 0.5)
            self.racha_actual = self.racha_actual - 1 if self.racha_actual < 0 else -1

        self.nivel_actual = max(1.0, min(10.0, self.nivel_actual + cambio))
        self.intentos_totales += 1
        self.save()

class PerfilEntrenamiento(models.Model):
    user = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE)
    nivel_actual = models.FloatField(default=1.0)
    preguntas_respondidas = models.IntegerField(default=0)
    ultima_actividad = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'tema')

    def __str__(self):
        return f"{self.user.username} - {self.tema.nombre} (Nvl {self.nivel_actual})"