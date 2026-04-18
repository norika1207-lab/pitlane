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
// Unified nav auth renderer — inline styles so buttons look identical on every
// page regardless of which stylesheet that page loads. Container is forced to
// right-align to match home's layout.
const NAV_BTN_BASE =
  "padding:7px 16px;border-radius:8px;font-family:'Barlow Condensed',sans-serif;" +
  "font-size:13px;font-weight:700;letter-spacing:.05em;cursor:pointer;line-height:1;";
const NAV_BTN_GHOST = NAV_BTN_BASE + "border:1px solid #333;background:transparent;color:#ccc;";
const NAV_BTN_GOLD  = NAV_BTN_BASE + "border:none;background:#e8ff00;color:#000;";

function updateAuthUI() {
  const authArea = document.getElementById('nav-auth');
  if (!authArea) return;
  // Force right-alignment identical to home, regardless of page CSS
  Object.assign(authArea.style, {
    display: 'flex', gap: '8px', alignItems: 'center',
    marginLeft: 'auto', justifySelf: 'end',
  });
  if (user) {
    authArea.innerHTML = `
      <span style="color:#e8ff00;font-weight:700;font-size:13px;font-family:'Barlow Condensed',sans-serif;letter-spacing:.05em;">◆ <span id="user-coins">${formatNum(user.balance)}</span></span>
      <button onclick="showProfileDashboard()" style="${NAV_BTN_GHOST}">👤 ${user.username} ▾</button>
    `;
  } else {
    authArea.innerHTML = `
      <button onclick="showModal('login')" style="${NAV_BTN_GHOST}">Log In</button>
      <button onclick="showModal('login')" style="${NAV_BTN_GOLD}">Sign Up</button>
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
            <div class="pd-utag">Throttenix Member</div>
          </div>
          <button class="pd-close" onclick="closeProfileDashboard()">✕</button>
        </div>
        <div class="pd-balance-box">
          <div class="pd-bal-lbl">USDClaw Balance</div>
          <div class="pd-bal-amt">◆ ${formatNum(user.balance)}</div>
        </div>

        <div class="pd-menu">
          <!-- Buy CTA block (pinned at top) -->
          <div class="pd-cta-block">
            <a class="pd-cta-btn" href="https://clawstockmarket.com" target="_blank">💎 Buy Diamond</a>
            <a class="pd-cta-btn secondary" href="https://clawstockmarket.com" target="_blank">💱 Swap USDClaw</a>
          </div>

          <!-- Account Overview -->
          <div class="pd-menu-item ${_pdTab==='overview'?'active':''}" onclick="pdSwitch('overview',this)">🏆 Overview</div>

          <!-- F1 primary section (expanded by default) -->
          <div class="pd-acc-head" onclick="pdToggleGroup(this)">
            <span>🏎 F1 Results</span>
            <span class="pd-acc-row-right">
              <a class="pd-ext-link" href="https://throttenix.com" target="_blank" onclick="event.stopPropagation()" title="Open Throttenix">↗</a>
              <span class="pd-chevron">▾</span>
            </span>
          </div>
          <div class="pd-acc-body open">
            <div class="pd-menu-item pd-sub ${_pdTab==='bets'?'active':''}" onclick="pdSwitch('bets',this)">📋 Pit History</div>
            <div class="pd-menu-item pd-sub ${_pdTab==='dist'?'active':''}" onclick="pdSwitch('dist',this)">📊 Pit Distribution</div>
            <div class="pd-menu-item pd-sub ${_pdTab==='pnl'?'active':''}" onclick="pdSwitch('pnl',this)">💰 Total P/L</div>
            <div class="pd-menu-item pd-sub ${_pdTab==='active'?'active':''}" onclick="pdSwitch('active',this)">⏳ Active Pits</div>
          </div>

          <div class="pd-menu-item ${_pdTab==='cards'?'active':''}" onclick="pdSwitch('cards',this)">🃏 Card Collection</div>
          <div class="pd-menu-item ${_pdTab==='rank'?'active':''}" onclick="pdSwitch('rank',this)">🏅 Leaderboard</div>

          <!-- Other platforms (collapsed by default) -->
          <div class="pd-section-divider">Other Platforms</div>

          <div class="pd-acc-head" onclick="pdToggleGroup(this)">
            <span>🐎 Horse Racing · Turfenix</span>
            <span class="pd-acc-row-right">
              <a class="pd-ext-link" href="https://turfenix.com" target="_blank" onclick="event.stopPropagation()" title="Open Turfenix">↗</a>
              <span class="pd-chevron collapsed">▸</span>
            </span>
          </div>
          <div class="pd-acc-body">
            <a class="pd-menu-item pd-sub pd-ext-item" href="https://turfenix.com" target="_blank">🏁 Horse Racing Pits</a>
            <a class="pd-menu-item pd-sub pd-ext-item" href="https://turfenix.com/leaderboard" target="_blank">🏅 Horse Racing Leaderboard</a>
          </div>

          <div class="pd-acc-head" onclick="pdToggleGroup(this)">
            <span>🎮 Esports</span>
            <span class="pd-acc-row-right">
              <a class="pd-ext-link" href="http://31.97.221.240:8003" target="_blank" onclick="event.stopPropagation()" title="Open Esports">↗</a>
              <span class="pd-chevron collapsed">▸</span>
            </span>
          </div>
          <div class="pd-acc-body">
            <a class="pd-menu-item pd-sub pd-ext-item" href="http://31.97.221.240:8003" target="_blank">🏁 Esports Pits</a>
            <a class="pd-menu-item pd-sub pd-ext-item" href="http://31.97.221.240:8003/leaderboard" target="_blank">🏅 Esports Leaderboard</a>
          </div>

          <!-- Stock market pinned at bottom -->
          <div class="pd-acc-head" onclick="pdToggleGroup(this)">
            <span>🏦 Stock Market · ClawStockMarket</span>
            <span class="pd-acc-row-right">
              <a class="pd-ext-link" href="https://clawstockmarket.com" target="_blank" onclick="event.stopPropagation()" title="Open ClawStockMarket">↗</a>
              <span class="pd-chevron collapsed">▸</span>
            </span>
          </div>
          <div class="pd-acc-body">
            <a class="pd-menu-item pd-sub pd-ext-item" href="https://clawstockmarket.com" target="_blank">📈 Go to Exchange</a>
            <a class="pd-menu-item pd-sub pd-ext-item" href="https://clawstockmarket.com/dashboard" target="_blank">💎 Buy Diamond</a>
          </div>
        </div>

        <button class="pd-logout-btn" onclick="logout();closeProfileDashboard()">Log Out</button>
      </div>
      <div class="pd-content" id="pd-content">
        <div class="pd-loading">Loading…</div>
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

function pdToggleGroup(head) {
  const body = head.nextElementSibling;
  const chevron = head.querySelector('.pd-chevron');
  const isOpen = body.classList.contains('open');
  body.classList.toggle('open', !isOpen);
  if (chevron) {
    chevron.textContent = isOpen ? '▸' : '▾';
    chevron.classList.toggle('collapsed', isOpen);
  }
}

function pdSwitch(tab, el) {
  _pdTab = tab;
  document.querySelectorAll('.pd-menu-item').forEach(x => x.classList.remove('active'));
  if (el) el.classList.add('active');
  const content = document.getElementById('pd-content');
  if (!content) return;
  content.innerHTML = '<div class="pd-loading">Loading…</div>';
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
      <div class="pd-section-title">Account Overview</div>
      <div class="pd-stat-grid">
        <div class="pd-stat"><div class="pd-stat-v">${formatNum(d.balance)}</div><div class="pd-stat-l">USDClaw Balance</div></div>
        <div class="pd-stat"><div class="pd-stat-v">${d.total_bets}</div><div class="pd-stat-l">Total Pits</div></div>
        <div class="pd-stat"><div class="pd-stat-v">${d.total_wins}</div><div class="pd-stat-l">Wins</div></div>
        <div class="pd-stat"><div class="pd-stat-v">${d.win_rate}%</div><div class="pd-stat-l">Win Rate</div></div>
      </div>
      <div class="pd-level-row">
        <span class="pd-level-badge level-${d.rarity_level}">${d.rarity_name}</span>
        <span style="color:#888;font-size:12px">${d.rarity_label}</span>
      </div>
      <div class="pd-quick-links">
        <a class="pd-qlink" href="/race">🏁 Pit In</a>
        <a class="pd-qlink" href="/collection">🃏 My Cards</a>
        <a class="pd-qlink" href="https://clawstockmarket.com" target="_blank">🏦 Exchange ↗</a>
      </div>
    `;
  } catch(e) { el.innerHTML = `<div class="pd-err">Failed to load</div>`; }
}

async function pdBets(el) {
  try {
    const d = await api('/api/bets/my');
    const bets = d.bets || [];
    if (!bets.length) { el.innerHTML = `<div class="pd-section-title">Pit History</div><div class="pd-empty">No pits yet</div>`; return; }
    el.innerHTML = `
      <div class="pd-section-title">Pit History <span class="pd-count">${bets.length} entries</span></div>
      <div class="pd-table-wrap">
      <table class="pd-table">
        <thead><tr>
          <th>Race</th><th>Driver Pick</th><th>Pit Stake</th><th>Type</th><th>Date</th><th>Implied %</th><th>Result</th><th>P/L</th>
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
              <td><span class="pd-result ${won?'won':lost?'lost':'pending'}">${won?'✓ Won':lost?'✗ Lost':b.result||'Pending'}</span></td>
              <td class="pd-num ${pnl>0?'pos':pnl<0?'neg':''}">${pnl!=null?(pnl>0?'+':'')+formatNum(pnl):'—'}</td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>
      </div>
    `;
  } catch(e) { el.innerHTML = `<div class="pd-err">Failed to load</div>`; }
}

async function pdDist(el) {
  try {
    const d = await api('/api/bets/my');
    const bets = d.bets || [];
    if (!bets.length) { el.innerHTML = `<div class="pd-section-title">Pit Distribution</div><div class="pd-empty">No pit data yet</div>`; return; }
    const byDriver = {};
    bets.forEach(b => {
      const k = b.prediction || 'Unknown';
      byDriver[k] = (byDriver[k] || 0) + Number(b.amount);
    });
    const sorted = Object.entries(byDriver).sort((a,b)=>b[1]-a[1]);
    const total = sorted.reduce((s,[,v])=>s+v, 0);
    const COLORS = ['#e8ff00','#00D2BE','#E10600','#00b0ff','#ff9800','#a020f0','#ff5555','#44ff88','#ff88cc','#88aaff'];
    el.innerHTML = `
      <div class="pd-section-title">Pit Distribution <span class="pd-count">by driver</span></div>
      <div class="pd-dist-wrap">
        <div class="pd-donut-wrap">
          <svg viewBox="0 0 120 120" class="pd-donut">
            ${pdDonutSlices(sorted, total, COLORS)}
            <text x="60" y="55" text-anchor="middle" class="pd-donut-lbl1">Total Pits</text>
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
  } catch(e) { el.innerHTML = `<div class="pd-err">Failed to load</div>`; }
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
    if (!bets.length) { el.innerHTML = `<div class="pd-section-title">Total P/L</div><div class="pd-empty">No settled pits yet</div>`; return; }
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
      <div class="pd-section-title">Total P/L</div>
      <div class="pd-pnl-summary">
        <div class="pd-stat"><div class="pd-stat-v" style="color:${totalColor}">${last>=0?'+':''}${formatNum(last)}</div><div class="pd-stat-l">Cumulative P/L</div></div>
        <div class="pd-stat"><div class="pd-stat-v">${bets.length}</div><div class="pd-stat-l">Settled Pits</div></div>
        <div class="pd-stat"><div class="pd-stat-v" style="color:#00D2BE">${formatNum(Math.max(...points.map(p=>p.val)))}</div><div class="pd-stat-l">All-time High</div></div>
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
  } catch(e) { el.innerHTML = `<div class="pd-err">Failed to load</div>`; }
}

async function pdActiveBets(el) {
  try {
    const d = await api('/api/bets/my');
    const bets = (d.bets || []).filter(b => !b.result || b.result === 'pending');
    el.innerHTML = `<div class="pd-section-title">Active Pits <span class="pd-count">${bets.length} entries</span></div>`;
    if (!bets.length) { el.innerHTML += `<div class="pd-empty">No active pits right now</div>`; return; }
    el.innerHTML += `<div class="pd-table-wrap"><table class="pd-table">
      <thead><tr><th>Race</th><th>Driver Pick</th><th>Pit Stake</th><th>Type</th><th>Pit Date</th><th>Implied %</th></tr></thead>
      <tbody>${bets.map(b=>`<tr>
        <td class="pd-td-race">${b.race_name||b.race_id}</td>
        <td><span class="pd-driver">${b.prediction||'—'}</span></td>
        <td class="pd-num">◆ ${formatNum(b.amount)}</td>
        <td><span class="pd-bet-type">${b.bet_type||'—'}</span></td>
        <td class="pd-date">${(b.created_at||'').slice(0,10)}</td>
        <td class="pd-num">${b.odds?(b.odds*100).toFixed(0)+'%':'—'}</td>
      </tr>`).join('')}</tbody>
    </table></div>`;
  } catch(e) { el.innerHTML = `<div class="pd-err">Failed to load</div>`; }
}

function pdCards(el) {
  el.innerHTML = `
    <div class="pd-section-title">Card Collection</div>
    <div class="pd-quick-links" style="flex-direction:column;gap:10px">
      <a class="pd-qlink-big" href="/collection">🃏 Browse all seasons</a>
      <a class="pd-qlink-big" href="/cards">🏎 My F1 Cards</a>
    </div>
  `;
}

function pdRank(el) {
  el.innerHTML = `<div class="pd-section-title">Leaderboard</div><div class="pd-loading">Loading…</div>`;
  api('/api/profile/leaderboard').then(d => {
    const rows = d.leaderboard || [];
    el.innerHTML = `<div class="pd-section-title">Leaderboard <span class="pd-count">Top ${rows.length}</span></div>
    <div class="pd-table-wrap"><table class="pd-table">
      <thead><tr><th>#</th><th>User</th><th>Win Rate</th><th>Total Pits</th><th>Tier</th></tr></thead>
      <tbody>${rows.map((r,i)=>`<tr class="${r.username===user?.username?'pd-me':''}">
        <td class="pd-num">${i+1}</td>
        <td>${r.username}</td>
        <td class="pd-num">${r.win_rate??0}%</td>
        <td class="pd-num">${r.total_bets??0}</td>
        <td><span class="pd-level-badge level-${r.rarity_level||'silverstone'}">${r.rarity_name||'—'}</span></td>
      </tr>`).join('')}</tbody>
    </table></div>`;
  }).catch(()=>{ el.innerHTML=`<div class="pd-section-title">Leaderboard</div><div class="pd-err">Failed to load</div>`; });
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

// ─── BRAND INJECTOR ─── every page gets favicon + racing chevron logo + tagline
const BRAND_LOGO_SVG = `<svg viewBox="0 0 48 48" width="26" height="26" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0">
  <defs>
    <linearGradient id="_tg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#ffea3a"/><stop offset="55%" stop-color="#d4a843"/><stop offset="100%" stop-color="#8a6d2c"/>
    </linearGradient>
    <linearGradient id="_yg" x1="0" x2="1" y1="0" y2="0.6">
      <stop offset="0%" stop-color="#fff07a"/><stop offset="100%" stop-color="#e8ff00"/>
    </linearGradient>
  </defs>
  <line x1="3" y1="9"  x2="15" y2="9"  stroke="#e8ff00" stroke-width="1.2" opacity=".55"/>
  <line x1="3" y1="13" x2="10" y2="13" stroke="#e8ff00" stroke-width=".9"  opacity=".30"/>
  <line x1="3" y1="39" x2="12" y2="39" stroke="#e8ff00" stroke-width=".9"  opacity=".30"/>
  <path d="M4 13 L13 13 L26 24 L13 35 L4 35 L17 24 Z"   fill="url(#_tg)"/>
  <path d="M20 13 L29 13 L42 24 L29 35 L20 35 L33 24 Z" fill="url(#_yg)"/>
</svg>`;

function installBrand() {
  // Favicon (idempotent)
  if (!document.querySelector('link[rel="icon"]')) {
    const link = document.createElement('link');
    link.rel = 'icon';
    link.type = 'image/svg+xml';
    link.href = '/static/assets/favicon.svg';
    document.head.appendChild(link);
  }

  // Global RWD + nav layout rules (idempotent)
  if (!document.getElementById('nav-rwd-rules')) {
    const s = document.createElement('style');
    s.id = 'nav-rwd-rules';
    s.textContent = `
      /* Kill scrollbar-induced layout shift (fixed nav appears to "jump"
         when content height changes and the scrollbar toggles). */
      html { scrollbar-gutter: stable; overflow-y: scroll; }

      /* Logo block — allow it to shrink without wrapping */
      .nav-brand, .nav-logo {
        min-width: 0;
        overflow: hidden;
      }
      .nav-tagline {
        flex-shrink: 1;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      /* Auth cluster — keep it on one line, hugging the right edge */
      #nav-auth { flex-shrink: 0 !important; }
      #nav-auth > * { flex-shrink: 0; }

      /* <1024px: tighten the middle link spacing */
      @media (max-width: 1024px) {
        .nav-links { gap: 14px !important; }
        .nav-links a { font-size: 12px !important; }
      }
      /* <820px: hide the center link bar entirely; nav becomes brand | auth */
      @media (max-width: 820px) {
        .nav-links { display: none !important; }
      }
      /* <600px: drop the subtitle tagline — nav is cramped */
      @media (max-width: 600px) {
        .nav-tagline { display: none !important; }
      }
      /* <520px: shrink Sign Up label and gaps so both buttons still fit */
      @media (max-width: 520px) {
        #nav-auth { gap: 6px !important; }
        #nav-auth button { padding: 6px 10px !important; font-size: 12px !important; }
      }
    `;
    document.head.appendChild(s);
  }

  // Remove the redundant "Profile" nav link (users access it via the
  // username dropdown on the right). Does nothing if already removed.
  document.querySelectorAll('.nav-links a[href="/profile"]').forEach(a => a.remove());

  const brand = document.querySelector('.nav-brand, .nav-logo');
  if (!brand) return;

  // Replace the old ".dot" / ".logo-dot" placeholder with the racing chevron SVG
  const oldDot = brand.querySelector('.dot, .logo-dot');
  if (oldDot && !brand.querySelector('.nav-mark')) {
    const mark = document.createElement('span');
    mark.className = 'nav-mark';
    mark.innerHTML = BRAND_LOGO_SVG;
    Object.assign(mark.style, {
      display: 'inline-flex', alignItems: 'center',
      filter: 'drop-shadow(0 0 6px rgba(232,255,0,.25))',
    });
    oldDot.replaceWith(mark);
  }

  // Tagline — stacked UNDER the THROTTENIX wordmark as a subtitle so it
  // takes zero horizontal space and cannot collide with nav links. Wrap the
  // existing "THROTTENIX" text node in a flex-column span and append the
  // tagline below it.
  if (!brand.querySelector('.nav-wordstack')) {
    // Find the first text node (the brand name) and wrap it
    const textNode = [...brand.childNodes].find(
      n => n.nodeType === Node.TEXT_NODE && n.textContent.trim()
    );
    if (textNode) {
      const stack = document.createElement('span');
      stack.className = 'nav-wordstack';
      Object.assign(stack.style, {
        display: 'inline-flex', flexDirection: 'column',
        justifyContent: 'center', lineHeight: '1',
        minWidth: '0',
      });
      const nameEl = document.createElement('span');
      nameEl.className = 'nav-wordmark';
      nameEl.textContent = textNode.textContent.trim();
      Object.assign(nameEl.style, { lineHeight: '1', whiteSpace: 'nowrap' });

      const tag = document.createElement('span');
      tag.className = 'nav-tagline';
      tag.textContent = 'SIMULATED BETTING · F1';
      Object.assign(tag.style, {
        marginTop: '3px',
        fontFamily: "'Barlow Condensed', 'IBM Plex Mono', monospace",
        fontSize: '9px', fontWeight: '700',
        letterSpacing: '.22em', color: '#888',
        textTransform: 'none', whiteSpace: 'nowrap',
      });

      stack.appendChild(nameEl);
      stack.appendChild(tag);
      textNode.replaceWith(stack);
    }
  }
}

// ─── INIT ───
document.addEventListener('DOMContentLoaded', () => {
  installBrand();
  updateAuthUI();
  document.getElementById('modal-overlay')?.addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && document.getElementById('login-username')) handleLogin();
    if (e.key === 'Escape') closeModal();
  });
});
