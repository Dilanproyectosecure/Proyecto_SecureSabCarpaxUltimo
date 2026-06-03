// Cargar aprendices cuando se selecciona una ficha
document.getElementById('ficha').addEventListener('change', function() {
    const fichaId = this.value;
    const aprendizSelect = document.getElementById('aprendiz');
    
    if (fichaId) {
        // Habilitar select y cargar aprendices
        aprendizSelect.disabled = false;
        aprendizSelect.innerHTML = '<option value="">Cargando...</option>';
        
        fetch(`/api/aprendices-por-ficha/?ficha=${fichaId}`)
            .then(response => response.json())
            .then(data => {
                aprendizSelect.innerHTML = '<option value="">Todos los aprendices</option>';
                data.aprendices.forEach(ap => {
                    aprendizSelect.innerHTML += `<option value="${ap.id}">${ap.nombre} ${ap.apellido} - ${ap.cedula}</option>`;
                });
            });
    } else {
        aprendizSelect.disabled = true;
        aprendizSelect.innerHTML = '<option value="">Seleccione una ficha primero</option>';
    }
});

// Generar reporte
function generarReporte() {
    const tipo = document.getElementById('tipo_reporte').value;
    const ficha = document.getElementById('ficha').value;
    const aprendiz = document.getElementById('aprendiz').value;
    const competencia = document.getElementById('competencia').value;
    const fechaDesde = document.getElementById('fecha_desde').value;
    const fechaHasta = document.getElementById('fecha_hasta').value;
    const estado = document.getElementById('estado').value;
    
    // Construir URL con parámetros
    let params = new URLSearchParams({
        tipo: tipo,
        ficha: ficha,
        aprendiz: aprendiz,
        competencia: competencia,
        fecha_desde: fechaDesde,
        fecha_hasta: fechaHasta,
        estado: estado
    });
    
    // Mostrar loading
    document.getElementById('resultados-container').style.display = 'block';
    document.getElementById('reporte-body').innerHTML = '<tr><td colspan="7" class="text-center">Cargando reporte...</td></tr>';
    
    fetch(`/api/generar-reporte/?${params}`)
        .then(response => response.json())
        .then(data => {
            actualizarTabla(data);
            actualizarResumen(data);
            actualizarInfo(data);
        });
}

// Actualizar tabla con resultados
function actualizarTabla(data) {
    const tbody = document.getElementById('reporte-body');
    tbody.innerHTML = '';
    
    if (data.asistencias.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">No hay resultados para los filtros seleccionados</td></tr>';
        return;
    }
    
    data.asistencias.forEach(a => {
        tbody.innerHTML += `
            <tr>
                <td>${a.fecha}</td>
                <td>${a.ficha}</td>
                <td>${a.aprendiz}</td>
                <td>${a.documento}</td>
                <td>${a.competencia}</td>
                <td><span class="badge-${a.estado}">${a.estado_texto}</span></td>
                <td>${a.instructor}</td>
            </tr>
        `;
    });
}

// Actualizar resumen
function actualizarResumen(data) {
    const resumen = document.getElementById('reporte-resumen');
    resumen.innerHTML = `
        <div class="resumen-item">
            <span class="resumen-label">Total Registros</span>
            <span class="resumen-valor">${data.total}</span>
        </div>
        <div class="resumen-item">
            <span class="resumen-label">Asistieron</span>
            <span class="resumen-valor">${data.asistio}</span>
        </div>
        <div class="resumen-item">
            <span class="resumen-label">Inasistieron</span>
            <span class="resumen-valor">${data.inasistio}</span>
        </div>
        <div class="resumen-item">
            <span class="resumen-label">Retardos</span>
            <span class="resumen-valor">${data.retardo}</span>
        </div>
        <div class="resumen-item">
            <span class="resumen-label">Justificadas</span>
            <span class="resumen-valor">${data.justificada}</span>
        </div>
    `;
}

// Actualizar información del reporte
function actualizarInfo(data) {
    const info = document.getElementById('reporte-info');
    info.innerHTML = `Período: ${data.fecha_desde || 'Inicio'} - ${data.fecha_hasta || 'Actual'}`;
}

// Exportar a Excel
function exportarExcel() {
    // Implementar exportación a Excel
    alert('Funcionalidad de exportación a Excel en desarrollo');
}

// Exportar a PDF
function exportarPDF() {
    // Implementar exportación a PDF
    alert('Funcionalidad de exportación a PDF en desarrollo');
}