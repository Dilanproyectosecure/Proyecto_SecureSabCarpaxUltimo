document.addEventListener('DOMContentLoaded', function() {
    // Toggle del menú lateral
    const menuIcono = document.getElementById('menuIcono');
    const menuOpen = document.getElementById('menuOpen');
    
    if (menuIcono && menuOpen) {
        menuIcono.addEventListener('click', function() {
            menuOpen.classList.toggle('closed');
        });
    }
    
    // Toggle del dropdown de usuario
    const userTrigger = document.getElementById('userMenuTrigger');
    const userDropdown = document.getElementById('userDropdown');
    
    if (userTrigger && userDropdown) {
        userTrigger.addEventListener('click', function(e) {
            e.stopPropagation();  // Evita que se propague
            console.log('Click en usuario');  // Para debug
            userDropdown.classList.toggle('show');
        });
        
        // Cerrar al hacer clic fuera
        document.addEventListener('click', function(e) {
            if (!userTrigger.contains(e.target)) {
                userDropdown.classList.remove('show');
            }
        });
    }
});