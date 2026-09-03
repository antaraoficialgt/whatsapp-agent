requireAuth();

let chartInstances = {};
let currentPeriod = 'daily';
const customerId = localStorage.getItem('currentCustomerId');

if (!customerId) {
    window.location.href = 'dashboard.html';
}

document.addEventListener('DOMContentLoaded', async () => {
    await loadMetrics('daily');
});

async function loadMetrics(periodType) {
    try {
        currentPeriod = periodType;

        // Update active button
        document.querySelectorAll('.period-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        event.target.classList.add('active');

        const data = await apiCall(`/dashboard/advanced/${customerId}`);

        const metrics = data[periodType + '_metrics'] || [];

        if (metrics.length === 0) {
            alert('Sin datos para este período');
            return;
        }

        // Update current period
        const firstMetric = metrics[0];
        document.getElementById('current-period').textContent = firstMetric.period_value;

        // Calculate aggregated metrics
        const totalMessages = metrics.reduce((sum, m) => sum + m.total_messages, 0);
        const totalConversations = metrics.reduce((sum, m) => sum + m.total_conversations, 0);
        const avgResponseTime = metrics.reduce((sum, m) => sum + m.avg_response_time, 0) / metrics.length;
        const totalUniqueUsers = metrics.reduce((sum, m) => sum + m.total_unique_users, 0);
        const avgSatisfaction = metrics.reduce((sum, m) => sum + m.satisfaction_score, 0) / metrics.length;

        // Update KPIs
        document.getElementById('kpi-total-messages').textContent = totalMessages;
        document.getElementById('kpi-total-conversations').textContent = totalConversations;
        document.getElementById('kpi-avg-response').textContent = Math.round(avgResponseTime) + 'ms';
        document.getElementById('kpi-unique-users').textContent = totalUniqueUsers;
        document.getElementById('kpi-satisfaction').textContent = avgSatisfaction.toFixed(2) + '/5.0';

        // Update charts
        loadMessagesChart(metrics);
        loadConversationsChart(metrics);
        loadResponseTimeChart(metrics);
        loadUsersChart(metrics);

        // Update table
        loadMetricsTable(metrics);
    } catch (error) {
        console.error('Error loading metrics:', error);
        alert('Error cargando métricas: ' + error.message);
    }
}

function loadMessagesChart(metrics) {
    const ctx = document.getElementById('messagesChart').getContext('2d');

    if (chartInstances.messages) {
        chartInstances.messages.destroy();
    }

    const labels = metrics.map(m => m.period_value);
    const data = metrics.map(m => m.total_messages);

    chartInstances.messages = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Mensajes',
                data,
                backgroundColor: '#0066cc'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });

    ctx.canvas.style.height = '300px';
}

function loadConversationsChart(metrics) {
    const ctx = document.getElementById('conversationsChart').getContext('2d');

    if (chartInstances.conversations) {
        chartInstances.conversations.destroy();
    }

    const labels = metrics.map(m => m.period_value);
    const data = metrics.map(m => m.total_conversations);

    chartInstances.conversations = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Conversaciones',
                data,
                backgroundColor: '#28a745'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });

    ctx.canvas.style.height = '300px';
}

function loadResponseTimeChart(metrics) {
    const ctx = document.getElementById('responseTimeChart').getContext('2d');

    if (chartInstances.responseTime) {
        chartInstances.responseTime.destroy();
    }

    const labels = metrics.map(m => m.period_value);
    const data = metrics.map(m => Math.round(m.avg_response_time));

    chartInstances.responseTime = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Tiempo Promedio (ms)',
                data,
                borderColor: '#ffc107',
                backgroundColor: 'rgba(255, 193, 7, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });

    ctx.canvas.style.height = '300px';
}

function loadUsersChart(metrics) {
    const ctx = document.getElementById('usersChart').getContext('2d');

    if (chartInstances.users) {
        chartInstances.users.destroy();
    }

    const labels = metrics.map(m => m.period_value);
    const data = metrics.map(m => m.total_unique_users);

    chartInstances.users = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Usuarios Únicos',
                data,
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });

    ctx.canvas.style.height = '300px';
}

function loadMetricsTable(metrics) {
    const tbody = document.getElementById('metrics-body');

    if (metrics.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Sin datos</td></tr>';
        return;
    }

    tbody.innerHTML = metrics.map(m => `
        <tr>
            <td>${m.period_value}</td>
            <td>${m.total_messages}</td>
            <td>${m.total_conversations}</td>
            <td>${Math.round(m.avg_response_time)}ms</td>
            <td>${m.total_unique_users}</td>
            <td>${m.satisfaction_score.toFixed(2)}/5.0</td>
        </tr>
    `).join('');
}

function exportCSV() {
    alert('Exportar CSV disponible próximamente');
}

function exportPDF() {
    alert('Exportar PDF disponible próximamente');
}
