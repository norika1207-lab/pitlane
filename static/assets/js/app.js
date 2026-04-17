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
      <button class="nav-user-btn" onclick="showProfileDashboard()">👤 ${user.username} ▾</button>
    `;
  } else {
    authArea.innerHTML = `
      <button class="btn btn-gold btn-sm" onclick="showModal('login')">Log In</button>
    `;
  }
}

// ─── PROFILE DASHBOARD ───
let _pdTab = 'overview';

function showProfileDashboard() {
  if (document.getElementById('pd-overlay')) return;
  const ov = document.createElement('div');
  ov.id = 'pd-overlay';
  ov.innerHTML = `
    <div class="pd-panel">
      <div class="pd-nav">
        <div class="pd-user-head">
          <div class="pd-avatar">${(user.username||'?')[0].toUpperCase()}</div>
          <div>
            <div class="pd-uname">${user.username}</div>
            <div class="pd-utag">Throttenix 會員</div>
          </div>
          <button class="pd-close" onclick="closeProfileDashboard()">✕</button>
        </div>
        <div class="pd-balance-box">
          <div class="pd-bal-lbl">USDClaw 餘額</div>
          <div class="pd-bal-amt">◆ ${formatNum(user.balance)}</div>
        </div>
        <div class="pd-menu">
          <div class="pd-menu-item ${_pdTab==='overview'?'active':''}" onclick="pdSwitch('overview',this)">🏆 帳戶概覽</div>
          <div class="pd-menu-group">
            <div class="pd-menu-label">🏎 F1 賽事成績</div>
            <div class="pd-menu-item pd-sub ${_pdTab==='bets'?'active':''}" onclick="pdSwitch('bets',this)">📋 下注紀錄</div>
            <div class="pd-menu-item pd-sub ${_pdTab==='dist'?'active':''}" onclick="pdSwitch('dist',this)">📊 下注分布圖</div>
            <div class="pd-menu-item pd-sub ${_pdTab==='pnl'?'active':''}" onclick="pdSwitch('pnl',this)">💰 總收益</div>
            <div class="pd-menu-item pd-sub ${_pdTab==='active'?'active':''}" onclick="pdSwitch('active',this)">⏳ 進行中下注</div>
          </div>
          <div class="pd-menu-item ${_pdTab==='cards'?'active':''}" onclick="pdSwitch('cards',this)">🃏 卡牌收藏</div>
          <div class="pd-menu-item ${_pdTab==='rank'?'active':''}" onclick="pdSwitch('rank',this)">🏅 排行榜</div>
        </div>
        <button class="pd-logout-btn" onclick="logout();closeProfileDashboard()">登出</button>
      </div>
      <div class="pd-content" id="pd-content">
        <div class="pd-loading">載入中…</div>
      </div>
    </div>
  `;
  ov.addEventListener('click', e => { if (e.target === ov) closeProfileDashboard(); });
  document.body.appendChild(ov);
  pdSwitch(_pdTab, ov.querySelector('.pd-menu-item.active'));
}

function closeProfileDashboard() {
  document.getElementById('pd-overlay')?.remove();
}

function pdSwitch(tab, el) {
  _pdTab = tab;
  document.querySelectorAll('.pd-menu-item').forEach(x => x.classList.remove('active'));
  if (el) el.classList.add('active');
  const content = document.getElementById('pd-content');
  if (!content) return;
  content.innerHTML = '<div class="pd-loading">載入中…</div>';
  ({
    overview: pdOverview,
    bets:     pdBets,
    dist:     pdDist,
    pnl:      pdPnl,
    active:   pdActiveBets,
    cards:    pdCards,
    rank:     pdRank,
  }[tab] || pdOverview)(content);
}

async function pdOverview(el) {
  try {
    const d = await api('/api/profile');
    el.innerHTML = `
      <div class="pd-section-title">帳戶概覽</div>
      <div class="pd-stat-grid">
        <div class="pd-stat"><div class="pd-stat-v">${formatNum(d.balance)}</div><div class="pd-stat-l">USDClaw 餘額</div></div>
        <div class="pd-stat"><div class="pd-stat-v">${d.total_bets}</div><div class="pd-stat-l">總下注次數</div></div>
        <div class="pd-stat"><div class="pd-stat-v">${d.total_wins}</div><div class="pd-stat-l">獲勝次數</div></div>
        <div class="pd-stat"><div class="pd-stat-v">${d.win_rate}%</div><div class="pd-stat-l">勝率</div></div>
      </div>
      <div class="pd-level-row">
        <span class="pd-level-badge level-${d.rarity_level}">${d.rarity_name}</span>
        <span style="color:#888;font-size:12px">${d.rarity_label}</span>
      </div>
      <div class="pd-quick-links">
        <a class="pd-qlink" href="/race">🏁 前往下注</a>
        <a class="pd-qlink" href="/collection">🃏 我的卡牌</a>
        <a class="pd-qlink" href="https://clawstockmarket.com" target="_blank">🏦 交易所 ↗</a>
      </div>
    `;
  } catch(e) { el.innerHTML = `<div class="pd-err">載入失敗</div>`; }
}

async function pdBets(el) {
  try {
    const d = await api('/api/bets/my');
    const bets = d.bets || [];
    if (!bets.length) { el.innerHTML = `<div class="pd-section-title">下注紀錄</div><div class="pd-empty">尚無下注紀錄</div>`; return; }
    el.innerHTML = `
      <div class="pd-section-title">下注紀錄 <span class="pd-count">${bets.length} 筆</span></div>
      <div class="pd-table-wrap">
      <table class="pd-table">
        <thead><tr>
          <th>賽事</th><th>預測車手</th><th>下注金額</th><th>方式</th><th>日期</th><th>勝率估算</th><th>結果</th><th>收益</th>
        </tr></thead>
        <tbody>
          ${bets.map(b => {
            const won = b.result === 'won';
            const lost = b.result === 'lost';
            const pnl = b.payout != null ? b.payout - b.amount : null;
            return `<tr>
              <td class="pd-td-race">${b.race_name || b.race_id}</td>
              <td><span class="pd-driver">${b.prediction || '—'}</span></td>
              <td class="pd-num">◆ ${formatNum(b.amount)}</td>
              <td><span class="pd-bet-type">${b.bet_type || '—'}</span></td>
              <td class="pd-date">${b.created_at ? b.created_at.slice(0,10) : '—'}</td>
              <td class="pd-num">${b.odds ? (b.odds*100).toFixed(0)+'%' : '—'}</td>
              <td><span class="pd-result ${won?'won':lost?'lost':'pending'}">${won?'✓ 勝':lost?'✗ 敗':b.result||'待定'}</span></td>
              <td class="pd-num ${pnl>0?'pos':pnl<0?'neg':''}">${pnl!=null?(pnl>0?'+':'')+formatNum(pnl):'—'}</td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>
      </div>
    `;
  } catch(e) { el.innerHTML = `<div class="pd-err">載入失敗</div>`; }
}

async function pdDist(el) {
  try {
    const d = await api('/api/bets/my');
    const bets = d.bets || [];
    if (!bets.length) { el.innerHTML = `<div class="pd-section-title">下注分布圖</div><div class="pd-empty">尚無下注資料</div>`; return; }
    const byDriver = {};
    bets.forEach(b => {
      const k = b.prediction || '不明';
      byDriver[k] = (byDriver[k] || 0) + Number(b.amount);
    });
    const sorted = Object.entries(byDriver).sort((a,b)=>b[1]-a[1]);
    const total = sorted.reduce((s,[,v])=>s+v, 0);
    const COLORS = ['#e8ff00','#00D2BE','#E10600','#00b0ff','#ff9800','#a020f0','#ff5555','#44ff88','#ff88cc','#88aaff'];
    el.innerHTML = `
      <div class="pd-section-title">下注分布圖 <span class="pd-count">依車手</span></div>
      <div class="pd-dist-wrap">
        <div class="pd-donut-wrap">
          <svg viewBox="0 0 120 120" class="pd-donut">
            ${pdDonutSlices(sorted, total, COLORS)}
            <text x="60" y="55" text-anchor="middle" class="pd-donut-lbl1">總下注</text>
            <text x="60" y="70" text-anchor="middle" class="pd-donut-lbl2">${formatNum(total)}</text>
          </svg>
        </div>
        <div class="pd-dist-legend">
          ${sorted.map(([name, amt], i) => `
            <div class="pd-legend-row">
              <span class="pd-legend-dot" style="background:${COLORS[i%COLORS.length]}"></span>
              <span class="pd-legend-name">${name}</span>
              <span class="pd-legend-pct">${(amt/total*100).toFixed(1)}%</span>
              <span class="pd-legend-amt">◆ ${formatNum(amt)}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  } catch(e) { el.innerHTML = `<div class="pd-err">載入失敗</div>`; }
}

function pdDonutSlices(sorted, total, colors) {
  if (!total) return '';
  let slices = '';
  let offset = 0;
  const r = 40, cx = 60, cy = 60, circ = 2 * Math.PI * r;
  sorted.forEach(([, amt], i) => {
    const pct = amt / total;
    const dash = pct * circ;
    const gap  = circ - dash;
    slices += `<circle r="${r}" cx="${cx}" cy="${cy}" fill="none"
      stroke="${colors[i%colors.length]}" stroke-width="18"
      stroke-dasharray="${dash} ${gap}"
      stroke-dashoffset="${-offset * circ}"
      transform="rotate(-90 ${cx} ${cy})"/>`;
    offset += pct;
  });
  return slices;
}

async function pdPnl(el) {
  try {
    const d = await api('/api/bets/my');
    const bets = (d.bets || []).filter(b => b.result && b.result !== 'pending').reverse();
    if (!bets.length) { el.innerHTML = `<div class="pd-section-title">總收益</div><div class="pd-empty">尚無已結算下注</div>`; return; }
    let cum = 0;
    const points = bets.map(b => {
      cum += (b.payout||0) - (b.amount||0);
      return { date: (b.created_at||'').slice(0,10), val: cum, race: b.race_name||b.race_id };
    });
    const maxV = Math.max(...points.map(p=>p.val), 0);
    const minV = Math.min(...points.map(p=>p.val), 0);
    const range = maxV - minV || 1;
    const W = 480, H = 160, PAD = 20;
    const toX = i => PAD + (i / (points.length - 1 || 1)) * (W - PAD*2);
    const toY = v => PAD + (1 - (v - minV) / range) * (H - PAD*2);
    const pathD = points.map((p,i) => `${i===0?'M':'L'}${toX(i)},${toY(p.val)}`).join(' ');
    const areaD = `${pathD} L${toX(points.length-1)},${toY(minV)} L${toX(0)},${toY(minV)} Z`;
    const last = points[points.length-1].val;
    const totalColor = last >= 0 ? '#00D2BE' : '#E10600';
    el.innerHTML = `
      <div class="pd-section-title">總收益</div>
      <div class="pd-pnl-summary">
        <div class="pd-stat"><div class="pd-stat-v" style="color:${totalColor}">${last>=0?'+':''}${formatNum(last)}</div><div class="pd-stat-l">累計收益</div></div>
        <div class="pd-stat"><div class="pd-stat-v">${bets.length}</div><div class="pd-stat-l">已結算下注</div></div>
        <div class="pd-stat"><div class="pd-stat-v" style="color:#00D2BE">${formatNum(Math.max(...points.map(p=>p.val)))}</div><div class="pd-stat-l">歷史最高</div></div>
      </div>
      <div class="pd-chart-wrap">
        <svg viewBox="0 0 ${W} ${H}" class="pd-line-chart">
          <defs>
            <linearGradient id="pnl-grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="${totalColor}" stop-opacity=".3"/>
              <stop offset="100%" stop-color="${totalColor}" stop-opacity="0"/>
            </linearGradient>
          </defs>
          <line x1="${PAD}" y1="${toY(0)}" x2="${W-PAD}" y2="${toY(0)}" stroke="#333" stroke-width="1" stroke-dasharray="4 4"/>
          <path d="${areaD}" fill="url(#pnl-grad)"/>
          <path d="${pathD}" fill="none" stroke="${totalColor}" stroke-width="2" stroke-linecap="round"/>
          ${points.map((p,i)=>`<circle cx="${toX(i)}" cy="${toY(p.val)}" r="3" fill="${totalColor}"><title>${p.race}: ${p.val>=0?'+':''}${formatNum(p.val)}</title></circle>`).join('')}
        </svg>
      </div>
    `;
  } catch(e) { el.innerHTML = `<div class="pd-err">載入失敗</div>`; }
}

async function pdActiveBets(el) {
  try {
    const d = await api('/api/bets/my');
    const bets = (d.bets || []).filter(b => !b.result || b.result === 'pending');
    el.innerHTML = `<div class="pd-section-title">進行中下注 <span class="pd-count">${bets.length} 筆</span></div>`;
    if (!bets.length) { el.innerHTML += `<div class="pd-empty">目前無進行中下注</div>`; return; }
    el.innerHTML += `<div class="pd-table-wrap"><table class="pd-table">
      <thead><tr><th>賽事</th><th>預測車手</th><th>下注金額</th><th>方式</th><th>下注日期</th><th>勝率估算</th></tr></thead>
      <tbody>${bets.map(b=>`<tr>
        <td class="pd-td-race">${b.race_name||b.race_id}</td>
        <td><span class="pd-driver">${b.prediction||'—'}</span></td>
        <td class="pd-num">◆ ${formatNum(b.amount)}</td>
        <td><span class="pd-bet-type">${b.bet_type||'—'}</span></td>
        <td class="pd-date">${(b.created_at||'').slice(0,10)}</td>
        <td class="pd-num">${b.odds?(b.odds*100).toFixed(0)+'%':'—'}</td>
      </tr>`).join('')}</tbody>
    </table></div>`;
  } catch(e) { el.innerHTML = `<div class="pd-err">載入失敗</div>`; }
}

function pdCards(el) {
  el.innerHTML = `
    <div class="pd-section-title">卡牌收藏</div>
    <div class="pd-quick-links" style="flex-direction:column;gap:10px">
      <a class="pd-qlink-big" href="/collection">🃏 瀏覽所有賽季卡牌</a>
      <a class="pd-qlink-big" href="/cards">🏎 我的 F1 卡牌</a>
    </div>
  `;
}

function pdRank(el) {
  el.innerHTML = `<div class="pd-section-title">排行榜</div><div class="pd-loading">載入中…</div>`;
  api('/api/profile/leaderboard').then(d => {
    const rows = d.leaderboard || [];
    el.innerHTML = `<div class="pd-section-title">排行榜 <span class="pd-count">Top ${rows.length}</span></div>
    <div class="pd-table-wrap"><table class="pd-table">
      <thead><tr><th>#</th><th>用戶</th><th>勝率</th><th>下注次數</th><th>級別</th></tr></thead>
      <tbody>${rows.map((r,i)=>`<tr class="${r.username===user?.username?'pd-me':''}">
        <td class="pd-num">${i+1}</td>
        <td>${r.username}</td>
        <td class="pd-num">${r.win_rate??0}%</td>
        <td class="pd-num">${r.total_bets??0}</td>
        <td><span class="pd-level-badge level-${r.rarity_level||'silverstone'}">${r.rarity_name||'—'}</span></td>
      </tr>`).join('')}</tbody>
    </table></div>`;
  }).catch(()=>{ el.innerHTML=`<div class="pd-section-title">排行榜</div><div class="pd-err">載入失敗</div>`; });
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
