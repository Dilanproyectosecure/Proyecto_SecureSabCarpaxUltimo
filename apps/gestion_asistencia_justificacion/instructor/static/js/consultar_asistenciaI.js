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


// Modal reporte
document.addEventListener("DOMContentLoaded", function () {

    // Abrir modal
    window.abrirModalReporte = function () {
        const fechaDesde = document.getElementById('fecha_desde').value;
        const fechaHasta = document.getElementById('fecha_hasta').value;
        if (fechaDesde) document.getElementById('reporte_desde').value = fechaDesde;
        if (fechaHasta) document.getElementById('reporte_hasta').value = fechaHasta;
        document.getElementById('modalReporte').style.display = 'flex';
    };

    // Cerrar modal
    window.cerrarModalReporte = function () {
        document.getElementById('modalReporte').style.display = 'none';
    };

    // Calcular diferencia en meses
    function mesesDiferencia(fechaInicio, fechaFin) {
        let d1 = new Date(fechaInicio);
        let d2 = new Date(fechaFin);
        
        let meses =
            (d2.getFullYear() - d1.getFullYear()) * 12 +
            (d2.getMonth() - d1.getMonth());
        
        if (d2.getDate() < d1.getDate()) {
            meses--;
        }
    
        return meses;
    }

    // Generar reporte
    window.generarReporte = function () {
        const ficha = document.getElementById('ficha').value;
        const desde = document.getElementById('reporte_desde').value;
        const hasta = document.getElementById('reporte_hasta').value;
        const competencia = document.getElementById('competencia').value;
        const estado = document.getElementById('estado').value;
        const aprendiz = document.getElementById('aprendiz').value;

        if (!ficha) {
            alert("Debes seleccionar una ficha primero");
            return;
        }


        if (!desde || !hasta) {
            alert("Debes seleccionar ambas fechas");
            return;
        }

        const d1 = new Date(desde);
        const d2 = new Date(hasta);

        if (d2 < d1) {
            alert("La fecha final no puede ser menor a la inicial");
            return;
        }

        const meses = mesesDiferencia(desde, hasta);

        if (meses < 1) {
            alert("El rango mínimo debe ser de 1 mes");
            return;
        }

        let url = `?reporte=1&reporte_desde=${desde}&reporte_hasta=${hasta}&ficha=${ficha}`;
        if (competencia) url += `&competencia=${competencia}`;
        if (estado) url += `&estado=${estado}`;
        if (aprendiz) url += `&aprendiz=${encodeURIComponent(aprendiz)}`;

        window.location.href = url;
    };

});