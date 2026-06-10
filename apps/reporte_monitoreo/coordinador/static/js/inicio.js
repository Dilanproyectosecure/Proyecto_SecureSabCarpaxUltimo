// ===== DASHBOARD DEL COORDINADOR =====

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Configurar gráfico de asistencias semanales
    if (document.getElementById('asistenciasChart')) {
        configurarGraficoAsistencias();
    }
    
    // 2. Actualizar datos en tiempo real (opcional)
    // actualizarDatos();
});

// Gráfico de asistencias semanales
function configurarGraficoAsistencias() {
    const ctx = document.getElementById('asistenciasChart').getContext('2d');
    
    const data = {
        labels: window.dashboardData.labels_semana,
        datasets: [
            {
                label: 'Entradas',
                data: window.dashboardData.entradas_semana,
                backgroundColor: '#48bb78',
                borderRadius: 6
            },
            {
                label: 'Salidas',
                data: window.dashboardData.salidas_semana,
                backgroundColor: '#fbbf24',
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