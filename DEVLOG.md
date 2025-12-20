NOVIEMBRE - 2025
FASE 1: GÉNESIS E INFRAESTRUCTURA MVP (COMPLETADA)
Objetivo de Fase: Construir una plataforma funcional capaz de procesar pagos, evaluar usuarios y emitir certificados PDF válidos en un entorno de producción.

Capítulo 1: Construcción del Core, Motor de Exámenes y Despliegue
Fecha de Cierre: 2025-12-16 (Retrospectiva del Desarrollo Inicial) Estado: Éxito - Sistema en Producción (Render)

1. Contexto y Objetivos
El propósito inicial fue desarrollar una plataforma SaaS (Software as a Service) minimalista pero robusta para la validación de competencias digitales. Se requería un sistema que pudiera gestionar el ciclo completo del usuario sin intervención manual: Selección -> Pago -> Evaluación -> Certificación.

2. Arquitectura y Ejecución Técnica
A. Core Backend (Django & PostgreSQL)

Se implementó una arquitectura MVT (Model-View-Template) sobre Django.

Diseño de Base de Datos: Se modeló una estructura relacional en PostgreSQL optimizada para la integridad transaccional:

Course: Entidad padre (ej. "Excel Intermedio").

Question & Option: Relación 1:N para soportar exámenes de selección múltiple.

UserResponse: Persistencia de cada respuesta para auditoría futura.

Certification: Registro inmutable del logro, vinculado a un UUID único para validación externa.

B. Motor de Ingesta de Contenido (JSON-based)

En lugar de depender de un panel de administración manual lento, se desarrolló un sistema de ingesta programática.

Scripts de Carga: Se crearon comandos de gestión (management commands) capaces de leer archivos JSON estructurados y poblar la base de datos automáticamente.

Hito Técnico: Esto sentó las bases para la futura integración con IA, desacoplando la creación del contenido de la lógica de la base de datos. Se validó con cursos piloto de Excel, Python e IA Prompts.

C. Pasarela de Pagos (PayPal Integration)

Implementación del SDK de PayPal.

Lógica de Negocio:

Configuración de entorno dual (Sandbox para desarrollo / Live para producción).

Webhooks/IPN: El sistema escucha la confirmación de pago segura. Solo tras la confirmación exitosa del banco (payment_status === 'APPROVED'), se libera el acceso al examen o la descarga del certificado, previniendo fraudes.

D. Motor de Certificación (PDF Generation)

Integración de la librería WeasyPrint.

Renderizado Dinámico: Se diseñó una plantilla HTML/CSS que se compila en el servidor para generar un PDF vectorial de alta calidad.

Datos Variables: El certificado incrusta dinámicamente:

Nombre completo del usuario.

Fecha de aprobación.

Puntaje obtenido.

Código de verificación único (UUID) y QR (preparado).

E. Infraestructura y Despliegue

Dockerización: Contenedorización de la aplicación para consistencia entre desarrollo y producción.

Cloud Provider: Despliegue exitoso en Render.com.

Configuración: Gestión de variables de entorno (SECRET_KEY, DB_URL, PAYPAL_CLIENT_ID) segura, separando configuración de código.

3. Descubrimientos Clave
Escalabilidad del Contenido: La decisión de usar JSONs para los cursos fue crítica. Permitió iterar rápidamente el contenido sin tocar el código fuente, validando que el sistema está listo para ser alimentado por agentes de IA.

Experiencia de Usuario: La fricción entre el pago y el examen es el punto crítico. La integración de PayPal funcionó, pero requiere monitoreo en producción para evitar carritos abandonados.

4. Estado del Sistema (Snapshot al cierre de Fase 1)
URL: https://cdcv.onrender.com/ (Activo/HTTPS).

Cursos Disponibles: 3 (Excel, Python, IA).

Stack: Python/Django, Postgres, Gunicorn, WeasyPrint.

Capacidad: Lista para recibir tráfico real y procesar transacciones monetarias.

## FASE 2: ESTABILIZACIÓN Y PRIMERA VENTA
*Objetivo de Fase: Corregir el flujo de usuario (Nombre/Certificado), activar pagos reales (PayPal Live) y lograr la primera transacción exitosa sin errores.*

### Capítulo 1: Go-Live (Infraestructura)
**Fecha:** 2025-12-16
**Estado:** Infraestructura OK, pero Lógica de Negocio con fallos críticos.
**Bloqueos Detectados:**
1.  **Identidad:** Los certificados no muestran el nombre del usuario (Falta captura de datos en registro).
2.  **Pagos:** PayPal sigue en modo Sandbox (Dinero ficticio).
3.  **Funcionalidad:** Reporte de fallos en la ejecución de cursos.

Fecha: 17 de Diciembre, 2025 Foco: Despliegue en Producción, Configuración de BD y Debugging de Exámenes. Estado: Funcionalidad Core Operativa (95%) - Pendiente servicio de Media.

🛠️ Logros y Correcciones Técnicas
Infraestructura y Build (build.sh):

Se limpió el script de construcción eliminando dependencias rotas (PowerBI/win32) incompatibles con Linux.

Se corrigió el comando de arranque de Gunicorn apuntando correctamente a config.wsgi en lugar de cdcv.wsgi.

Base de Datos y Seeding (seed_taxonomy.py):

Taxonomía Automática: Se implementó un script que reconstruye la estructura de Cursos y Temas automáticamente tras cada despliegue.

Vinculación de Preguntas: Se solucionó el error de "Preguntas Huérfanas". Se añadió una rutina que fuerza la vinculación de las 100 preguntas importadas al Tema Padre "Análisis de Datos (Excel)" mediante una relación Many-to-Many (.add()).

Corrección de Código: Se refactorizó el uso incorrecto de .update() en campos ManyToMany.

Lógica del Examen (views.py):

Receta de Examen: Se simplificó la estructura JSON del examen ("Receta") para hacerla más permisiva en producción (Rango de dificultad 0-10, aceptación de tema padre).

Diagnóstico (Rayos X): Se implementó un sistema de logs detallados en STDERR dentro de la vista examen para trazar por qué fallaba la selección de preguntas en tiempo real.

Resultado: El motor de exámenes ya genera cuestionarios correctamente, calcula la nota y registra el aprobado.

Flujo de Negocio Completado:

✅ Login de Usuario (Superuser).

✅ Generación de Examen (10 preguntas).

✅ Evaluación y Cálculo de Nota.

✅ Integración con PayPal (Sandbox) funcionando en vivo.

✅ Generación del registro de Certificado en Base de Datos.

⚠️ Pendientes y Próximos Pasos
Error 404 en Descarga de PDF:

Problema: Django en modo producción (DEBUG=False) no sirve archivos de la carpeta /media/ por defecto. El archivo se crea, pero la URL da 404.

Solución Aplicada (Pendiente de Test): Se configuró re_path y serve en urls.py y se definió MEDIA_ROOT en settings.py para forzar la entrega de archivos estáticos en Render.

Acción: Verificar descarga tras el próximo reinicio.

¡Buen descanso! Ha sido una sesión técnica muy productiva y "dura" (tocando código base, base de datos y scripts externos). Aquí tienes tu DevLog para cerrar el día, con el resumen de lo logrado y lo que queda pendiente para mañana.

📝 DevLog: Implementación de Agentes de Curación
Fecha: 18 de Diciembre, 2025 Proyecto: CDCV - Certified Digital Competency Validation

✅ Hitos Completados (Backend & Datos)
Creación del Agente Orquestador (curador.py):

Se implementó un script autónomo capaz de cargar el entorno de Django (django.setup()) sin iniciar el servidor completo.

Se conectó exitosamente a la base de datos de producción (SQLite).

Evolución del Modelo de Datos:

Se modificó el modelo Curso agregando campos de control de calidad: score y status.

Se ejecutaron migraciones (makemigrations / migrate) correctamente.

Inyección Masiva de Contenido:

El agente detectó brechas de inventario en 5 cursos.

Se generaron e insertaron +200 preguntas sintéticas para alcanzar la meta de 30 preguntas por curso.

Total actual en BD: 277 preguntas (antes ~65).

Corrección de Integridad de Datos (Data Fixing):

Se solucionaron errores de restricciones NOT NULL añadiendo JSONs de opciones válidos.

Se normalizaron campos huérfanos mediante consola interactiva: idioma='es', dificultad=1.

Script asignar_temas.py: Se creó y ejecutó con éxito un script para vincular las 150 preguntas nuevas a temas específicos ("Fundamentos Generales", etc.).

⚠️ Estado Actual (El "Cliffhanger")
Base de Datos: 🟢 SALUDABLE. Los datos están ahí, asignados y completos (277 registros).

Dashboard Visual: 🔴 DESSINCRONIZADO. El contador global muestra los datos nuevos (277), pero el desglose por curso sigue en cero o bajo stock.

Causa probable: La lógica de la vista (views.py) tiene un filtro específico (ej: visible=True, aprobada=True) que las nuevas preguntas aún no cumplen.

📌 Próximos Pasos (Para la siguiente sesión)
Revisar core/views.py para identificar el filtro que está ocultando las preguntas nuevas en el desglose.

Ajustar el script curador.py para que genere contenido con ese "flag" de visibilidad activado por defecto.

Conectar el Agente a ai_services.py para que el texto de las preguntas sea real y no simulado.