// Variables globales del modal
let campoActual = '';

// Función para abrir el modal
function abrirModal(userId, valorActual, campo) {
    campoActual = campo;
    
    // Configurar el modal
    document.getElementById('modal_user_id').value = userId;
    document.getElementById('modal_valor').value = valorActual;
    document.getElementById('modal_campo').value = campo;
    
    // Cambiar el título y etiqueta según el campo
    const titulo = document.getElementById('modalTitulo');
    const label = document.getElementById('modal_label');
    
    if (campo === 'correo') {
        titulo.textContent = 'Editar Correo Electrónico';
        label.textContent = 'Nuevo correo:';
    } else {
        titulo.textContent = 'Editar Teléfono';
        label.textContent = 'Nuevo teléfono:';
    }
    
    // Mostrar el modal
    document.getElementById('editModal').style.display = 'block';
}

// Función para cerrar el modal
function cerrarModal() {
    document.getElementById('editModal').style.display = 'none';
}

// Cerrar modal si se hace clic fuera
window.onclick = function(event) {
    const modal = document.getElementById('editModal');
    if (event.target == modal) {
        cerrarModal();
    }
};