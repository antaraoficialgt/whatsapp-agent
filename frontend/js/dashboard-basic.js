requireAuth();

let chartInstances = {};
const customerId = localStorage.getItem('currentCustomerId');

if (!customerId) {
    window.location.href = 'dashboard.html';
}

document.addEventListener('DOMContentLoaded', async () => {
    await loadBasicDashboard();
});

async function loadBasicDashboard() {
    try {
        const data = await apiCall(`/dashboard/basic/${customerId}`);

        // Update header
        document.getElementById('customer-name-header').textContent = data.customer_name;

        // Update KPIs
        document.getElementById('kpi-messages').textContent = data.total_messages_month;
        document.getElementById('kpi-response-time').textContent = Math.round(data.avg_response_time_ms) + 'ms';

        const totalConversations = data.recent_conversations.length;
        document.getElementById('kpi-conversations').textContent = totalConversations;

        // Count unique clients
        const uniqueClients = new Set(data.recent_conversations.map(c => c.sender_phone)).size;
        document.getElementById('kpi-unique-clients').textContent = uniqueClients;

        // Load charts
        loadMessagesChart(data.daily_analytics);
        loadResponseTimeChart(data.daily_analytics);

        // Load conversations table
        loadConversationsTable(data.recent_conversations);
    } catch (error) {
        console.error('Error loading dashboard:', error);
        alert('Error cargando dashboard: ' + error.message);
    }
}

function loadMessagesChart(analytics) {
    const ctx = document.getElementById('messagesChart').getContext('2d');

    if (chartInstances.messages) {
        chartInstances.messages.destroy();
    }

    const labels = analytics.map(a => a.date).reverse();
    const data = analytics.map(a => a.messages_count).reverse();

    chartInstances.messages = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Mensajes',
                data,
                borderColor: '#0066cc',
                backgroundColor: 'rgba(0, 102, 204, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    document.getElementById('messagesChart').style.height = '300px';
}

function loadResponseTimeChart(analytics) {
    const ctx = document.getElementById('responseTimeChart').getContext('2d');

    if (chartInstances.responseTime) {
        chartInstances.responseTime.destroy();
    }

    const labels = analytics.map(a => a.date).reverse();
    const data = analytics.map(a => Math.round(a.response_time_avg)).reverse();

    chartInstances.responseTime = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Tiempo Promedio (ms)',
                data,
                backgroundColor: '#28a745'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    document.getElementById('responseTimeChart').style.height = '300px';
}

function loadConversationsTable(conversations) {
    const tbody = document.getElementById('conversations-body');

    if (conversations.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">Sin conversaciones</td></tr>';
        return;
    }

    tbody.innerHTML = conversations.map(conv => `
        <tr>
            <td>${conv.sender_phone}</td>
            <td>${truncate(conv.message_text)}</td>
            <td>${truncate(conv.response_text)}</td>
            <td>${conv.response_time_ms || '-'}ms</td>
            <td>${formatDate(conv.timestamp)}</td>
        </tr>
    `).join('');
}
