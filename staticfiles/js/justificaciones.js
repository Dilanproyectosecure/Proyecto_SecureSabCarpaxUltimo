// justificaciones.js - SOLO para el modal y confirmaciones
// TODO lo demás (filtros, KPIs, tabla) lo maneja Django con GET

document.addEventListener('DOMContentLoaded', function() {
    initModal();
});

// ==================== MODAL DE DETALLE ====================

function initModal() {
    const modal = document.getElementById('justModal');
    const closeBtn = document.getElementById('justModalClose');
    const cancelBtn = document.getElementById('justModalCancel');
    
    if (closeBtn) closeBtn.addEventListener('click', () => modal.style.display = 'none');
    if (cancelBtn) cancelBtn.addEventListener('click', () => modal.style.display = 'none');
    
    window.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });
}

function verDetalle(id) {
    // Redirigir a una página de detalle o mostrar modal con datos del servidor
    // Por ahora, redirigimos a una URL que mostrará el detalle
    window.location.href = `/coordinador/justificaciones/${id}/`;
}

function aprobar(id) {
    if (confirm('¿Aprobar esta justificación?')) {
        document.getElementById('accion-form').action.value = 'aprobar';
        document.getElementById('accion-form').justificacion_id.value = id;
        document.getElementById('accion-form').submit();
    }
}

function rechazar(id) {
    if (confirm('¿Rechazar esta justificación?')) {
        document.getElementById('accion-form').action.value = 'rechazar';
        document.getElementById('accion-form').justificacion_id.value = id;
        document.getElementById('accion-form').submit();
    }
}