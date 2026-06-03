// Función para actualizar por fecha
function actualizarAsistencia() {
    const fecha = document.getElementById('fecha').value;
    const fichaId = document.querySelector('.fecha-selector').dataset.fichaId
    if (!fecha) {
        alert('Seleccione una fecha');
        return;
    }
    window.location.href = `?ficha=${fichaId}&fecha=${fecha}`;
}

// Marcar select cuando cambia
document.querySelectorAll('.asistencia-select').forEach(select => {
    select.addEventListener('change', function() {
        this.classList.add('changed');
        setTimeout(() => {
            this.classList.remove('changed');
        }, 1000);
    });
});