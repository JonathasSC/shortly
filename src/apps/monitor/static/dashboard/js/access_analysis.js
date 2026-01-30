document.addEventListener("DOMContentLoaded", function() {
    const pieLabels = JSON.parse(document.getElementById('pieLabels').textContent);
    const pieData = JSON.parse(document.getElementById('pieData').textContent);
    const lineLabels = JSON.parse(document.getElementById('lineLabels').textContent);
    const lineData = JSON.parse(document.getElementById('lineData').textContent);

    const lineCtx = document.getElementById('clicksChart').getContext('2d');
    new Chart(lineCtx, {
        type: 'line',
        data: {
            labels: lineLabels,
            datasets: [{
                label: 'Cliques por mês',
                data: lineData,
                borderColor: 'rgba(59, 130, 246, 1)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true,
                pointRadius: 4,
                pointBackgroundColor: 'rgba(59, 130, 246, 1)',
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(229, 231, 235, 0.5)' } },
                x: { grid: { display: false } }
            },
            plugins: {
                legend: {
                    display: false,
                    labels: {
                        color: '#374151' 
                    }
                },
                tooltip: { backgroundColor: '#111827', titleColor: '#fff', bodyColor: '#fff' }
            }
        }
    });

    const pieCtx = document.getElementById('urlClicksChart').getContext('2d');
    new Chart(pieCtx, {
        type: 'pie',
        data: {
            labels: pieLabels,
            datasets: [{
                label: 'Cliques por URL',
                data: pieData,
                backgroundColor: [
                    'rgba(30, 64, 175, 0.8)',  
                    'rgba(37, 99, 235, 0.8)',  
                    'rgba(59, 130, 246, 0.8)',  
                    'rgba(96, 165, 250, 0.8)', 
                    'rgba(147, 197, 253, 0.8)',
                    'rgba(219, 234, 254, 0.8)',
                ],
                borderColor: 'rgba(255, 255, 255, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, 
            plugins: {
                legend: { display: true, position: 'bottom', align: 'start', labels: { color: '#374151' } },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw;
                            const total = context.dataset.data.reduce((a,b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} cliques (${percentage}%)`;
                        }
                    },
                    backgroundColor: '#111827',
                    titleColor: '#fff',
                    bodyColor: '#fff'
                }
            }
        }
    });
});
