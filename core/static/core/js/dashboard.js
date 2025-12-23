/**
 * 🧠 Dashboard Admin Logic
 * Encargado de la comunicación con la API de IA y gestión de cursos.
 */

// 1. Utilidad para obtener el Token CSRF desde el HTML
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// ------------------------------------------------------------------
// FUNCIONALIDAD 1: Crear un Curso Nuevo desde Cero
// ------------------------------------------------------------------
async function crearCursoNuevo() {
    const input = document.getElementById('inputNicho');
    const btn = document.getElementById('btnCrear');
    const nicho = input.value;

    if (!nicho) {
        alert("Por favor escribe un tema.");
        return;
    }

    // Feedback Visual
    btn.disabled = true;
    btn.innerHTML = "🏗️ Construyendo... (Revisa Consola F12)";
    btn.style.opacity = "0.7";
    
    console.log("🚀 Enviando petición al servidor para:", nicho);

    try {
        const response = await fetch('/dashboard/crear-curso/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken() // <--- USO DEL TOKEN SEGURO
            },
            body: JSON.stringify({ nicho: nicho })
        });

        // Lectura forense de la respuesta
        const textoCrudo = await response.text();
        console.log("📩 Estado HTTP:", response.status);
        // console.log("🔥 RAW:", textoCrudo); // Descomentar para debug extremo

        let data;
        try {
            data = JSON.parse(textoCrudo);
        } catch (e) {
            console.error("❌ ERROR DE PARSEO JSON:", e);
            throw new Error("El servidor devolvió HTML en lugar de JSON (Posible error 500).");
        }

        if (data.status === 'success') {
            alert("¡ÉXITO! " + data.message);
            location.reload(); 
        } else {
            alert("Error del sistema: " + data.message);
        }

    } catch (err) {
        console.error("💀 ERROR FATAL:", err);
        alert("Ocurrió un error. Revisa la consola.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = "✨ Crear Producto";
        btn.style.opacity = "1";
    }
}

// ------------------------------------------------------------------
// FUNCIONALIDAD 2: Ejecutar IA de Curación (Rellenar Preguntas)
// ------------------------------------------------------------------
function ejecutarCuracion(cursoId) {
    const btn = document.getElementById(`btn-ia-${cursoId}`);
    const textoOriginal = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = "⏳ Pensando... (Esto toma ~10s)";
    btn.style.backgroundColor = "#6c757d";

    fetch(`/dashboard/curar-ia/${cursoId}/`)
        .then(response => {
            if (!response.ok) throw new Error('Error en la red o servidor');
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                alert("✅ ¡Misión Cumplida!\n\n" + data.reporte.join("\n"));
                location.reload();
            } else {
                alert("❌ Error del Agente: " + data.message);
                restaurarBoton(btn, textoOriginal);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert("❌ Error de conexión.");
            restaurarBoton(btn, textoOriginal);
        });
}

function restaurarBoton(btn, texto) {
    btn.disabled = false;
    btn.innerHTML = texto;
    btn.style.backgroundColor = "";
}

// ------------------------------------------------------------------
// FUNCIONALIDAD 3: Activar / Desactivar Curso (Switch)
// ------------------------------------------------------------------
function toggleCurso(id) {
    fetch(`/dashboard/toggle-status/${id}/`)
    .then(r => r.json())
    .then(data => {
        if(data.status === 'success') {
            console.log(data.mensaje); 
        } else {
            alert("Error al cambiar estado");
            location.reload();
        }
    });
}


// ------------------------------------------------------------------
// FUNCIONALIDAD 4: Eliminar Curso
// ------------------------------------------------------------------
function eliminarCurso(id, nombre) {
    if(!confirm(`⚠️ ¿Estás SEGURO de eliminar el curso "${nombre}"?\n\nEsta acción borrará:\n- El curso\n- Sus preguntas\n- Los exámenes de usuarios vinculados.`)) {
        return;
    }

    // 1. OBTENER EL TOKEN DESDE EL HTML (ESTA ES LA CLAVE)
    // Buscamos la etiqueta meta que agregaste en el head
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = metaToken ? metaToken.getAttribute('content') : '';

    fetch(`/dashboard/eliminar-curso/${id}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // 2. USAR LA VARIABLE, NO EL CÓDIGO {{...}}
            'X-CSRFToken': csrfToken 
        }
    })
    .then(response => {
        // Validación extra por si devuelve HTML de error (403/500)
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            alert("🗑️ Curso eliminado correctamente.");
            location.reload();
        } else {
            alert("❌ Error: " + data.message);
        }
    })
    .catch(err => {
        console.error(err);
        alert("Error al intentar eliminar. Revisa la consola (F12) para más detalles.");
    });
}