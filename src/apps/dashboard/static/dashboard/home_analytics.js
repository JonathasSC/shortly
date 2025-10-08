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
                legend: { display: true, labels: { color: '#374151' } },
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
                    'rgba(59, 130, 246, 0.6)',
                    'rgba(16, 185, 129, 0.6)',
                    'rgba(234, 179, 8, 0.6)',
                    'rgba(239, 68, 68, 0.6)',
                    'rgba(139, 92, 246, 0.6)',
                    'rgba(16, 163, 127, 0.6)'
                ],
                borderColor: 'rgba(255, 255, 255, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true, position: 'right', labels: { color: '#374151' } },
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
