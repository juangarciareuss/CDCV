📋 Inventario Maestro de Funcionalidades - CDCV
Este documento actúa como el mapa de ruta técnico del proyecto. Cada funcionalidad está listada para ser verificada ([x]) a medida que se implementa y prueba.

🛠️ Módulo 1: Administración y Gestión de Contenido (Backoffice)
Funciones para el administrador y la gestión de la "Fábrica de Cursos".

[ ] Gestión de Cursos (CRUD Básico)

[ ] Crear un nuevo curso (Título, Slug, Descripción, Nivel).

[ ] Editar metadata básica del curso (Precio, Idioma, Estado Activo/Inactivo).

[ ] Eliminar curso (Borrado lógico/Soft delete).

[ ] Visualizar lista de todos los cursos en el Admin.

[ ] Gestión de la Estructura del Examen

[ ] Definir JSON de reglas (Cantidad de preguntas, Tiempo límite, Nota aprobación).

[ ] Validar sintaxis del JSON en el guardado.

[ ] Gestión de Preguntas (Banco de Datos)

[ ] Crear pregunta manual (Enunciado, Opciones, Respuesta Correcta).

[ ] Editar texto de una pregunta existente.

[ ] Asignar etiquetas/tags a una pregunta (Tema, Dificultad).

[ ] Eliminar pregunta.

[ ] Ingesta Masiva (AI Factory)

[ ] Script para importar curso completo desde JSON (importar_curso).

[ ] Validación automática de duplicados al importar.

[ ] Carga de imágenes asociadas a preguntas (si aplica).

🔐 Módulo 2: Identidad y Acceso (Auth)
Funciones relacionadas con la seguridad y la cuenta del usuario.

[ ] Registro e Ingreso

[ ] Registro de usuario con Correo y Contraseña.

[ ] Login clásico (Email/Pass).

[ ] Login Social con Google (OAuth2).

[ ] Logout (Cierre de sesión seguro).

[ ] Gestión de Contraseñas

[ ] Flujo de "Olvidé mi contraseña" (Solicitud de email).

[ ] Pantalla de establecimiento de nueva contraseña.

[ ] Seguridad

[ ] Verificación de correo electrónico (Código o Link).

[ ] Protección CSRF en todos los formularios.

[ ] Bloqueo de rutas protegidas (@login_required).

🛍️ Módulo 3: Vitrina y Compra (Marketplace)
Funciones visibles para el usuario antes de tomar el examen.

[ ] Navegación Pública

[ ] Homepage con listado de cursos destacados/nuevos.

[ ] Buscador de cursos por palabra clave.

[ ] Filtros por Categoría, Nivel o Precio.

[ ] Detalle del Producto

[ ] Página de detalle del curso (Descripción, qué incluye, precio).

[ ] Visualización de temario o habilidades a validar.

[ ] Pasarela de Pagos (PayPal)

[ ] Botón de pago dinámico (SDK PayPal).

[ ] Procesamiento de respuesta exitosa (Webhook/Return URL).

[ ] Manejo de errores de pago o cancelaciones.

[ ] Generación de registro de "Orden de Compra" en BD.

📝 Módulo 4: Motor de Exámenes (Core)
La experiencia principal de evaluación.

[ ] Inicialización

[ ] Verificación de elegibilidad (¿Pagó el usuario?).

[ ] Generación de intento de examen (Snapshot de preguntas aleatorias).

[ ] Pantalla de instrucciones y bienvenida al examen.

[ ] Ejecución (Runtime)

[ ] Renderizado de pregunta (Texto + Opciones).

[ ] Mecanismo de selección de respuesta (Radio buttons).

[ ] Navegación entre preguntas (Siguiente/Anterior - Opcional).

[ ] Guardado temporal de respuestas (para evitar pérdida por desconexión).

[ ] Cronómetro / Temporizador visual (Cuenta regresiva).

[ ] Forzar envío automático al agotarse el tiempo.

[ ] Cierre y Cálculos

[ ] Cálculo de puntaje final (Score).

[ ] Determinación de estado (Aprobado/Reprobado).

[ ] Guardado de intento finalizado en BD.

📜 Módulo 5: Certificación y Resultados
El valor entregable al usuario.

[ ] Visualización de Resultados

[ ] Pantalla de feedback inmediato (Nota obtenida).

[ ] Detalle de respuestas correctas/incorrectas (Opcional según configuración).

[ ] Generación de Documentos

[ ] Generar PDF del certificado (Diseño corporativo).

[ ] Incrustar datos dinámicos (Nombre, Fecha, ID Único).

[ ] Generar código QR único apuntando a validación.

[ ] Validación Pública

[ ] Ruta pública /verificar/<uuid>.

[ ] Vista de validación (Muestra: "Este certificado es legítimo").

[ ] Manejo de error para UUIDs inexistentes.

👤 Módulo 6: Panel de Usuario (Dashboard)
El espacio personal del cliente.

[ ] Mi Perfil

[ ] Editar datos personales (Nombre para el diploma).

[ ] Ver historial de compras.

[ ] Mis Certificaciones

[ ] Listado de exámenes aprobados.

[ ] Botón para descargar PDF nuevamente.

[ ] Botón para compartir en LinkedIn (Enlace directo).

⚙️ Módulo 7: Sistema e Infraestructura
Configuraciones técnicas y mantenimiento.

[ ] Configuración

[ ] Variables de entorno separadas (Dev/Prod).

[ ] Configuración de Base de Datos (SQLite/Postgres).

[ ] Configuración de Archivos Estáticos (Whitenoise).

[ ] Monitoreo y Analytics

[ ] Dashboard simple de métricas (Total ventas, Tasa de aprobación).

[ ] Registro de logs de errores (Sentry o logs nativos).

🚀 Futuras Implementaciones (Roadmap IA)
Funciones pendientes para la Fase 2 (Agentización).

[ ] Agente Radar: Detector de tendencias en GitHub/StackOverflow.

[ ] Agente Constructor: Generador automático de JSON de preguntas.

[ ] Agente Auditor: Validador de código en Sandbox.

[ ] Sistema Multi-idioma (i18n) para la interfaz.