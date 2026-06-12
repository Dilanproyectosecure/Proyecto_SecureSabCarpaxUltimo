// ===== DASHBOARD DEL COORDINADOR =====

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('donaChart')) {
        configurarGraficoDona();
    }
    if (document.getElementById('barrasChart')) {
        configurarGraficoBarras();
    }
    if (document.getElementById('tendenciaChart')) {
        configurarGraficoTendencia();
    }
});

function configurarGraficoDona() {
    const ctx = document.getElementById('donaChart').getContext('2d');
    const dist = window.dashboardData.distribucion;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Presentes', 'Ausentes', 'Justificados'],
            datasets: [{
                data: [dist.presentes, dist.ausentes, dist.justificados],
                backgroundColor: ['#22c55e', '#ef4444', '#f59e0b'],
                borderWidth: 0,
                hoverOffset: 8
            }]
        },
        options: {
            cutout: '65%',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    padding: 12,
                    titleFont: { size: 13 },
                    bodyFont: { size: 12 },
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = total > 0 ? ((context.raw / total) * 100).toFixed(1) : 0;
                            return context.label + ': ' + context.raw + ' (' + pct + '%)';
                        }
                    }
                }
            }
        }
    });
}

function configurarGraficoBarras() {
    const ctx = document.getElementById('barrasChart').getContext('2d');
    const ambientes = window.dashboardData.ambientes;

    const labels = ambientes.map(function(a) { return a.ambiente; });
    const data = ambientes.map(function(a) { return a.presentes; });

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: '#22c55e',
                borderRadius: 4,
                barThickness: 22
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            return context.raw + ' aprendices presentes';
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { display: false },
                    ticks: {
                        stepSize: 10,
                        font: { size: 11 },
                        color: '#6b7280'
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: {
                        font: { size: 12 },
                        color: '#374151'
                    }
                }
            }
        }
    });
}

function configurarGraficoTendencia() {
    const ctx = document.getElementById('tendenciaChart').getContext('2d');
    const tendencia = window.dashboardData.tendencia;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: tendencia.labels,
            datasets: [{
                label: 'Aprendices presentes',
                data: tendencia.valores,
                borderColor: '#22c55e',
                backgroundColor: 'transparent',
                borderWidth: 2.5,
                pointBackgroundColor: '#22c55e',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7,
                tension: 0.3,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            return context.raw + ' aprendices presentes';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 5,
                        font: { size: 11 },
                        color: '#6b7280'
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        font: { size: 11 },
                        color: '#6b7280'
                    }
                }
            }
        }
    });
}
