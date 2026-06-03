// Usar la variable global definida en el template
const csrftoken = window.csrfToken;
let invitadoIdSeleccionado = null;

function abrirModal(id) {
    invitadoIdSeleccionado = id;
    document.getElementById('modalInvitado').classList.add('active');
}

function cerrarModal() {
    document.getElementById('modalInvitado').classList.remove('active');
    invitadoIdSeleccionado = null;
}

function registrarIngreso() {
    if (!invitadoIdSeleccionado) return;
    
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/vigilante/entrada-invitado/${invitadoIdSeleccionado}/`;
    
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrftoken;
    
    form.appendChild(csrfInput);
    document.body.appendChild(form);
    form.submit();
}

function registrarSalida() {
    if (!invitadoIdSeleccionado) return;
    
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/vigilante/salida-invitado/${invitadoIdSeleccionado}/`;
    
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrftoken;
    
    form.appendChild(csrfInput);
    document.body.appendChild(form);
    form.submit();
}

// Cerrar modal al hacer click fuera
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('modalInvitado');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                cerrarModal();
            }
        });
    }
});