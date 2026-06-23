document.addEventListener('DOMContentLoaded', function() {
    const menuIcono = document.getElementById('menuIcono');
    const menuOpen = document.getElementById('menuOpen');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    function isMobile() {
        return window.innerWidth <= 768;
    }

    // Toggle sidebar
    if (menuIcono && menuOpen) {
        menuIcono.addEventListener('click', function() {
            menuOpen.classList.toggle('closed');
            if (isMobile() && sidebarOverlay) {
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
    if (isMobile() && menuOpen) {
        menuOpen.classList.add('closed');
    }

    // Toggle acordeón de secciones del menú gestor
    var toggleBtns = document.querySelectorAll('.menu-toggle');
    toggleBtns.forEach(function(btn) {
        var section = btn.getAttribute('data-section');
        var submenu = document.querySelector('.menu-submenu[data-section="' + section + '"]');
        if (!submenu) return;

        var saved = localStorage.getItem('menu_' + section);
        if (saved === 'open') {
            btn.classList.add('open');
            submenu.classList.add('open');
        }

        btn.addEventListener('click', function() {
            var isOpen = submenu.classList.contains('open');
            if (isOpen) {
                submenu.classList.remove('open');
                btn.classList.remove('open');
                localStorage.setItem('menu_' + section, 'closed');
            } else {
                submenu.classList.add('open');
                btn.classList.add('open');
                localStorage.setItem('menu_' + section, 'open');
            }
        });
    });

    // Auto-abrir sección que contiene link activo
    var activeLink = document.querySelector('.menu-submenu .nav-link.active');
    if (activeLink) {
        var parentSubmenu = activeLink.closest('.menu-submenu');
        var parentToggle = parentSubmenu ? document.querySelector('.menu-toggle[data-section="' + parentSubmenu.getAttribute('data-section') + '"]') : null;
        if (parentSubmenu && parentToggle && !parentSubmenu.classList.contains('open')) {
            parentSubmenu.classList.add('open');
            parentToggle.classList.add('open');
            localStorage.setItem('menu_' + parentSubmenu.getAttribute('data-section'), 'open');
        }
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
