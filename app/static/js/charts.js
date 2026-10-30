// Analytics Charts using Chart.js
function initAnalyticsCharts(data) {
    if (typeof Chart === 'undefined') return;

    // 1. Status Distribution Doughnut Chart
    const statusCtx = document.getElementById('statusChart');
    if (statusCtx) {
        new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: ['Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved', 'Rejected'],
                datasets: [{
                    data: [
                        data.status_counts['Submitted'] || 0,
                        data.status_counts['Under Review'] || 0,
                        data.status_counts['Assigned'] || 0,
                        data.status_counts['In Progress'] || 0,
                        data.status_counts['Resolved'] || 0,
                        data.status_counts['Rejected'] || 0
                    ],
                    backgroundColor: ['#3b82f6', '#f59e0b', '#06b6d4', '#8b5cf6', '#10b981', '#ef4444'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    // 2. Monthly Trend Line Chart
    const trendCtx = document.getElementById('trendChart');
    if (trendCtx) {
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: data.monthly_labels,
                datasets: [{
                    label: 'Complaints Submitted',
                    data: data.monthly_counts,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2,
                    pointBackgroundColor: '#2563eb'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 }
                    }
                }
            }
        });
    }

    // 3. Priority Bar Chart
    const priorityCtx = document.getElementById('priorityChart');
    if (priorityCtx) {
        new Chart(priorityCtx, {
            type: 'bar',
            data: {
                labels: ['Low', 'Medium', 'High', 'Critical'],
                datasets: [{
                    label: 'Count',
                    data: [
                        data.priority_counts['Low'] || 0,
                        data.priority_counts['Medium'] || 0,
                        data.priority_counts['High'] || 0,
                        data.priority_counts['Critical'] || 0
                    ],
                    backgroundColor: ['#10b981', '#f59e0b', '#f97316', '#ef4444'],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 }
                    }
                }
            }
        });
    }
}

