document.addEventListener('DOMContentLoaded', function() {
    const menuIcono = document.getElementById('menuIcono');
    const menuOpen = document.getElementById('menuOpen');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    // Toggle sidebar
    if (menuIcono && menuOpen) {
        menuIcono.addEventListener('click', function() {
            menuOpen.classList.toggle('closed');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('active');
            }
            // Toggle icon
            var icon = menuIcono.querySelector('i');
            if (icon) {
                if (menuOpen.classList.contains('closed')) {
                    icon.classList.remove('bi-x-lg');
                    icon.classList.add('bi-list');
                } else {
                    icon.classList.remove('bi-list');
                    icon.classList.add('bi-x-lg');
                }
            }
        });
    }

    // Close sidebar on overlay click
    if (sidebarOverlay && menuOpen) {
        sidebarOverlay.addEventListener('click', function() {
            menuOpen.classList.add('closed');
            sidebarOverlay.classList.remove('active');
            var icon = menuIcono ? menuIcono.querySelector('i') : null;
            if (icon) {
                icon.classList.remove('bi-x-lg');
                icon.classList.add('bi-list');
            }
        });
    }

    // Start sidebar closed on mobile
    if (window.innerWidth <= 768 && menuOpen) {
        menuOpen.classList.add('closed');
    }

    // Toggle dropdown de usuario
    const userTrigger = document.getElementById('userMenuTrigger');
    const userDropdown = document.getElementById('userDropdown');

    if (userTrigger && userDropdown) {
        userTrigger.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });

        document.addEventListener('click', function(e) {
            if (!userTrigger.contains(e.target)) {
                userDropdown.classList.remove('show');
            }
        });
    }
});
