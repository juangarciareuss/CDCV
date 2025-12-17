CDCV (Certified Digital Competency Validation)

Estado del Proyecto: MVP Funcional (Fase de Pre-Lanzamiento)
Visión: Democratizar la certificación de competencias mediante validación de mérito puro, automatizada por IA y accesible ($5 USD).

# 1. Whitepaper / Resumen Ejecutivo

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

# 2. Arquitectura Técnica

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

# 3. Estado Funcional (Features)

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

# 4. Instrucciones de Instalación y Uso

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


# 5. Roadmap Inmediato (Siguientes Pasos)

Despliegue (Día 1): Subir a Railway/Render y conectar dominio (cdcv.io).

Go-Live: Cambiar credenciales de PayPal a LIVE en variables de entorno.

Marketing: Primera venta orgánica (LinkedIn/Reddit).

Fase 2 (IA Autónoma): Implementar core/ai_factory/agent_factory.py para automatizar la creación de JSONs de cursos (Agentes Estratega, Constructor y Auditor).

## 6. Plan Maestro Económico: Roadmap a $300k ARR

Este plan proyecta el crecimiento financiero para los primeros 12 meses de operación, fundamentado en tres pilares de escalabilidad tecnológica que rompen la linealidad tradicional:

1.  **Hiper-Escalabilidad de Contenido (Agentización):** Uso de agentes autónomos para pasar de 3 cursos a +1,000 cursos sin intervención humana directa.
2.  **Multiplicador Lingüístico:** Traducción y adaptación automática simultánea a 3 idiomas clave (Español, Inglés, Portugués), triplicando el mercado objetivo instantáneamente.
3.  **Base de Datos Infinita:** Generación procedimental de millones de preguntas únicas, eliminando el riesgo de plagio y permitiendo re-intentos ilimitados para el usuario.

### Hipótesis de Ingresos
* **Ticket Promedio Inicial:** $5 USD (Validación Masiva).
* **Ticket Promedio Fase 2:** $29 USD (Certificación Pro/Especializada).
* **Margen Operativo:** ~95% (Costos de servidor fijos, costo de creación de producto cercano a $0 por la IA).

### Proyección Mensual - Año 1 (Fase de Arranque y Escalamiento)

El objetivo es cerrar el Mes 12 con una facturación recurrente mensual (MRR) de **$25,000 USD**, lo que anualizado equivale al objetivo de **$300,000 USD**.

| Mes | Fase | Acción Estratégica Clave (Agentes & Tech) | Catálogo (Cursos x Idiomas) | Ventas Est. / Mes | Ingresos Proyectados |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Semilla | Despliegue de MVP. Ajuste manual de pasarela de pagos. | 10 (Esp) | 20 | **$100** |
| **2** | Calibración | **Activación Agente Creador**. Primeros 50 cursos generados por IA (Excel, Python, SQL). | 50 (Esp) | 100 | **$500** |
| **3** | Tracción | Indexación SEO inicial. Campañas orgánicas en redes. | 100 (Esp) | 300 | **$1,500** |
| **4** | **Expansión** | **Activación Agente Traductor**. Lanzamiento en Inglés (USA/India/Europa). | 300 (100 x 3 Idiomas) | 800 | **$4,000** |
| **5** | Escala 1 | Agentes operando 24/7 generando nichos (Frameworks JS, AWS, Azure). | 600 (200 x 3 Idiomas) | 1,200 | **$6,000** |
| **6** | Escala 2 | Optimización de conversión. Inicio de captación B2B pequeña. | 900 (300 x 3 Idiomas) | 1,800 | **$9,000** |
| **7** | **Pro Tier** | **Lanzamiento Certificaciones Pro ($29 USD)**. Validación de identidad básica. | 1,500 (Total activos) | 2,000 (Std) + 100 (Pro) | **$12,900** |
| **8** | Dominio | Cobertura total de tecnologías "Trending" en GitHub. | 2,400 Activos | 2,500 (Std) + 200 (Pro) | **$18,300** |
| **9** | Automatización | El sistema se auto-mantiene. Agente Auditor mejora calidad de preguntas. | 3,000 Activos | 3,000 (Std) + 300 (Pro) | **$23,700** |
| **10**| Optimización | Refinamiento de UX. Retención de usuarios (Upselling). | 3,600 Activos | 3,200 (Std) + 350 (Pro) | **$26,150** |
| **11**| Consolidación | Expansión a Portugués (Brasil). Mercado LATAM dominado. | 4,500 Activos | 3,500 (Std) + 400 (Pro) | **$29,100** |
| **12**| **Éxito** | **Máquina de Ventas Autónoma**. Foco en Enterprise API. | **+5,000 Activos** | **4,000 (Std) + 500 (Pro)** | **$34,500** |

**Resultado al final del Año 1:**
* **Run Rate Anualizado:** ~$414,000 USD.
* **Activos Digitales:** +5,000 exámenes únicos generando tráfico pasivo.
* **Base de Datos:** +500,000 preguntas generadas y auditadas por IA.

---

## 7. Arquitectura de "Agentización" (AI Workforce)

Para sostener la proyección económica anterior, CDCV no contrata personal humano para la creación de contenido. Emplea una fuerza de trabajo digital (Agentes) orquestada en Python.

### El Ecosistema de Agentes

1.  **Agente Radar (Trend Scout):**
    * Monitoriza APIs de StackOverflow, GitHub Trending y Google Trends.
    * Detecta demanda: *"Surgió una nueva librería de Python 'FastUI'. No hay certificaciones aún."*
    * Acción: Ordena la creación inmediata del curso.

2.  **Agente Arquitecto (Curriculum Builder):**
    * Diseña el temario basado en la documentación oficial de la tecnología detectada.
    * Estructura niveles: Junior, Ssr, Senior.

3.  **Agente Generador (The Factory):**
    * Genera miles de preguntas en formato JSON.
    * Crea variantes de la misma pregunta para evitar memorización.
    * Genera el código de justificación (Feedback educativo).

4.  **Agente Políglota (Localization):**
    * Toma el JSON maestro y lo adapta cultural y lingüísticamente a EN, ES, PT.
    * No traduce literalmente; adapta el contexto técnico.

5.  **Agente Auditor (QA & Fact-Checking):**
    * Ejecuta los snippets de código generados en un entorno sandbox aislado.
    * Si el código da error, descarta la pregunta. Si compila/ejecuta correctamente, aprueba el pase a Producción.

> **Nota:** Esta arquitectura permite que CDCV sea la plataforma más rápida del mundo en ofrecer certificaciones para nuevas tecnologías, llegando al mercado días después de que una tecnología es lanzada (Time-to-Market récord).