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