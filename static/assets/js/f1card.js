/* ═════════════════════════════════════════════════════════════
   F1 Card renderer — shared by cards.html and collection.html
   Exposes: window.F1Card = { buildCard, TIER_CONFIG, LOCAL_HEADSHOT }
   ═════════════════════════════════════════════════════════════ */
(function () {
  const LOCAL_HEADSHOT = code => code ? `/static/assets/drivers/${code.toLowerCase()}.png` : '';

  const TIER_CONFIG = {
    silverstone:{
      label:'SILVERSTONE',
      statColor:'linear-gradient(90deg,#555,#888)',
      svColor:'#aaa',
      teamColor:(c)=>c,
      ovrColor:'#ccc',
      winColor:'#44dd88',
      oddsColor:'#ccdd00',
      divider:'linear-gradient(90deg,transparent,#2a2a35,transparent)',
    },
    monza:{
      label:'MONZA',
      statColor:'linear-gradient(90deg,#1a4a9a,#6ab0ff)',
      svColor:'#6ab0ff',
      teamColor:()=>'#4a8acc',
      ovrColor:'#6ab0ff',
      winColor:'#00cc66',
      oddsColor:'#ddee00',
      divider:'linear-gradient(90deg,transparent,#1a3a6a,transparent)',
      ovrShadow:'0 0 10px rgba(54,113,198,0.6)',
    },
    suzuka:{
      label:'SUZUKA',
      statColor:'linear-gradient(90deg,#534AB7,#AFA9EC)',
      svColor:'#AFA9EC',
      teamColor:()=>'#8a84cc',
      ovrColor:'#AFA9EC',
      winColor:'#00ff88',
      oddsColor:'#eeff00',
      divider:'linear-gradient(90deg,transparent,rgba(127,119,221,0.4),transparent)',
      ovrShadow:'0 0 12px rgba(127,119,221,0.8)',
    },
    spa:{
      label:'SPA',
      statColor:'linear-gradient(90deg,#0044aa,#00ccff,#8800ff)',
      svColor:'#00ccff',
      teamColor:()=>'#0099cc',
      ovrColor:'#00ccff',
      winColor:'#00ff88',
      oddsColor:'#ffee00',
      divider:'linear-gradient(90deg,transparent,rgba(0,180,255,0.4),transparent)',
      ovrShadow:'0 0 15px rgba(0,200,255,1),0 0 30px rgba(0,200,255,0.5)',
    },
    monaco:{
      label:'MONACO',
      statColor:'linear-gradient(90deg,#a07830,#c9a84c,#f0d070,#c9a84c)',
      svColor:'#c9a84c',
      teamColor:()=>'#c9a84c',
      ovrColor:'#c9a84c',
      winColor:'#00ff88',
      oddsColor:'#ffff00',
      divider:'linear-gradient(90deg,transparent,rgba(201,168,76,0.6),transparent)',
      ovrShadow:'0 0 20px rgba(201,168,76,1),0 0 40px rgba(201,168,76,0.5)',
    },
  };

  function buildCard(d) {
    const t = TIER_CONFIG[d.tier] || TIER_CONFIG.silverstone;
    const emojiFilter = {
      silverstone:`drop-shadow(0 4px 10px ${d.color}40)`,
      monza:`drop-shadow(0 0 10px ${d.color}99)`,
      suzuka:`drop-shadow(0 0 14px rgba(127,119,221,0.9))`,
      spa:`drop-shadow(0 0 16px rgba(0,200,255,1))`,
      monaco:`drop-shadow(0 0 20px rgba(201,168,76,1)) drop-shadow(0 0 40px rgba(255,200,100,0.6))`,
    }[d.tier];

    const extras = {
      silverstone:`
        <div class="s-top-line"></div>
        <div class="s-corner"></div>
        <div class="s-sweep"></div>
        <div class="s-accent" style="--team-color:${d.color}"></div>`,
      monza:`
        <div class="m-top"></div>
        <div class="m-glow"></div>
        <div class="m-sweep"></div>
        <div class="m-accent"></div>`,
      suzuka:`
        <div class="sz-outer"></div>
        <div class="sz-diamond"></div>
        <div class="sz-topglow"></div>
        <div class="sz-sweep"></div>
        <div class="sz-sl"></div>
        <div class="sz-sr"></div>`,
      spa:`
        <div class="sp-outer"></div>
        <div class="sp-rainbow"></div>
        <div class="sp-grid"></div>
        <div class="sp-sweep"></div>
        <div class="sp-top"></div>
        <div class="sp-bot"></div>
        <div class="sp-sl"></div>
        <div class="sp-sr"></div>`,
      monaco:`
        <div class="mc-outer"></div>
        <div class="mc-diamond"></div>
        <div class="mc-rotate"></div>
        <div class="mc-rainbow"></div>
        <div class="mc-sweep"></div>
        <div class="mc-check-top"></div>
        <div class="mc-check-bot"></div>
        <div class="mc-sl"></div>
        <div class="mc-sr"></div>
        <div class="mc-topglow"></div>
        <div class="mc-p" style="top:15%;left:10%;animation-delay:0s"></div>
        <div class="mc-p" style="top:28%;right:12%;animation-delay:0.7s"></div>
        <div class="mc-p" style="top:50%;left:7%;animation-delay:1.4s"></div>
        <div class="mc-p" style="top:70%;right:9%;animation-delay:0.4s"></div>
        <div class="mc-crown">
          <svg width="40" height="32" viewBox="0 0 40 32" style="position:absolute;top:8px;left:50%;transform:translateX(-50%);z-index:20;">
            <path d="M4 26 L4 16 L10 22 L20 8 L30 22 L36 16 L36 26 Z" fill="#c9a84c" stroke="#f0d070" stroke-width="0.8"/>
            <rect x="4" y="24" width="32" height="4" rx="1" fill="#c9a84c" stroke="#f0d070" stroke-width="0.8"/>
            <circle cx="20" cy="7" r="2.5" fill="#f0d070"/>
            <circle cx="10" cy="21" r="2" fill="#f0d070"/>
            <circle cx="30" cy="21" r="2" fill="#f0d070"/>
            <circle cx="12" cy="26" r="1.2" fill="#fff" opacity="0.8"/>
            <circle cx="20" cy="26" r="1.2" fill="#fff" opacity="0.8"/>
            <circle cx="28" cy="26" r="1.2" fill="#fff" opacity="0.8"/>
            <path d="M4 26 L4 16 L10 22 L20 8 L30 22 L36 16 L36 26 Z" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="0.5"/>
          </svg>
        </div>`,
    }[d.tier];

    const monacoFlag = d.tier === 'monaco' ? `
      <div style="display:flex;justify-content:center;margin-bottom:5px;position:relative;z-index:10;">
        <svg width="80" height="6" viewBox="0 0 80 6">
          <rect x="0"  y="0" width="8" height="6" fill="#c9a84c" opacity="0.8"/><rect x="8"  y="0" width="8" height="6" fill="#050400"/>
          <rect x="16" y="0" width="8" height="6" fill="#c9a84c" opacity="0.8"/><rect x="24" y="0" width="8" height="6" fill="#050400"/>
          <rect x="32" y="0" width="8" height="6" fill="#c9a84c" opacity="0.8"/><rect x="40" y="0" width="8" height="6" fill="#050400"/>
          <rect x="48" y="0" width="8" height="6" fill="#c9a84c" opacity="0.8"/><rect x="56" y="0" width="8" height="6" fill="#050400"/>
          <rect x="64" y="0" width="8" height="6" fill="#c9a84c" opacity="0.8"/><rect x="72" y="0" width="8" height="6" fill="#050400"/>
        </svg>
      </div>` : '';

    const emojiAnim = d.tier === 'monaco' ? `animation:float 3s ease-in-out infinite;` : '';
    const glowCircle = ['suzuka','spa','monaco'].includes(d.tier) ? `
      <div style="position:absolute;width:80px;height:80px;border-radius:50%;background:radial-gradient(circle,${{
        suzuka:'rgba(127,119,221,0.2)', spa:'rgba(0,200,255,0.2)', monaco:'rgba(201,168,76,0.3)'
      }[d.tier]} 0%,transparent 70%);animation:tg 2s ease-in-out infinite;"></div>` : '';

    const ovrStyle = `color:${t.ovrColor};${t.ovrShadow?`text-shadow:${t.ovrShadow};`:''}${d.tier==='monaco'?'font-size:28px;':''}`;
    const rarityTop = d.tier === 'monaco' ? 'top:46px;' : '';
    const yearBadge = d.isHistorical
      ? `<div class="c-hist-year" style="color:${t.ovrColor};opacity:.75;top:${d.tier==='monaco'?'64px':'26px'}">${d.season}</div>`
      : '';

    const code = (d.code || d.name?.slice(0,3) || '?').toUpperCase();
    const placeholder = `<div style="width:80px;height:80px;border-radius:50%;border:2px solid ${d.color};background:linear-gradient(135deg,${d.color}33,${d.color}11);display:flex;align-items:center;justify-content:center;font-family:'Barlow Condensed',sans-serif;font-weight:900;font-size:32px;letter-spacing:.04em;color:${d.color};text-shadow:0 1px 2px rgba(0,0,0,.5)">${code}</div>`;
    const safePlaceholder = placeholder.replace(/"/g, '&quot;');
    const imgOrPh = d.headshot
      ? `<img src="${d.headshot}" style="width:80px;height:80px;border-radius:50%;object-fit:cover;object-position:top center;border:2px solid ${d.color};filter:${emojiFilter};${emojiAnim}" onerror="this.outerHTML='${safePlaceholder}'">`
      : placeholder;

    return `
      <div class="card ${d.tier}" data-tier="${d.tier}">
        <div class="card-inner">
          ${extras}
          <span class="c-rarity" style="${rarityTop}color:${t.ovrColor};${d.tier==='monaco'?'text-shadow:0 0 10px rgba(201,168,76,1);':''}">${t.label}</span>
          ${yearBadge}
          <span class="c-num">${d.num}</span>
          <div class="c-art" style="z-index:5;">
            ${glowCircle}
            ${imgOrPh}
          </div>
          ${monacoFlag}
          <div class="c-info">
            <div class="c-name" style="${d.tier==='monaco'?'text-shadow:0 0 20px rgba(201,168,76,0.7);':''}">${d.name}</div>
            <div class="c-team" style="color:${t.teamColor(d.color)}">${d.team}</div>
            <div class="c-stats">
              ${['SPD','TYR','WET','OVT'].map((sl,i)=>{
                const vals = [d.stats.q,d.stats.t,d.stats.w,d.stats.o];
                return `<div class="c-stat">
                  <span class="c-sl" style="${['monaco','spa','suzuka'].includes(d.tier)?`color:${t.ovrColor};`:''}">${sl}</span>
                  <div class="c-sb"><div class="c-sf" style="width:${vals[i]}%;background:${t.statColor};${d.tier!=='silverstone'?`box-shadow:0 0 4px ${t.ovrColor}44;`:''}"></div></div>
                  <span class="c-sv" style="color:${t.svColor}">${vals[i]}</span>
                </div>`;
              }).join('')}
            </div>
            ${d.str && d.wk ? `
            <div class="c-sw">
              <div class="c-sw-row">
                <span class="c-sw-lbl" style="color:#44ff88">▲</span>
                <div class="c-sw-tags">${d.str.map(s=>`<span class="c-sw-tag str">${s}</span>`).join('')}</div>
              </div>
              <div class="c-sw-row">
                <span class="c-sw-lbl" style="color:#ff6060">▼</span>
                <div class="c-sw-tags">${d.wk.map(w=>`<span class="c-sw-tag wk">${w}</span>`).join('')}</div>
              </div>
            </div>` : ''}
          </div>
          <div class="c-divider" style="background:${t.divider};"></div>
          ${d.last5?.length ? `<div style="padding:4px 12px 0;display:flex;align-items:center;gap:3px;position:relative;z-index:5;">
            <span style="font-size:7px;color:#666;letter-spacing:.05em;font-family:'Barlow Condensed',sans-serif;margin-right:2px">L5</span>
            ${(()=>{const mx=Math.max(...d.last5,1);return d.last5.map(p=>`<div style="width:8px;height:${Math.max(3,Math.round(p/mx*18))}px;background:${p>0?t.statColor:'#222'};border-radius:1px;align-self:flex-end;${p>0?`box-shadow:0 0 3px ${t.ovrColor}44;`:''}"></div>`).join('')})()}
          </div>` : ''}
          <div class="c-bottom">
            <div>
              <div class="c-wn" style="color:${t.winColor};${d.tier==='monaco'?'text-shadow:0 0 12px rgba(0,255,136,1);':''}">${d.win}%</div>
              <div class="c-wl">WIN</div>
            </div>
            <div>
              <div class="c-ov" style="${ovrStyle}">${d.ovr}</div>
              <div class="c-ol">OVR</div>
            </div>
            <div>
              ${d.pts2024 ? `<div class="c-od" style="color:${t.oddsColor};${d.tier==='monaco'?'text-shadow:0 0 12px rgba(255,255,0,1);':''}">${d.pts2024}</div><div class="c-odl">PTS</div>` : `<div class="c-od" style="color:${t.oddsColor}">${d.odds}x</div><div class="c-odl">ODDS</div>`}
            </div>
          </div>
        </div>
      </div>`;
  }

  window.F1Card = { buildCard, TIER_CONFIG, LOCAL_HEADSHOT };
})();
