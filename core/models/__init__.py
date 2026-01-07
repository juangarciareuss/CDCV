# core/models/__init__.py

# 1. Content
from .content import Tema, MicroCompetencia, Pregunta

# 2. Gamification (Debe ir antes de Product porque Product usa Usuario en Certificado string reference)
# Pero importamos las clases aquí para exponerlas.
from .gamification import (
    Usuario, 
    Examen, 
    ProgresoCompetencia, 
    InsigniaUsuario, 
    PerfilMicroCompetencia, 
    PerfilEntrenamiento
)

# 3. Product
from .product import Curso, CursoMicroCompetencia, Certificado