/* ============================================
   Aunty Queen Connect — Dashboard App
   ============================================ */

const API_BASE = '/api/dashboard';

// --- API Key Management ---
function getApiKey() {
  return localStorage.getItem('dashboard_api_key') || '';
}

function saveApiKey(key) {
  localStorage.setItem('dashboard_api_key', key);
}

// --- Fetch Helper ---
async function api(path, options = {}) {
  const key = getApiKey();
  if (!key) {
    showGlobalError('Please enter your API key above.');
    throw new Error('No API key');
  }

  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'X-API-Key': key, 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  return data;
}

function showGlobalError(msg) {
  const el = document.getElementById('global-error');
  if (el) { el.textContent = msg; el.className = 'result-msg error show'; }
}
function hideGlobalError() {
  const el = document.getElementById('global-error');
  if (el) { el.className = 'result-msg'; }
}

// --- Tab Navigation ---
function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');

      // Load data on first visit
      const tab = btn.dataset.tab;
      if (tab === 'overview') loadOverview();
      if (tab === 'analytics') loadAnalytics();
      if (tab === 'counsellors') loadCounsellors();
      if (tab === 'tickets') loadTickets();
      if (tab === 'users') loadUsers();
      if (tab === 'messages') loadMessages();
      if (tab === 'settings') loadSettings();
    });
  });
}

// --- Helper: Render Table ---
function renderTable(containerId, headers, rows) {
  const el = document.getElementById(containerId);
  if (!rows || rows.length === 0) {
    el.innerHTML = '<div class="empty-state">No data found.</div>';
    return;
  }

  let html = '<div class="table-wrap"><table><thead><tr>';
  headers.forEach(h => { html += `<th>${h.label}</th>`; });
  html += '</tr></thead><tbody>';

  rows.forEach(row => {
    html += '<tr>';
    headers.forEach(h => {
      const val = h.render ? h.render(row) : (row[h.key] ?? '-');
      html += `<td>${val}</td>`;
    });
    html += '</tr>';
  });

  html += '</tbody></table></div>';
  el.innerHTML = html;
}

function statusBadge(status) {
  if (!status) return '-';
  const s = status.toLowerCase().replace(' ', '_');
  return `<span class="badge badge-${s}">${status}</span>`;
}

function categoryBadge(cat) {
  if (!cat) return '-';
  return `<span class="badge badge-${cat}">${cat}</span>`;
}

function editableBadge(val) {
  return val ? '<span class="badge badge-yes">Yes</span>' : '<span class="badge badge-no">No</span>';
}

function showResult(id, msg, type) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = `result-msg ${type} show`;
  setTimeout(() => { el.className = 'result-msg'; }, 5000);
}


// ============================================
// TAB: OVERVIEW
// ============================================
async function loadOverview() {
  hideGlobalError();
  try {
    const data = await api('/stats');
    const s = data.stats;

    document.getElementById('stat-users').textContent = s.total_users;
    document.getElementById('stat-messages').textContent = s.total_messages;
    document.getElementById('stat-tickets').textContent = s.active_tickets;
    document.getElementById('stat-counsellors').textContent = s.total_counsellors;
    document.getElementById('stat-maintenance').textContent = s.maintenance_mode ? 'ON' : 'OFF';

    const model = String(s.ai_model || 'N/A');
    document.getElementById('stat-model').textContent = model.includes('/') ? model.split('/').pop().slice(0, 25) : model.slice(0, 25);

    // Load recent tickets & messages
    const [ticketsData, messagesData] = await Promise.all([
      api('/tickets?limit=5'),
      api('/messages?limit=5')
    ]);

    renderTable('overview-tickets', [
      { label: 'Ticket ID', key: 'id' },
      { label: 'Status', render: r => statusBadge(r.status) },
      { label: 'Handler', key: 'handler' },
      { label: 'User', key: 'user' },
      { label: 'Created', key: 'created_at' },
    ], ticketsData.tickets);

    renderTable('overview-messages', [
      { label: 'From', key: 'from' },
      { label: 'To', key: 'to' },
      { label: 'Type', key: 'type' },
      { label: 'Content', render: r => { const c = r.content || ''; return c.length > 80 ? c.slice(0, 80) + '...' : c; } },
      { label: 'Timestamp', key: 'timestamp' },
    ], messagesData.messages);

  } catch (e) {
    showGlobalError('Failed to load overview: ' + e.message);
  }
}


// ============================================
// TAB: ANALYTICS
// ============================================
let chartInstances = {};

function destroyChart(id) {
  if (chartInstances[id]) { chartInstances[id].destroy(); delete chartInstances[id]; }
}

async function loadAnalytics() {
  hideGlobalError();
  try {
    const [msgData, ticketData, langData, demoData] = await Promise.all([
      api('/analytics/messages-per-day?days=30'),
      api('/analytics/ticket-status'),
      api('/analytics/user-languages'),
      api('/analytics/user-demographics'),
    ]);

    // Messages line chart
    destroyChart('msgChart');
    const msgCtx = document.getElementById('msgChart').getContext('2d');
    chartInstances['msgChart'] = new Chart(msgCtx, {
      type: 'line',
      data: {
        labels: msgData.data.map(d => d.date),
        datasets: [{
          label: 'Messages',
          data: msgData.data.map(d => d.count),
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59,130,246,0.1)',
          fill: true,
          tension: 0.3,
          pointRadius: 3,
          pointBackgroundColor: '#3b82f6',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 10 }, maxTicksLimit: 8 } },
          y: { beginAtZero: true, grid: { color: '#f3f4f6' }, ticks: { font: { size: 10 } } }
        }
      }
    });

    // Ticket donut chart
    destroyChart('ticketChart');
    const ticketCtx = document.getElementById('ticketChart').getContext('2d');
    const tColors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'];
    chartInstances['ticketChart'] = new Chart(ticketCtx, {
      type: 'doughnut',
      data: {
        labels: ticketData.data.map(d => d.status),
        datasets: [{
          data: ticketData.data.map(d => d.count),
          backgroundColor: tColors.slice(0, ticketData.data.length),
          borderWidth: 0,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '55%',
        plugins: { legend: { position: 'bottom', labels: { font: { size: 11 }, padding: 12 } } }
      }
    });

    // Language bar chart
    destroyChart('langChart');
    const langCtx = document.getElementById('langChart').getContext('2d');
    chartInstances['langChart'] = new Chart(langCtx, {
      type: 'bar',
      data: {
        labels: langData.data.map(d => d.language),
        datasets: [{
          data: langData.data.map(d => d.count),
          backgroundColor: tColors.slice(0, langData.data.length),
          borderWidth: 0,
          borderRadius: 4,
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { beginAtZero: true, grid: { color: '#f3f4f6' }, ticks: { font: { size: 10 } } },
          y: { grid: { display: false }, ticks: { font: { size: 11 } } }
        }
      }
    });

    // Demographics bar chart
    destroyChart('demoChart');
    const demoCtx = document.getElementById('demoChart').getContext('2d');
    chartInstances['demoChart'] = new Chart(demoCtx, {
      type: 'bar',
      data: {
        labels: demoData.data.map(d => d.age_range),
        datasets: [{
          data: demoData.data.map(d => d.count),
          backgroundColor: '#8b5cf6',
          borderWidth: 0,
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 10 } } },
          y: { beginAtZero: true, grid: { color: '#f3f4f6' }, ticks: { font: { size: 10 } } }
        }
      }
    });

  } catch (e) {
    showGlobalError('Failed to load analytics: ' + e.message);
  }
}


// ============================================
// TAB: COUNSELLORS
// ============================================
async function loadCounsellors() {
  hideGlobalError();
  try {
    const data = await api('/counsellors');
    renderTable('counsellors-table', [
      { label: 'ID', key: 'id' },
      { label: 'Username', key: 'username' },
      { label: 'Name', key: 'name' },
      { label: 'Email', key: 'email' },
      { label: 'Phone', key: 'phone' },
      { label: 'Current Ticket', render: r => r.current_ticket || 'Available' },
    ], data.counsellors);
  } catch (e) {
    showGlobalError('Failed to load counsellors: ' + e.message);
  }
}

async function createCounsellor() {
  const fields = ['username', 'name', 'email', 'password', 'phone', 'whatsapp'];
  const payload = {};
  fields.forEach(f => {
    const val = document.getElementById(`c-${f}`).value.trim();
    if (val) payload[f] = val;
  });

  if (!payload.username || !payload.email) {
    showResult('counsellor-result', 'Username and email are required.', 'error');
    return;
  }

  try {
    const data = await api('/counsellors', { method: 'POST', body: JSON.stringify(payload) });
    showResult('counsellor-result', data.message, 'success');
    fields.forEach(f => { document.getElementById(`c-${f}`).value = ''; });
    loadCounsellors();
  } catch (e) {
    showResult('counsellor-result', e.message, 'error');
  }
}

async function deleteCounsellor() {
  const username = document.getElementById('c-delete-username').value.trim();
  if (!username) { showResult('counsellor-delete-result', 'Enter a username.', 'error'); return; }

  try {
    const data = await api(`/counsellors/${username}`, { method: 'DELETE' });
    showResult('counsellor-delete-result', data.message, 'success');
    document.getElementById('c-delete-username').value = '';
    loadCounsellors();
  } catch (e) {
    showResult('counsellor-delete-result', e.message, 'error');
  }
}


// ============================================
// TAB: TICKETS
// ============================================
async function loadTickets() {
  hideGlobalError();
  const status = document.getElementById('ticket-status-filter').value;
  const limit = document.getElementById('ticket-limit').value;

  try {
    const data = await api(`/tickets?status=${status}&limit=${limit}`);
    renderTable('tickets-table', [
      { label: 'Ticket ID', key: 'id' },
      { label: 'Status', render: r => statusBadge(r.status) },
      { label: 'Handler', key: 'handler' },
      { label: 'User', key: 'user' },
      { label: 'Created', key: 'created_at' },
      { label: 'Closed', render: r => r.closed_at || '-' },
    ], data.tickets);
  } catch (e) {
    showGlobalError('Failed to load tickets: ' + e.message);
  }
}

async function viewTicketDetails() {
  const ticketId = document.getElementById('ticket-id-input').value.trim();
  if (!ticketId) return;

  try {
    const data = await api(`/tickets/${ticketId}`);
    const t = data.ticket;
    const panel = document.getElementById('ticket-detail-panel');
    panel.innerHTML = `
      <h3>Ticket: ${t.id}</h3>
      <div class="detail-row"><span class="detail-label">Status</span><span class="detail-value">${statusBadge(t.status)}</span></div>
      <div class="detail-row"><span class="detail-label">Handler</span><span class="detail-value">${t.handler || 'Unassigned'}</span></div>
      <div class="detail-row"><span class="detail-label">User</span><span class="detail-value">${t.user || '-'}</span></div>
      <div class="detail-row"><span class="detail-label">Created</span><span class="detail-value">${t.created_at || '-'}</span></div>
      <div class="detail-row"><span class="detail-label">Closed</span><span class="detail-value">${t.closed_at || 'Still open'}</span></div>
      <div style="margin-top:16px">
        <strong style="font-size:13px;color:var(--gray-700)">Transcript:</strong>
        <pre style="margin-top:8px;background:var(--gray-50);padding:14px;border-radius:8px;font-size:12px;white-space:pre-wrap;max-height:300px;overflow-y:auto;border:1px solid var(--gray-200)">${t.transcript || 'No transcript available.'}</pre>
      </div>
    `;
    panel.style.display = 'block';
  } catch (e) {
    showResult('ticket-result', e.message, 'error');
  }
}


// ============================================
// TAB: USERS
// ============================================
async function loadUsers() {
  hideGlobalError();
  const search = document.getElementById('user-search').value.trim();
  const limit = document.getElementById('user-limit').value;

  try {
    const params = `?limit=${limit}${search ? `&search=${encodeURIComponent(search)}` : ''}`;
    const data = await api(`/users${params}`);
    renderTable('users-table', [
      { label: 'Phone / ID', key: 'id' },
      { label: 'Language', render: r => r.language || '-' },
      { label: 'Handler', key: 'handler' },
      { label: 'Onboarding', key: 'onboarding_level' },
      { label: 'Age', key: 'age' },
      { label: 'Gender', key: 'gender' },
    ], data.users);
  } catch (e) {
    showGlobalError('Failed to load users: ' + e.message);
  }
}


// ============================================
// TAB: MESSAGES
// ============================================
async function loadMessages() {
  hideGlobalError();
  const search = document.getElementById('msg-search').value.trim();
  const limit = document.getElementById('msg-limit').value;

  try {
    const params = `?limit=${limit}${search ? `&search=${encodeURIComponent(search)}` : ''}`;
    const data = await api(`/messages${params}`);
    renderTable('messages-table', [
      { label: 'From', key: 'from' },
      { label: 'To', key: 'to' },
      { label: 'Type', key: 'type' },
      { label: 'Content', render: r => { const c = r.content || ''; return c.length > 120 ? c.slice(0, 120) + '...' : c; } },
      { label: 'Timestamp', key: 'timestamp' },
    ], data.messages);
  } catch (e) {
    showGlobalError('Failed to load messages: ' + e.message);
  }
}


// ============================================
// TAB: SETTINGS
// ============================================
async function loadSettings() {
  hideGlobalError();
  try {
    const data = await api('/settings');
    const configs = data.configs;
    const rows = [];

    for (const [category, entries] of Object.entries(configs)) {
      for (const [key, info] of Object.entries(entries)) {
        rows.push({
          category,
          key,
          value: String(info.value),
          data_type: info.data_type,
          description: info.description,
          is_editable: info.is_editable,
        });
      }
    }

    renderTable('settings-table', [
      { label: 'Category', render: r => categoryBadge(r.category) },
      { label: 'Key', key: 'key' },
      { label: 'Value', render: r => `<code style="font-size:12px;background:var(--gray-100);padding:2px 6px;border-radius:4px">${r.value}</code>` },
      { label: 'Type', key: 'data_type' },
      { label: 'Description', key: 'description' },
      { label: 'Editable', render: r => editableBadge(r.is_editable) },
    ], rows);
  } catch (e) {
    showGlobalError('Failed to load settings: ' + e.message);
  }
}

async function updateSetting() {
  const category = document.getElementById('setting-category').value;
  const key = document.getElementById('setting-key').value.trim();
  const value = document.getElementById('setting-value').value.trim();

  if (!key || value === '') {
    showResult('setting-result', 'Key and value are required.', 'error');
    return;
  }

  try {
    const data = await api(`/settings/${category}/${key}`, {
      method: 'PUT',
      body: JSON.stringify({ value }),
    });
    showResult('setting-result', data.message, 'success');
    loadSettings();
  } catch (e) {
    showResult('setting-result', e.message, 'error');
  }
}


// ============================================
// INIT
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  // Restore API key
  const keyInput = document.getElementById('api-key-input');
  keyInput.value = getApiKey();
  keyInput.addEventListener('input', () => saveApiKey(keyInput.value.trim()));

  initTabs();

  // Auto-load overview on start
  if (getApiKey()) {
    loadOverview();
  }
});
