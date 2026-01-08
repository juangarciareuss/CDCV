/* core/static/core/js/gym_engine.js */

document.addEventListener('DOMContentLoaded', () => {
    // 1. CONFIGURACIÓN DE SONIDOS (Efectos sutiles)
    // Usamos sonidos cortos para feedback inmediato
    const soundSuccess = new Audio('https://assets.mixkit.co/sfx/preview/mixkit-arcade-game-jump-coin-216.mp3');
    const soundError = new Audio('https://assets.mixkit.co/sfx/preview/mixkit-wrong-answer-fail-notification-946.mp3');
    const soundLevelUp = new Audio('https://assets.mixkit.co/sfx/preview/mixkit-winning-chimes-2015.mp3');

    // Volumen suave para no asustar
    soundSuccess.volume = 0.4;
    soundError.volume = 0.3;
    soundLevelUp.volume = 0.5;

    let isProcessing = false;
    let currentPreguntaId = null;

    // 2. REFERENCIAS A LA INTERFAZ (DOM)
    const ui = {
        questionText: document.getElementById('q-text'),
        optionsContainer: document.getElementById('options-area'),
        levelNumber: document.getElementById('level-number'),
        difficultyText: document.getElementById('difficulty-text'), // Texto en la barra dorada
        feedbackModal: document.getElementById('feedback-modal'),
        feedbackTitle: document.getElementById('feedback-title'),
        feedbackContent: document.getElementById('feedback-content'),
        feedbackDelta: document.getElementById('feedback-delta'),
        nextBtn: document.getElementById('next-btn'),
        timerDisplay: document.getElementById('timer')
    };

    // Iniciar
    cargarPregunta();

    // Listener para el botón "Siguiente"
    ui.nextBtn.addEventListener('click', cargarPregunta);

    // --- FUNCIONES PRINCIPALES ---

    function cargarPregunta() {
        // Reset Visual
        ui.feedbackModal.classList.add('d-none'); // Ocultar feedback
        ui.optionsContainer.style.opacity = '1';
        ui.optionsContainer.style.pointerEvents = 'auto'; // Reactivar clicks
        
        // Loader elegante
        ui.questionText.innerHTML = '<span class="text-muted"><i class="fas fa-circle-notch fa-spin me-2"></i>Calibrando siguiente desafío...</span>';
        ui.optionsContainer.innerHTML = '';

        // Llamada al Backend
        fetch(`/entrenamiento/api/pregunta/${TEMA_ID}/`)
            .then(r => {
                if(!r.ok) throw new Error("Fin");
                return r.json();
            })
            .then(data => renderizar(data))
            .catch(err => mostrarFinSesion());
    }

    function renderizar(data) {
        currentPreguntaId = data.id;
        
        // 1. Mostrar Texto con animación suave
        ui.questionText.style.opacity = 0;
        ui.questionText.innerText = data.texto;
        fadeIn(ui.questionText);

        // 2. Actualizar Badge de Dificultad (En la barra dorada)
        const niveles = ['Básico', 'Intermedio', 'Avanzado', 'Experto', 'Maestro'];
        // Math.floor para asegurar índice entero. Restamos 1 porque arrays empiezan en 0
        const difLabel = niveles[Math.floor(data.dificultad) - 1] || 'Adaptativo';
        ui.difficultyText.innerText = `${difLabel} (${data.dificultad})`;

        // 3. Generar Botones de Opción (Grid 2x2)
        ui.optionsContainer.innerHTML = '';
        
        Object.entries(data.opciones).forEach(([key, value], index) => {
            const btn = document.createElement('div');
            btn.className = 'option-btn';
            
            // SOLUCIÓN NUEVA: Animación directa sin depender de CSS
            btn.style.opacity = '0';
            btn.style.transform = 'translateY(10px)';
            btn.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            
            // Pequeño retraso matemático para el efecto cascada
            setTimeout(() => {
                btn.style.opacity = '1';
                btn.style.transform = 'translateY(0)';
            }, index * 100 + 50); // 100ms * índice

            btn.innerHTML = `
                <div class="option-key">${key}</div>
                <div style="line-height: 1.3;">${value}</div>
            `;
            
            // Click Event
            btn.onclick = () => enviarRespuesta(key, btn);
            
            ui.optionsContainer.appendChild(btn);
        });
    }

    function enviarRespuesta(key, btnElement) {
        if (isProcessing) return;
        isProcessing = true;
        
        // Bloquear UI para evitar doble respuesta
        ui.optionsContainer.style.pointerEvents = 'none';
        
        // Efecto visual instantáneo de "Pensando..."
        btnElement.style.borderColor = '#D4AF37'; // Dorado momentáneo
        btnElement.style.backgroundColor = '#fffbf0';

        fetch('/entrenamiento/api/responder/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ pregunta_id: currentPreguntaId, respuesta: key })
        })
        .then(r => r.json())
        .then(data => procesarResultado(data, key, btnElement));
    }

    function procesarResultado(data, userKey, btnElement) {
        isProcessing = false;

        // 1. Determinar Estilos (Iconos y Colores)
        let iconHtml, colorClass, titleText;
        
        if (data.correcto) {
            btnElement.classList.add('correct');
            playSound(soundSuccess);
            if (data.delta > 0.4) setTimeout(() => playSound(soundLevelUp), 200);
            
            // Estilo Éxito
            colorClass = 'text-success';
            iconHtml = '<i class="fas fa-check-circle"></i>';
            titleText = '¡Correcto!';
        } else {
            btnElement.classList.add('incorrect');
            playSound(soundError);
            
            // Estilo Error
            colorClass = 'text-danger';
            iconHtml = '<i class="fas fa-times-circle"></i>';
            titleText = 'Incorrecto';

            // Resaltar la correcta discretamente
            document.querySelectorAll('.option-btn').forEach(b => {
                if(b.innerText.startsWith(data.respuesta_correcta_key)) {
                    b.classList.add('correct');
                    b.style.opacity = '0.6'; 
                }
            });
        }

        // 2. Animar el Nivel (Header)
        animarNumero(ui.levelNumber, parseFloat(ui.levelNumber.innerText), data.nivel_nuevo);

        // 3. INYECTAR EL HTML COMPACTO (Aquí está la magia del diseño)
        // Usamos innerHTML para reestructurar la caja totalmente
        ui.feedbackModal.className = `feedback-box ${colorClass.replace('text-', 'border-')}`; // Borde sutil del color
        ui.feedbackModal.style.borderLeft = "none"; // Quitamos el borde grueso viejo
        ui.feedbackModal.style.borderLeft = `4px solid ${data.correcto ? '#10b981' : '#ef4444'}`;

        ui.feedbackModal.innerHTML = `
            <div class="feedback-icon ${colorClass}">
                ${iconHtml}
            </div>
            
            <div class="feedback-body">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <h6 class="fw-bold m-0 ${colorClass}">${titleText}</h6>
                    <span class="fw-bold small ${data.delta >= 0 ? 'text-success' : 'text-danger'}">
                        ${data.delta >= 0 ? '+' : ''}${data.delta.toFixed(2)}
                    </span>
                </div>
                
                <p class="small text-secondary mb-2" style="line-height: 1.3;">
                    ${data.justificacion || "Sin justificación."}
                </p>
                
                <button id="btn-next-action" class="btn btn-dark w-100 btn-compact fw-bold shadow-sm">
                    Siguiente <i class="fas fa-arrow-right ms-2"></i>
                </button>
            </div>
        `;

        // 4. Reactivar el botón (Como recreamos el HTML, el listener viejo murió)
        document.getElementById('btn-next-action').addEventListener('click', cargarPregunta);

        // 5. Mostrar
        ui.feedbackModal.classList.remove('d-none');
    }
    // --- UTILIDADES ---

    function animarNumero(elemento, inicio, fin) {
        const duracion = 800; // ms
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duracion, 1);
            
            // Easing function (easeOutQuart) para que frene suave al final
            const ease = 1 - Math.pow(1 - progress, 4);
            
            const actual = inicio + (fin - inicio) * ease;
            elemento.innerText = actual.toFixed(2).replace('.', ',');

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                elemento.innerText = fin.toFixed(1).replace('.', ','); // Asegurar valor final limpio
            }
        }
        requestAnimationFrame(update);
    }

    function playSound(audioObj) {
        // Reiniciar audio por si se toca rápido
        audioObj.currentTime = 0;
        // Catch para evitar errores si el navegador bloquea autoplay
        audioObj.play().catch(e => console.log("Audio bloqueado por política del navegador"));
    }

    function fadeIn(element) {
        let op = 0.1;  // initial opacity
        element.style.opacity = op;
        const timer = setInterval(function () {
            if (op >= 1){
                clearInterval(timer);
            }
            element.style.opacity = op;
            element.style.filter = 'alpha(opacity=' + op * 100 + ")";
            op += op * 0.1;
        }, 10);
    }

    function mostrarFinSesion() {
        ui.optionsContainer.innerHTML = '';
        ui.questionText.innerHTML = `<div class="text-center py-5">
            <i class="fas fa-flag-checkered fa-3x text-warning mb-3"></i>
            <h3>¡Sesión Completada!</h3>
            <p class="text-muted">Has respondido todas las preguntas disponibles para tu nivel.</p>
            <a href="/" class="btn btn-dark mt-2">Volver al Inicio</a>
        </div>`;
        ui.feedbackModal.classList.add('d-none');
    }
});