function registrarHuella(idUsuario) {
    fetch(`/gestor/registrar-huella/${idUsuario}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert("❌ " + data.error);
        } else {
            alert("✅ " + data.mensaje);

            // 🔥 ESTO ACTUALIZA LA TABLA EN VIVO
            const celdaEstado = document.getElementById(`status-${idUsuario}`);
            if (celdaEstado) {
                celdaEstado.innerHTML = '<span style="color: green;">✅ Registrada</span>';
            }
        }
    })
    .catch(error => {
        console.error(error);
        alert("❌ Error de conexión");
    });
}