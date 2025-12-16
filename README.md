CDCV (Certified Digital Competency Validation)

Estado del Proyecto: MVP Funcional (Fase de Pre-Lanzamiento)
Visión: Democratizar la certificación de competencias mediante validación de mérito puro, automatizada por IA y accesible ($5 USD).

1. Whitepaper / Resumen Ejecutivo

CDCV es una plataforma global de certificación digital que permite a cualquier persona validar sus habilidades reales mediante exámenes automatizados y de bajo costo, sin necesidad de pagar cursos o instituciones tradicionales.

Objetivo General

Democratizar la certificación de competencias profesionales y prácticas, creando una alternativa masiva, rápida y accesible a las certificaciones tradicionales.

Público Objetivo

Usuarios de YouTube, freelancers, estudiantes autodidactas y empresas pequeñas que buscan validar habilidades sin grandes inversiones.

Propuesta de Valor

"Valida tu habilidad, no tu asistencia."
CDCV certifica lo que sabes, no lo que pagas. A diferencia de las plataformas tradicionales que cobran por el contenido educativo, CDCV cobra únicamente por la validación rigurosa del conocimiento adquirido por cualquier medio.

Estructura del Producto

Niveles: CDCV-A (Associate), CDCV-P (Professional), CDCV-M (Master).

Mecanismo: Exámenes automatizados, selección aleatoria de preguntas y certificados verificables en línea.

Modelo de Negocio

Estrategia: "Probar Gratis, Pagar por Certificado" (Validación de resultados).

Pricing: $5 USD base (Tier Express/Early Bird). Margen alto debido a costos variables mínimos.

Crecimiento: "Founder-led Growth" (8h/día dedicadas a SEO Long-tail y Marketing de Contenidos).

Escalabilidad: Generación masiva de cursos mediante Agentes de IA (Fábrica de Contenido).

Ventajas Competitivas

Costo: Ultra bajo comparado con certificaciones tradicionales ($5 vs $100+).

Automatización: Total, permitiendo escalabilidad infinita.

Flexibilidad: Enfoque multiidioma y temático (Trend-jacking de nuevas tecnologías el "Día 1").

Visión a 12 Meses

Lograr una base de datos con +1,000 cursos y +100,000 preguntas, disponible en 5 idiomas, con un sistema de ranking global.

2. Arquitectura Técnica

Stack Tecnológico

Backend: Django 5.x (Python 3.12).

Base de Datos: SQLite (Dev) / PostgreSQL (Prod).

Pagos: PayPal REST SDK (Configurado para pagos globales en USD).

Generación de Documentos: ReportLab (PDF) + Qrcode.

Infraestructura: Listo para despliegue en Railway/Render (Gunicorn + Whitenoise configurados).

Modelos de Datos Clave (core/models.py)

Curso: Contiene la metadata y una estructura JSON opcional (estructura_examen) para recetas de generación complejas.

Pregunta: Vinculada a Curso. Soporta estructura JSON para opciones (A, B, C, D) y justificación. Incluye metadatos de dificultad y tags.

Examen: Registra el intento del usuario. Almacena el snapshot de las preguntas usadas (preguntas_set) y las respuestas del usuario.

Certificado: Se genera SOLO tras un pago exitoso. Vinculado 1:1 con un Examen aprobado. Genera un UUID único para validación pública.

3. Estado Funcional (Features)

✅ Autenticación: Login/Logout nativo de Django. Vistas protegidas con @login_required.

✅ Motor de Exámenes: Selección aleatoria de preguntas (Logic en utils.py). Cálculo automático de puntaje.

✅ Flujo de Pago (PayPal):

Integración con PayPal Sandbox (probada y funcional).

Manejo de moneda USD.

Webhooks/Redirección para confirmación de pago (pago_exitoso).

✅ Emisión de Certificados:

Generación de PDF con nombre, curso, fecha y ID.

Generación de código QR incrustado que apunta a la URL de validación.

✅ Validación Pública: URL pública /verificar/<uuid>/ que muestra la autenticidad del certificado sin requerir login.

✅ Ingesta de Contenido: Scripts de gestión (importar_curso) para cargar cursos masivamente desde archivos JSON estandarizados.

4. Instrucciones de Instalación y Uso

Configuración Local

Clonar repositorio.

Crear entorno virtual: python -m venv venv.

Instalar dependencias: pip install -r requirements.txt.

Configurar variables de entorno: Crear archivo .env con SECRET_KEY, PAYPAL_CLIENT_ID y PAYPAL_CLIENT_SECRET.

Migrar DB: python manage.py migrate.

Crear Superusuario: python manage.py createsuperuser.

Carga de Datos (Fábrica de Contenido)

El sistema utiliza scripts para ingestar cursos generados por IA.
Ejemplo:

python manage.py importar_curso cursos_json/powerbi_avanzado.json


Ejecución

python manage.py runserver


5. Roadmap Inmediato (Siguientes Pasos)

Despliegue (Día 1): Subir a Railway/Render y conectar dominio (cdcv.io).

Go-Live: Cambiar credenciales de PayPal a LIVE en variables de entorno.

Marketing: Primera venta orgánica (LinkedIn/Reddit).

Fase 2 (IA Autónoma): Implementar core/ai_factory/agent_factory.py para automatizar la creación de JSONs de cursos (Agentes Estratega, Constructor y Auditor).