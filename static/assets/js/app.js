/* ═══════════════════════════════════════════
   PitLane — Core JS (USDClaw integrated)
   ═══════════════════════════════════════════ */

const API = '';  // same origin
let token = localStorage.getItem('throttenix_token');
let user = JSON.parse(localStorage.getItem('throttenix_user') || 'null');

// ─── API HELPER ───
async function api(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { ...opts, headers });
  if (res.status === 401) { logout(); throw new Error('Please log in again'); }
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'API Error');
  return data;
}

// ─── AUTH ───
function updateAuthUI() {
  const authArea = document.getElementById('nav-auth');
  if (!authArea) return;
  if (user) {
    authArea.innerHTML = `
      <span class="nav-coins">◆ <span id="user-coins">${formatNum(user.balance)}</span></span>
      <span style="color:var(--text-secondary);font-size:14px">${user.username}</span>
      <button class="btn btn-outline btn-sm" onclick="logout()">Log Out</button>
    `;
  } else {
    authArea.innerHTML = `
      <button class="btn btn-gold btn-sm" onclick="showModal('login')">Log In</button>
    `;
  }
}

function formatNum(n) {
  if (n == null) return '0';
  return Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
}

async function refreshBalance() {
  if (!token) return;
  try {
    const data = await api('/api/auth/me');
    user.balance = data.balance;
    localStorage.setItem('throttenix_user', JSON.stringify(user));
    const el = document.getElementById('user-coins');
    if (el) el.textContent = formatNum(data.balance);
  } catch (e) {}
}

async function login(username, password) {
  const data = await api('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  token = data.access_token;
  user = { username: data.username, balance: data.balance };
  localStorage.setItem('throttenix_token', token);
  localStorage.setItem('throttenix_user', JSON.stringify(user));
  updateAuthUI();
  closeModal();
}

function logout() {
  token = null;
  user = null;
  localStorage.removeItem('throttenix_token');
  localStorage.removeItem('throttenix_user');
  updateAuthUI();
}

// ─── MODAL ───
function showModal(type) {
  const overlay = document.getElementById('modal-overlay');
  const modal = document.getElementById('auth-modal');
  overlay.classList.add('active');

  modal.innerHTML = `
    <h2>Log In to Throttenix</h2>
    <p style="color:var(--text-secondary);font-size:13px;margin-bottom:20px;text-align:center">
      Use your ClawStockMarket account
    </p>
    <div class="form-group">
      <label>Username / Email</label>
      <input type="text" id="login-username" placeholder="Exchange username or Email" />
    </div>
    <div id="auth-error" class="error-msg"></div>
    <div class="form-actions">
      <button class="btn btn-outline" onclick="closeModal()">Cancel</button>
      <button class="btn btn-gold" onclick="handleLogin()">Log In</button>
    </div>
    <div class="switch-link" style="margin-top:16px">
      No account? Register at <a href="https://clawstockmarket.com" target="_blank">ClawStockMarket</a>
    </div>
  `;

  // Focus username input
  setTimeout(() => document.getElementById('login-username')?.focus(), 100);
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('active');
}

async function handleLogin() {
  const u = document.getElementById('login-username').value.trim();
  const errEl = document.getElementById('auth-error');
  if (!u) { errEl.textContent = 'Please enter your username or email'; return; }
  try {
    await login(u, '');
    location.reload();
  } catch (err) {
    errEl.textContent = err.message;
  }
}

// ─── CAR IMAGES ───
const TEAM_CAR_MAP = {
  'McLaren': '/static/assets/cars/car_orange.png',
  'Red Bull Racing': '/static/assets/cars/car_blue.png',
  'Ferrari': '/static/assets/cars/car_red.png',
  'Mercedes': '/static/assets/cars/car_teal.png',
  'Aston Martin': '/static/assets/cars/car_green.png',
  'Alpine': '/static/assets/cars/car_blue.png',
  'Williams': '/static/assets/cars/car_blue.png',
  'Haas': '/static/assets/cars/car_black.png',
  'Racing Bulls': '/static/assets/cars/car_blue.png',
  'RB': '/static/assets/cars/car_blue.png',
  'Audi': '/static/assets/cars/car_green.png',
  'Kick Sauber': '/static/assets/cars/car_green.png',
};
function getCarImage(team) {
  return TEAM_CAR_MAP[team] || '/static/assets/cars/car_black.png';
}

// ─── UTILITY ───
function statBarClass(val) {
  if (val >= 70) return 'high';
  if (val >= 40) return 'mid';
  return 'low';
}

function renderStatBar(label, value) {
  return `
    <div class="stat-row">
      <span class="stat-label">${label}</span>
      <div class="stat-bar telemetry-line">
        <div class="stat-bar-fill ${statBarClass(value)}" style="width:${value}%"></div>
      </div>
      <span class="stat-value">${value}</span>
    </div>
  `;
}

function rarityClass(rarity) {
  return `rarity-${rarity || 'silverstone'}`;
}

function rarityLabel(rarity) {
  const map = {
    silverstone: 'Silverstone',
    monza: 'Monza',
    suzuka: 'Suzuka',
    monaco: 'Monaco',
  };
  return map[rarity] || map.silverstone;
}

// ─── INIT ───
document.addEventListener('DOMContentLoaded', () => {
  updateAuthUI();
  document.getElementById('modal-overlay')?.addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && document.getElementById('login-username')) handleLogin();
    if (e.key === 'Escape') closeModal();
  });
});
