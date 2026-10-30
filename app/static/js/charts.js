// Modern SaaS Analytics Charts with Teal & Emerald Theme
function initAnalyticsCharts(data) {
    if (typeof Chart === 'undefined') return;

    // Set Global Chart.js defaults
    Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
    Chart.defaults.color = '#64748B';

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
                    backgroundColor: [
                        '#3B82F6', // Blue for Submitted
                        '#F59E0B', // Amber for Under Review
                        '#0F766E', // Teal for Assigned
                        '#8B5CF6', // Purple for In Progress
                        '#10B981', // Emerald for Resolved
                        '#EF4444'  // Rose for Rejected
                    ],
                    borderWidth: 3,
                    borderColor: '#FFFFFF',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '72%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 16,
                            font: { size: 12, weight: '500' }
                        }
                    }
                }
            }
        });
    }

    // 2. Monthly Trend Line Chart (Teal & Emerald Gradient)
    const trendCtx = document.getElementById('trendChart');
    if (trendCtx) {
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: data.monthly_labels,
                datasets: [{
                    label: 'Complaints Submitted',
                    data: data.monthly_counts,
                    borderColor: '#0F766E',
                    backgroundColor: 'rgba(15, 118, 110, 0.08)',
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2.5,
                    pointBackgroundColor: '#0F766E',
                    pointBorderColor: '#FFFFFF',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 },
                        grid: { color: '#F1F5F9' }
                    }
                }
            }
        });
    }

    // 3. Priority Distribution Bar Chart
    const priorityCtx = document.getElementById('priorityChart');
    if (priorityCtx) {
        new Chart(priorityCtx, {
            type: 'bar',
            data: {
                labels: ['Low', 'Medium', 'High', 'Critical'],
                datasets: [{
                    label: 'Complaints',
                    data: [
                        data.priority_counts['Low'] || 0,
                        data.priority_counts['Medium'] || 0,
                        data.priority_counts['High'] || 0,
                        data.priority_counts['Critical'] || 0
                    ],
                    backgroundColor: ['#10B981', '#F59E0B', '#EA580C', '#EF4444'],
                    borderRadius: 8,
                    barThickness: 36
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { grid: { display: false } },
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 },
                        grid: { color: '#F1F5F9' }
                    }
                }
            }
        });
    }
}
