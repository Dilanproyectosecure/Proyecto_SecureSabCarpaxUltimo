(function () {
    'use strict';

    const formulario = document.getElementById('formularioCrear');
    const btnMostrar = document.getElementById('btnMostrarFormulario');
    const btnCerrar = document.getElementById('btnCerrarFormulario');
    const btnCancelar = document.getElementById('btnCancelarFormulario');
    const selectRol = document.getElementById('selectRol');
    const divFicha = document.getElementById('divFicha');

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
        if (divFicha) divFicha.style.display = 'none';
    }

    if (btnCerrar) btnCerrar.addEventListener('click', cerrarFormulario);
    if (btnCancelar) btnCancelar.addEventListener('click', cerrarFormulario);

    if (selectRol && divFicha) {
        selectRol.addEventListener('change', function () {
            const texto = (selectRol.options[selectRol.selectedIndex]?.text || '').toLowerCase();
            divFicha.style.display = (texto === 'aprendiz') ? 'block' : 'none';
        });
    }
})();
