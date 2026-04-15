/* ═══════════════════════════════════════════
   PitLane — Core JS
   ═══════════════════════════════════════════ */

const API = '';  // same origin
let token = localStorage.getItem('pitlane_token');
let user = JSON.parse(localStorage.getItem('pitlane_user') || 'null');

// ─── API HELPER ───
async function api(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { ...opts, headers });
  if (res.status === 401) { logout(); throw new Error('Unauthorized'); }
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
      <span class="nav-coins">◆ <span id="user-coins">${user.coins?.toLocaleString() || '10,000'}</span></span>
      <span style="color:var(--text-secondary);font-size:14px">${user.username}</span>
      <button class="btn btn-outline btn-sm" onclick="logout()">登出</button>
    `;
  } else {
    authArea.innerHTML = `
      <button class="btn btn-outline btn-sm" onclick="showModal('login')">登入</button>
      <button class="btn btn-gold btn-sm" onclick="showModal('register')">註冊</button>
    `;
  }
}

async function register(username, email, password) {
  const data = await api('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, email, password }),
  });
  token = data.access_token;
  user = { username: data.username, coins: data.coins };
  localStorage.setItem('pitlane_token', token);
  localStorage.setItem('pitlane_user', JSON.stringify(user));
  updateAuthUI();
  closeModal();
}

async function login(username, password) {
  const data = await api('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  token = data.access_token;
  user = { username: data.username, coins: data.coins };
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

  if (type === 'register') {
    modal.innerHTML = `
      <h2>加入 PitLane</h2>
      <div class="form-group">
        <label>用戶名稱</label>
        <input type="text" id="reg-username" placeholder="your_name" />
      </div>
      <div class="form-group">
        <label>Email</label>
        <input type="email" id="reg-email" placeholder="you@example.com" />
      </div>
      <div class="form-group">
        <label>密碼</label>
        <input type="password" id="reg-password" placeholder="至少 4 位" />
      </div>
      <div id="auth-error" class="error-msg"></div>
      <div class="form-actions">
        <button class="btn btn-outline" onclick="closeModal()">取消</button>
        <button class="btn btn-gold" onclick="handleRegister()">註冊</button>
      </div>
      <div class="switch-link">已有帳號？<a href="#" onclick="showModal('login')">登入</a></div>
    `;
  } else {
    modal.innerHTML = `
      <h2>登入 PitLane</h2>
      <div class="form-group">
        <label>用戶名稱</label>
        <input type="text" id="login-username" placeholder="your_name" />
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
      <div class="switch-link">還沒帳號？<a href="#" onclick="showModal('register')">註冊</a></div>
    `;
  }
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('active');
}

async function handleRegister() {
  const u = document.getElementById('reg-username').value.trim();
  const e = document.getElementById('reg-email').value.trim();
  const p = document.getElementById('reg-password').value;
  try {
    await register(u, e, p);
  } catch (err) {
    document.getElementById('auth-error').textContent = err.message;
  }
}

async function handleLogin() {
  const u = document.getElementById('login-username').value.trim();
  const p = document.getElementById('login-password').value;
  try {
    await login(u, p);
  } catch (err) {
    document.getElementById('auth-error').textContent = err.message;
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
      <div class="stat-bar">
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
  // Close modal on overlay click
  document.getElementById('modal-overlay')?.addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeModal();
  });
  // Enter key in modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const loginBtn = document.getElementById('login-username');
      const regBtn = document.getElementById('reg-username');
      if (loginBtn) handleLogin();
      else if (regBtn) handleRegister();
    }
    if (e.key === 'Escape') closeModal();
  });
});
