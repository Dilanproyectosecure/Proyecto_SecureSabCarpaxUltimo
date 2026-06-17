// ===== INICIALIZAR TODOS LOS ELEMENTOS =====
document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Inicializar botones de novedades
    document.querySelectorAll('.btn-ver-novedades').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            const nombre = this.getAttribute('data-nombre');
            const tiene3 = this.getAttribute('data-tiene3');
            const tiene5 = this.getAttribute('data-tiene5');
            const total = this.getAttribute('data-total');
            
            mostrarNovedades(id, nombre, tiene3, tiene5, total);
        });
    });
    
    // 2. Inicializar enlaces editables (correo y teléfono)
    document.querySelectorAll('.editar-link').forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const id = this.getAttribute('data-id');
            const tipo = this.getAttribute('data-tipo');
            let valor;
            
            if (tipo === 'correo') {
                valor = this.getAttribute('data-correo');
            } else if (tipo === 'telefono') {
                valor = this.getAttribute('data-telefono');
            }
            
            if (typeof abrirModal === 'function') {
                abrirModal(id, valor, tipo);
            } else {
                console.error('La función abrirModal no está definida');
            }
        });
    });
});

// ===== MOSTRAR NOVEDADES EN MODAL =====
function mostrarNovedades(idUsuario, nombreCompleto, tiene3, tiene5, totalInasistencias) {
    // Convertir strings a booleanos
    const tiene3Consecutivas = tiene3 === 'true';
    const tiene5Inasistencias = tiene5 === 'true';
    
    // Crear contenido del modal
    let novedadesHTML = '';
    
    if (tiene3Consecutivas) {
        novedadesHTML += `
            <div class="novedad-item">
                <div class="novedad-icono"></div>
                <div class="novedad-texto">
                    <strong>3 Inasistencias Consecutivas</strong>
                    <p>El aprendiz ha acumulado 3 inasistencias sin justificar de manera consecutiva. 
                    Se recomienda solicitar la justificación correspondiente para evitar cancelación de matrícula.</p>
                </div>
            </div>
        `;
    }
    
    if (tiene5Inasistencias) {
        novedadesHTML += `
            <div class="novedad-item">
                <div class="novedad-icono"></div>
                <div class="novedad-texto">
                    <strong>5+ Inasistencias Totales</strong>
                    <p>El aprendiz ha acumulado ${totalInasistencias} días de inasistencia sin justificar en el trimestre actual. 
                    Esto excede el límite máximo permitido (5 faltas).</p>
                </div>
            </div>
        `;
    }
    
    // Si por algún error no hay novedades (no debería pasar)
    if (!novedadesHTML) {
        novedadesHTML = `
            <div class="novedad-item">
                <div class="novedad-icono">✅</div>
                <div class="novedad-texto">
                    <strong>Sin novedades</strong>
                    <p>El aprendiz no presenta alertas de inasistencia en este momento.</p>
                </div>
            </div>
        `;
    }
    
    // Construir modal completo
    const modalHTML = `
        <div class="modal-novedades-overlay" id="modalNovedades" onclick="cerrarModalNovedades(event)">
            <div class="modal-novedades-content" onclick="event.stopPropagation()">
                <div class="modal-novedades-header">
                    <h3>
                        
                        Novedades de ${nombreCompleto}
                    </h3>
                    <button class="btn-cerrar-modal" onclick="cerrarModalNovedades()">
                        <i class="bi bi-x-circle-fill"></i>
                    </button>
                </div>
                <div class="modal-novedades-body">
                    ${novedadesHTML}
                </div>
            </div>
        </div>
    `;
    
    // Eliminar modal existente si hay uno
    const modalExistente = document.getElementById('modalNovedades');
    if (modalExistente) {
        modalExistente.remove();
    }
    
    // Insertar modal en el DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Bloquear scroll del body
    document.body.style.overflow = 'hidden';
}

// ===== CERRAR MODAL DE NOVEDADES =====
function cerrarModalNovedades(event) {
    const modal = document.getElementById('modalNovedades');
    if (modal) {
        modal.remove();
        document.body.style.overflow = 'auto';
    }
}

// ===== CERRAR MODAL CON TECLA ESC =====
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('modalNovedades');
        if (modal) {
            modal.remove();
            document.body.style.overflow = 'auto';
        }
    }
});