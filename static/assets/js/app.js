/* ═══════════════════════════════════════════
   PitLane — Core JS (USDClaw integrated)
   ═══════════════════════════════════════════ */

const API = '';  // same origin
let token = localStorage.getItem('pitlane_token');
let user = JSON.parse(localStorage.getItem('pitlane_user') || 'null');

// ─── API HELPER ───
async function api(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { ...opts, headers });
  if (res.status === 401) { logout(); throw new Error('請重新登入'); }
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
      <button class="btn btn-outline btn-sm" onclick="logout()">登出</button>
    `;
  } else {
    authArea.innerHTML = `
      <button class="btn btn-gold btn-sm" onclick="showModal('login')">登入</button>
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
    localStorage.setItem('pitlane_user', JSON.stringify(user));
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
  localStorage.setItem('pitlane_token', token);
  localStorage.setItem('pitlane_user', JSON.stringify(user));
  updateAuthUI();
  closeModal();
}

function logout() {
  token = null;
  user = null;
  localStorage.removeItem('pitlane_token');
  localStorage.removeItem('pitlane_user');
  updateAuthUI();
}

// ─── MODAL ───
function showModal(type) {
  const overlay = document.getElementById('modal-overlay');
  const modal = document.getElementById('auth-modal');
  overlay.classList.add('active');

  modal.innerHTML = `
    <h2>登入 PitLane</h2>
    <p style="color:var(--text-secondary);font-size:13px;margin-bottom:20px;text-align:center">
      使用你的 ClawStockMarket 交易所帳號
    </p>
    <div class="form-group">
      <label>帳號 / Email</label>
      <input type="text" id="login-username" placeholder="交易所帳號或 Email" />
    </div>
    <div class="form-group">
      <label>密碼</label>
      <input type="password" id="login-password" placeholder="密碼" />
    </div>
    <div id="auth-error" class="error-msg"></div>
    <div class="form-actions">
      <button class="btn btn-outline" onclick="closeModal()">取消</button>
      <button class="btn btn-gold" onclick="handleLogin()">登入</button>
    </div>
    <div class="switch-link" style="margin-top:16px">
      還沒有帳號？到 <a href="https://clawstockmarket.com" target="_blank">交易所</a> 註冊
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
  const p = document.getElementById('login-password').value;
  const errEl = document.getElementById('auth-error');
  if (!u || !p) { errEl.textContent = '請輸入帳號和密碼'; return; }
  try {
    await login(u, p);
    // Reload page to refresh data
    location.reload();
  } catch (err) {
    errEl.textContent = err.message;
  }
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
    silverstone: '銀石 Silverstone',
    monza: '蒙扎 Monza',
    suzuka: '鈴鹿 Suzuka',
    monaco: '摩納哥 Monaco',
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
