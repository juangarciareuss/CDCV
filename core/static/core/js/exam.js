/* core/static/core/js/exam.js */

document.addEventListener("DOMContentLoaded", function() {
    
    // --- VARIABLES GLOBALES ---
    let currentSlide = 0;
    const slides = document.querySelectorAll('.question-card');
    const totalSlides = slides.length;
    const progressBar = document.getElementById('progressBar');
    const timeDisplay = document.getElementById('timeDisplay');
    const timerBadge = document.getElementById('timerBadge');
    
    // TIEMPO: 2 minutos (120 seg) por pregunta. 
    // Puedes ajustar el multiplicador aquí.
    let timeRemaining = totalSlides * 120; 

    // --- FUNCIONES UI ---

    function updateUI(index) {
        // Ocultar todas
        slides.forEach(s => {
            s.classList.remove('active');
            s.style.opacity = '0';
        });

        // Mostrar actual con leve delay para suavidad
        setTimeout(() => {
            if(slides[index]) {
                slides[index].classList.add('active');
                slides[index].style.opacity = '1';
            }
        }, 50);

        // Actualizar barra superior
        const percent = ((index + 1) / totalSlides) * 100;
        if(progressBar) progressBar.style.width = `${percent}%`;
    }

    // --- SELECCIÓN VISUAL (Click en Opciones) ---
    // Esta función se expone al objeto window para poder llamarla desde el HTML onclick=""
    window.selectVisual = function(label) {
        // Limpiar seleccionados previos en esta tarjeta
        const container = label.closest('.options-grid');
        container.querySelectorAll('.option-item').forEach(l => l.classList.remove('selected'));
        
        // Marcar actual
        label.classList.add('selected');
        
        // Asegurar que el input radio está marcado
        const input = label.querySelector('input');
        if(input) input.checked = true;
    };

    // --- NAVEGACIÓN ---

    window.nextQuestion = function() {
        const currentCard = slides[currentSlide];
        const checked = currentCard.querySelector('input:checked');
        
        // Validación: ¿Respondió?
        if (!checked) {
            currentCard.style.animation = "shake 0.4s ease";
            setTimeout(() => currentCard.style.animation = "", 400);
            return;
        }

        if (currentSlide < totalSlides - 1) {
            currentSlide++;
            updateUI(currentSlide);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    window.prevQuestion = function() {
        if (currentSlide > 0) {
            currentSlide--;
            updateUI(currentSlide);
        }
    };

    window.submitExam = function() {
        const currentCard = slides[currentSlide];
        const checked = currentCard.querySelector('input:checked');
        
        if (!checked) {
            alert("⚠️ Por favor selecciona una respuesta antes de finalizar.");
            return;
        }

        if (confirm("¿Confirmas que deseas enviar tus respuestas y terminar?")) {
            document.getElementById('examForm').submit();
        }
    };

    // --- CRONÓMETRO ---
    if(timeDisplay) {
        const interval = setInterval(() => {
            const m = Math.floor(timeRemaining / 60);
            const s = timeRemaining % 60;
            
            timeDisplay.innerText = `${m}:${s < 10 ? '0' : ''}${s}`;
            
            // Alerta visual (< 10% del tiempo)
            if (timeRemaining < (totalSlides * 120 * 0.1)) {
                timerBadge.classList.add('warning');
            }

            if (timeRemaining <= 0) {
                clearInterval(interval);
                alert("⏰ El tiempo ha finalizado. Se enviarán tus respuestas.");
                document.getElementById('examForm').submit();
            }
            timeRemaining--;
        }, 1000);
    }

    // --- TECLADO (Atajos) ---
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (currentSlide < totalSlides - 1) nextQuestion();
            else submitExam();
        }
        
        // Teclas 1, 2, 3, 4
        if (['1','2','3','4'].includes(e.key)) {
            const card = slides[currentSlide];
            const options = card.querySelectorAll('.option-item');
            const idx = parseInt(e.key) - 1;
            if(options[idx]) options[idx].click();
        }
    });

    // --- INICIALIZACIÓN ---
    updateUI(0);
});