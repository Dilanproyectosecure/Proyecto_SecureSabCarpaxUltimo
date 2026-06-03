// ===== DASHBOARD DEL COORDINADOR =====

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Configurar gráficos si existen los canvas
    if (document.getElementById('asistenciasChart')) {
        configurarGraficoAsistencias();
    }
    
    if (document.getElementById('novedadesChart')) {
        configurarGraficoNovedades();
    }
    
    // 2. Actualizar datos en tiempo real (opcional)
    // actualizarDatos();
});

// Gráfico de asistencias semanales
function configurarGraficoAsistencias() {
    const ctx = document.getElementById('asistenciasChart').getContext('2d');
    
    // Datos de ejemplo (deberían venir del backend)
    const data = {
        labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'],
        datasets: [
            {
                label: 'Presentes',
                data: [65, 72, 68, 70, 75, 60],
                backgroundColor: '#48bb78',
                borderRadius: 6
            },
            {
                label: 'Ausentes',
                data: [12, 8, 10, 7, 5, 15],
                backgroundColor: '#f56565',
                borderRadius: 6
            }
        ]
    };

    new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        display: true,
                        color: 'rgba(0,0,0,0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Gráfico de estado de novedades
function configurarGraficoNovedades() {
    const ctx = document.getElementById('novedadesChart').getContext('2d');
    
    // Datos de ejemplo
    const data = {
        labels: ['Pendientes', 'En Proceso', 'Resueltas'],
        datasets: [{
            data: [12, 8, 25],
            backgroundColor: [
                '#fbbf24',
                '#60a5fa',
                '#34d399'
            ],
            borderWidth: 0
        }]
    };

    new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            cutout: '65%'
        }
    });
}

// Función para actualizar datos (simulación)
function actualizarDatos() {
    setInterval(() => {
        // Aquí irían peticiones AJAX para actualizar los KPIs
        console.log('Actualizando datos...');
    }, 30000); // Cada 30 segundos
}

// Tooltips y menús (si es necesario)
document.addEventListener('click', function(e) {
    // Cerrar dropdowns al hacer clic fuera
    const dropdowns = document.querySelectorAll('.user-dropdown');
    dropdowns.forEach(dropdown => {
        if (!dropdown.contains(e.target) && !e.target.closest('.user-menu-container')) {
            dropdown.classList.remove('show');
        }
    });
});

// Animaciones de entrada
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, { threshold: 0.1 });

document.querySelectorAll('.dash-kpi-card, .dash-chart-card, .dash-quick-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s, transform 0.6s';
    observer.observe(el);
});