(function () {
    'use strict';

    const formulario = document.getElementById('formularioCrear');
    const btnMostrar = document.getElementById('btnMostrarFormulario');
    const btnCerrar = document.getElementById('btnCerrarFormulario');
    const btnCancelar = document.getElementById('btnCancelarFormulario');

    if (formulario && btnMostrar) {
        btnMostrar.addEventListener('click', function () {
            formulario.style.display = 'block';
            setTimeout(() => formulario.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50);
        });
    }

    function cerrarFormulario() {
        if (!formulario) return;
        formulario.style.display = 'none';
        const form = formulario.querySelector('form');
        if (form) form.reset();
    }

    if (btnCerrar) btnCerrar.addEventListener('click', cerrarFormulario);
    if (btnCancelar) btnCancelar.addEventListener('click', cerrarFormulario);
})();

function toggleRolFields() {
    const selectRol = document.getElementById('selectRol');
    const divFicha = document.getElementById('divFicha');
    const divFichasIns = document.getElementById('divFichasInstructor');
    if (!selectRol) return;
    var texto = selectRol.options[selectRol.selectedIndex]?.text || '';
    var rolLower = texto.toLowerCase();
    if (divFicha) divFicha.style.display = rolLower === 'aprendiz' ? 'block' : 'none';
    if (divFichasIns) divFichasIns.style.display = rolLower === 'instructor' ? 'block' : 'none';
}
document.addEventListener('DOMContentLoaded', function () {
    var sel = document.getElementById('selectRol');
    if (sel) { toggleRolFields(); sel.addEventListener('change', toggleRolFields); }
});

var cmUsuarios = [];

function cmCambiarRol() {
    var rol = document.getElementById('cmRol').value;
    document.getElementById('cmFormFields').style.display = rol ? 'block' : 'none';
    document.getElementById('cmFieldFicha').style.display = rol === 'aprendiz' ? 'block' : 'none';
    document.getElementById('cmFieldFichasInstructor').style.display = rol === 'instructor' ? 'block' : 'none';
}

function cmAgregarFila() {
    var rol = document.getElementById('cmRol').value;
    if (!rol) { alert('Seleccione un tipo de usuario'); return; }
    var doc = document.getElementById('cmDoc').value.trim();
    var nombre = document.getElementById('cmNombre').value.trim();
    var apellido = document.getElementById('cmApellido').value.trim();
    if (!doc || !nombre) { alert('Documento y nombre son obligatorios'); return; }

    var email = document.getElementById('cmEmail').value.trim();
    var telefono = document.getElementById('cmTelefono').value.trim();
    var tipoDoc = document.getElementById('cmTipoDoc').value;

    var fichasLabel = '';
    var fichasIds = [];

    if (rol === 'aprendiz') {
        var selFicha = document.getElementById('cmFicha');
        if (selFicha.value) {
            fichasLabel = selFicha.options[selFicha.selectedIndex].text;
        }
    } else if (rol === 'instructor') {
        var selFichas = document.getElementById('cmFichasInstructor');
        var selected = [];
        for (var i = 0; i < selFichas.options.length; i++) {
            if (selFichas.options[i].selected) {
                selected.push(selFichas.options[i]);
            }
        }
        if (selected.length < 1 || selected.length > 5) {
            alert('El instructor debe tener entre 1 y 5 fichas seleccionadas');
            return;
        }
        fichasLabel = selected.map(function(o) { return o.text; }).join(', ');
        fichasIds = selected.map(function(o) { return o.value; });
    }

    var usuario = {
        tipo_documento: tipoDoc,
        cedula: doc,
        nombre: nombre,
        apellido: apellido,
        correo: email,
        telefono: telefono,
        ficha_id: (rol === 'aprendiz' && document.getElementById('cmFicha').value) ? document.getElementById('cmFicha').value : null,
        fichas_ids: fichasIds,
        fichasLabel: fichasLabel
    };
    cmUsuarios.push(usuario);
    cmRenderTabla();

    document.getElementById('cmDoc').value = '';
    document.getElementById('cmNombre').value = '';
    document.getElementById('cmApellido').value = '';
    document.getElementById('cmEmail').value = '';
    document.getElementById('cmTelefono').value = '';
    if (rol === 'aprendiz') document.getElementById('cmFicha').value = '';
    if (rol === 'instructor') {
        var sel = document.getElementById('cmFichasInstructor');
        for (var i = 0; i < sel.options.length; i++) sel.options[i].selected = false;
    }
}

function cmEliminarFila(index) {
    cmUsuarios.splice(index, 1);
    cmRenderTabla();
}

function cmRenderTabla() {
    var tbody = document.getElementById('cmTableBody');
    var container = document.getElementById('cmTableContainer');
    var btnEnviar = document.getElementById('cmBtnEnviar');
    var countSpan = document.getElementById('cmCount');
    if (!tbody) return;

    tbody.innerHTML = '';
    if (cmUsuarios.length === 0) {
        container.style.display = 'none';
        btnEnviar.style.display = 'none';
        return;
    }
    container.style.display = 'block';
    btnEnviar.style.display = 'inline-block';
    countSpan.textContent = cmUsuarios.length;

    for (var i = 0; i < cmUsuarios.length; i++) {
        var u = cmUsuarios[i];
        var tr = document.createElement('tr');
        tr.innerHTML = '<td>' + (i+1) + '</td>' +
            '<td>' + u.tipo_documento + '</td>' +
            '<td>' + u.cedula + '</td>' +
            '<td>' + u.nombre + '</td>' +
            '<td>' + u.apellido + '</td>' +
            '<td>' + (u.correo || '-') + '</td>' +
            '<td>' + (u.telefono || '-') + '</td>' +
            '<td>' + (u.fichasLabel || '-') + '</td>' +
            '<td><button class="btn btn-danger btn-sm" onclick="cmEliminarFila(' + i + ')"><i class="bi bi-trash"></i></button></td>';
        tbody.appendChild(tr);
    }
}

function cmEnviar() {
    if (cmUsuarios.length === 0) { alert('No hay usuarios para crear'); return; }
    if (!confirm('Crear ' + cmUsuarios.length + ' usuario(s)?')) return;

    var rol = document.getElementById('cmRol').value;
    var btn = document.getElementById('cmBtnEnviar');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Creando...';

    var datos = cmUsuarios.map(function(u) {
        return {
            tipo_documento: u.tipo_documento,
            cedula: u.cedula,
            nombre: u.nombre,
            apellido: u.apellido,
            correo: u.correo,
            telefono: u.telefono,
            ficha_id: u.ficha_id,
            fichas_ids: u.fichas_ids
        };
    });

    fetch('/gestor_sistema/carga-masiva/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({ usuarios: datos, rol: rol })
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-cloud-upload"></i> Crear Usuarios';
        var div = document.getElementById('cmResultado');
        div.style.display = 'block';
        var html = '';
        if (data.creados > 0) html += '<div class="alert alert-success">' + data.creados + ' usuario(s) creados exitosamente.</div>';
        if (data.omitidos > 0) html += '<div class="alert alert-warning">' + data.omitidos + ' usuario(s) omitidos (ya existían).</div>';
        if (data.errores && data.errores.length > 0) {
            html += '<div class="alert alert-danger"><ul>';
            data.errores.forEach(function(e) { html += '<li>' + e + '</li>'; });
            html += '</ul></div>';
        }
        div.innerHTML = html;
        if (data.creados > 0) {
            cmUsuarios = [];
            cmRenderTabla();
        }
    })
    .catch(function(err) {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-cloud-upload"></i> Crear Usuarios';
        alert('Error al crear usuarios: ' + err);
    });
}
