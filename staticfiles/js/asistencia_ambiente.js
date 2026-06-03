// asistencia_ambiente.js - Solo para el botón limpiar
document.addEventListener('DOMContentLoaded', function() {
    const clearBtn = document.getElementById('clearAmbienteFiltersBtn');
    
    if (clearBtn) {
        clearBtn.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = window.location.pathname;
        });
    }
});