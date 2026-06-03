// Aplicar filtros
function aplicarFiltros() {
    const ficha = document.getElementById('ficha').value;
    const competencia = document.getElementById('competencia').value;
    const fechaDesde = document.getElementById('fecha_desde').value;
    const fechaHasta = document.getElementById('fecha_hasta').value;
    const estado = document.getElementById('estado').value;
    
    let url = window.location.pathname + '?';
    const params = [];
    
    if (ficha) params.push(`ficha=${ficha}`);
    if (competencia) params.push(`competencia=${competencia}`);
    if (fechaDesde) params.push(`fecha_desde=${fechaDesde}`);
    if (fechaHasta) params.push(`fecha_hasta=${fechaHasta}`);
    if (estado) params.push(`estado=${estado}`);
    
    window.location.href = url + params.join('&');
}

// Limpiar filtros
function limpiarFiltros() {
    document.getElementById('ficha').value = '';
    document.getElementById('competencia').value = '';
    document.getElementById('fecha_desde').value = '';
    document.getElementById('fecha_hasta').value = '';
    document.getElementById('estado').value = '';
    aplicarFiltros();
}

// Cambiar página
function cambiarPagina(numero) {
    const url = new URL(window.location.href);
    url.searchParams.set('page', numero);
    window.location.href = url.toString();
}

// Enter en los inputs
document.querySelectorAll('.filtro-input').forEach(input => {
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            aplicarFiltros();
        }
    });
});