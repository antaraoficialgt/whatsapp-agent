requireAuth();

const user = getUser();

document.addEventListener('DOMContentLoaded', async () => {
    // Set user info
    if (user) {
        document.getElementById('user-name').textContent = user.name;
        document.getElementById('settings-name').textContent = user.name;
        document.getElementById('settings-email').textContent = user.email;

        if (user.subscription) {
            const badge = document.getElementById('plan-badge');
            badge.textContent = user.subscription.plan.toUpperCase();
            badge.className = `badge badge-${user.subscription.plan}`;
        }
    }

    // Load customers
    await loadCustomers();

    // Set active nav
    document.querySelector('.nav-menu a').classList.add('active');
});

async function loadCustomers() {
    try {
        const data = await apiCall('/customers');
        const customersList = document.getElementById('customers-list');

        if (data.total === 0) {
            customersList.innerHTML = `
                <div class="card" style="grid-column: 1/-1; text-align: center;">
                    <p>No tienes negocios agregados</p>
                    <button onclick="showAddCustomer()" class="btn btn-primary" style="width: 200px; margin-top: 10px;">
                        Agregar tu primer negocio
                    </button>
                </div>
            `;
            return;
        }

        customersList.innerHTML = data.customers.map(customer => `
            <div class="card customer-card">
                <h3>${customer.name}</h3>
                <p><strong>Número:</strong> ${customer.phone_number_id}</p>
                <p><strong>Creado:</strong> ${formatDate(customer.created_at)}</p>
                <div class="card-buttons">
                    <button onclick="viewDashboard(${customer.id})" class="btn btn-primary btn-small">Ver Dashboard</button>
                    <button onclick="editCustomer(${customer.id})" class="btn btn-secondary btn-small">Editar</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading customers:', error);
        document.getElementById('customers-list').innerHTML = '<p class="error">Error cargando negocios</p>';
    }
}

async function handleAddCustomer(event) {
    event.preventDefault();

    const name = document.getElementById('customer-name').value;
    const phoneNumberId = document.getElementById('customer-phone-id').value;
    const token = document.getElementById('customer-token').value;
    const prompt = document.getElementById('customer-prompt').value;

    try {
        const data = await apiCall('/customers', 'POST', {
            name,
            phone_number_id: phoneNumberId,
            access_token: token,
            system_prompt: prompt || undefined
        });

        alert('Negocio agregado! Tu API key: ' + data.api_key);
        hideAddCustomer();

        // Clear form
        event.target.reset();
        document.getElementById('customer-name').value = '';
        document.getElementById('customer-phone-id').value = '';
        document.getElementById('customer-token').value = '';
        document.getElementById('customer-prompt').value = '';

        // Reload customers
        await loadCustomers();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function viewDashboard(customerId) {
    // Check subscription for dashboard access
    if (user.subscription.has_basic_dashboard) {
        localStorage.setItem('currentCustomerId', customerId);
        window.location.href = 'dashboard-basic.html';
    } else {
        alert('Tu plan no incluye acceso a dashboards');
    }
}

function editCustomer(customerId) {
    alert('Funcionalidad de editar próximamente');
}

async function loadSubscription() {
    try {
        const data = await apiCall('/subscription');
        document.getElementById('current-plan').textContent = data.plan.toUpperCase();

        const features = [];
        if (data.has_basic_dashboard) features.push('✓ Dashboard Básico');
        if (data.has_advanced_dashboard) features.push('✓ Dashboard Avanzado');
        if (data.has_custom_prompts) features.push('✓ Prompts Personalizados');

        document.getElementById('plan-features').innerHTML = features.join('<br>');

        // Highlight current plan
        document.querySelectorAll('.plan-card').forEach(card => {
            card.style.opacity = '0.5';
        });
        const currentPlanCard = document.getElementById('plan-' + data.plan);
        if (currentPlanCard) {
            currentPlanCard.style.opacity = '1';
        }
    } catch (error) {
        console.error('Error loading subscription:', error);
    }
}

async function upgradePlan(plan) {
    if (plan === user.subscription.plan) {
        alert('Ya estás en este plan');
        return;
    }

    if (!confirm(`¿Actualizar a plan ${plan}?`)) return;

    try {
        const data = await apiCall('/subscription/upgrade', 'POST', { new_plan: plan });
        alert('Plan actualizado exitosamente!');
        window.location.reload();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function contactSales() {
    window.location.href = 'mailto:sales@example.com?subject=Información Plan Enterprise';
}

function deleteAccount() {
    if (!confirm('¿Estás seguro? Esta acción es irreversible.')) return;
    if (!confirm('Escribe "ELIMINAR" para confirmar')) return;

    alert('Funcionalidad de eliminar cuenta próximamente');
}

// Load subscription when switching to subscription page
document.addEventListener('click', function(e) {
    if (e.target.textContent.includes('Mi Suscripción')) {
        loadSubscription();
    }
});
