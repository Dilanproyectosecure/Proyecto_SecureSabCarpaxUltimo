// Variables globales
let justificacionActual = null;

// Aplicar filtros
function aplicarFiltros() {
    const ficha = document.getElementById('ficha').value;
    const jornada = document.getElementById('jornada').value;
    const estado = document.getElementById('estado').value;
    const fechaDesde = document.getElementById('fecha_desde').value;
    const fechaHasta = document.getElementById('fecha_hasta').value;
    const aprendiz = document.getElementById('aprendiz').value;
    
    let url = window.location.pathname + '?';
    let params = [];
    
    if (ficha) params.push(`ficha=${ficha}`);
    if (jornada) params.push(`jornada=${jornada}`);
    if (estado) params.push(`estado=${estado}`);
    if (fechaDesde) params.push(`fecha_desde=${fechaDesde}`);
    if (fechaHasta) params.push(`fecha_hasta=${fechaHasta}`);
    if (aprendiz) params.push(`aprendiz=${encodeURIComponent(aprendiz)}`);
    
    window.location.href = url + params.join('&');
}

// Limpiar filtros
function limpiarFiltros() {
    window.location.href = window.location.pathname;
}

// Cambiar página
function cambiarPagina(numero) {
    const url = new URL(window.location.href);
    url.searchParams.set('page', numero);
    window.location.href = url.toString();
}

// Aprobar justificación directamente (sin modal)
function aprobarDirecto(id) {
    if (confirm('¿Aprobar esta justificación?')) {
        var form = document.createElement('form');
        form.method = 'POST';
        form.action = '/instructor/procesar-justificacion/';
        
        var csrf = document.createElement('input');
        csrf.type = 'hidden';
        csrf.name = 'csrfmiddlewaretoken';
        csrf.value = document.querySelector('[name=csrfmiddlewaretoken]').value;
        form.appendChild(csrf);
        
        var inputId = document.createElement('input');
        inputId.type = 'hidden';
        inputId.name = 'justificacion_id';
        inputId.value = id;
        form.appendChild(inputId);
        
        var inputAccion = document.createElement('input');
        inputAccion.type = 'hidden';
        inputAccion.name = 'accion';
        inputAccion.value = 'aprobar';
        form.appendChild(inputAccion);
        
        document.body.appendChild(form);
        form.submit();
    }
}

// Abrir modal para rechazar
function abrirModalRechazar(id) {
    justificacionActual = id;
    document.getElementById('modalTitulo').textContent = 'Rechazar Justificación';
    document.getElementById('justificacion_id').value = id;
    document.getElementById('observaciones').value = '';
    document.getElementById('modalJustificacion').style.display = 'block';
}

// Cerrar modal
function cerrarModal() {
    document.getElementById('modalJustificacion').style.display = 'none';
}

// Cerrar modal al hacer clic fuera
window.onclick = function(event) {
    const modal = document.getElementById('modalJustificacion');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}