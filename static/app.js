'use strict';
const $ = (s, r = document) => r.querySelector(s), V = () => $('#view');
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const TA = {'Home': 'முகப்பு', 'Crop Plan': 'பயிர் திட்டம்', 'Intercrop': 'ஊடுபயிர்', 'Protect': 'பயிர் பாதுகாப்பு', 'Market': 'சந்தை',
  'Marketplace': 'நேரடி சந்தை', 'Services': 'சேவைகள்', 'Login': 'உள்நுழை', 'Account': 'கணக்கு', 'Logout': 'வெளியேறு', 'Register': 'பதிவு செய்',
  'District': 'மாவட்டம்', 'Soil': 'மண்', 'Water': 'நீர்', 'Season': 'பருவம்', 'Acres': 'ஏக்கர்', 'Recommend': 'பரிந்துரை', 'Crop': 'பயிர்',
  'Details': 'விவரம்', 'Calculate': 'கணக்கிடு', 'Analyze': 'ஆய்வு செய்', 'Leaf photo': 'இலை படம்', 'Symptoms you see': 'தெரியும் அறிகுறிகள்',
  'Email': 'மின்னஞ்சல்', 'Password': 'கடவுச்சொல்', 'Name': 'பெயர்', 'Role': 'பங்கு', 'Phone': 'தொலைபேசி', 'Order': 'ஆர்டர்',
  'Browse': 'பார்க்க', 'My listings': 'என் பட்டியல்', 'Orders': 'ஆர்டர்கள்', 'Bulk requests': 'மொத்த கோரிக்கைகள்', 'Search': 'தேடு',
  'Price': 'விலை', 'farmer': 'உழவர்', 'consumer': 'நுகர்வோர்', 'bulk_buyer': 'மொத்த வாங்குபவர்', 'service_provider': 'சேவை வழங்குநர்',
  'Estimated profit': 'மதிப்பிடப்பட்ட லாபம்', 'days': 'நாட்கள்', 'Generate layout': 'அமைப்பை உருவாக்கு',
  'From Soil to Sale — one intelligent platform for farmers': 'மண்ணிலிருந்து விற்பனை வரை — விவசாயிகளுக்கான ஒரே அறிவார்ந்த தளம்',
  'Estimates only. No yield, profit or price is guaranteed.': 'மதிப்பீடுகள் மட்டுமே. மகசூல், லாபம், விலைக்கு உத்தரவாதம் இல்லை.'};
let LANG = localStorage.getItem('lang') || 'en', TOKEN = localStorage.getItem('token') || '', USER = null, META = null, TAB = 'home', SUB = 'browse', DIST = '';
try { USER = JSON.parse(localStorage.getItem('user') || 'null'); } catch (e) { USER = null; }
const t = k => (LANG === 'ta' && TA[k]) || k, role = () => USER && USER.role;
const money = n => '₹' + Number(n).toLocaleString('en-IN');
const cropName = c => LANG === 'ta' ? META.crops[c].ta + ' (' + c + ')' : c;
const opts = (arr, selv, label) => arr.map(v => `<option value="${esc(v)}"${v === selv ? ' selected' : ''}>${esc(label ? label(v) : v)}</option>`).join('');
const sel = (n, l, o) => `<label>${t(l)}<select name="${n}">${o}</select></label>`;
const inp = (n, l, type = 'text', x = '') => `<label>${t(l)}<input name="${n}" type="${type}" ${x}></label>`;
const fd = f => Object.fromEntries(new FormData(f));
const on = (f, fn) => f.addEventListener('submit', async e => { e.preventDefault(); try { await fn(e); } catch (x) { toast(x.message, 1); } });
function toast(m, err) { const e = $('#toast'); e.textContent = m; e.className = 'show' + (err ? ' err' : ''); clearTimeout(toast.h); toast.h = setTimeout(() => e.className = '', 3500); if (!err && USER) refreshBadges(); }
async function api(path, o = {}) {
  const h = {}; if (TOKEN) h.Authorization = 'Bearer ' + TOKEN;
  let b = o.body; if (b && !(b instanceof FormData)) { h['Content-Type'] = 'application/json'; b = JSON.stringify(b); }
  const r = await fetch('/api' + path, {method: o.method || (b ? 'POST' : 'GET'), headers: h, body: b});
  const j = await r.json().catch(() => ({}));
  if (!r.ok) { if (r.status === 401 && TOKEN) logout(true); throw new Error(typeof j.detail === 'string' ? j.detail : 'Error ' + r.status); }
  return j;
}
function setUser(r) { TOKEN = r.token; USER = r.user; localStorage.setItem('token', TOKEN); localStorage.setItem('user', JSON.stringify(USER)); }
function logout(silent) { TOKEN = ''; USER = null; localStorage.removeItem('token'); localStorage.removeItem('user'); sessionStorage.removeItem('guest'); BADGE = {}; nav(); go(silent ? 'account' : 'home'); }
const ICO = {home: '🏠', plan: '🌾', intercrop: '🌿', protect: '🛡️', market: '📈', shop: '🛒', services: '🛠️', account: '👤'};
let BADGE = {};
function nav() {
  const show = !!(USER || sessionStorage.getItem('guest'));
  $('#nav').hidden = !show; $('.shell').classList.toggle('solo', !show);
  $('#logout').hidden = !USER; $('#logout').textContent = '🚪 ' + t('Logout'); $('#who').textContent = USER ? USER.name + ' · ' + t(USER.role) : '';
  const T = [['home', 'Home'], ['plan', 'Crop Plan'], ['intercrop', 'Intercrop'], ['protect', 'Protect'], ['market', 'Market'], ['shop', 'Marketplace'], ['services', 'Services'], ['account', USER ? 'Account' : 'Login']];
  $('#nav').innerHTML = T.map(([k, l]) => `<button data-t="${k}" class="${TAB === k ? 'on' : ''}"><span class="ico">${ICO[k]}</span><span class="lbl">${t(l)}</span><span class="bd" ${BADGE[k] ? '' : 'hidden'}>${BADGE[k] || ''}</span></button>`).join('');
  $('#nav').querySelectorAll('button').forEach(b => b.onclick = () => go(b.dataset.t));
  if (USER) refreshBadges();
}
async function refreshBadges() {
  if (!USER) { BADGE = {}; return; }
  try {
    const b = {};
    if (role() === 'farmer') { const [o, r] = await Promise.all([api('/orders'), api('/requests')]); b.shop = o.incoming.filter(x => x.status === 'placed').length + r.filter(x => x.status === 'open').length; }
    else if (role() === 'bulk_buyer') { const r = await api('/requests'); b.shop = r.filter(x => x.buyer_id === USER.id && x.status === 'open').reduce((a, x) => a + x.offers, 0); }
    else if (role() === 'service_provider') { const s = await api('/service-requests'); b.services = s.filter(x => x.status === 'open').length; }
    BADGE = b;
    $('#nav').querySelectorAll('[data-t]').forEach(x => { const n = BADGE[x.dataset.t], e = x.querySelector('.bd'); e.textContent = n || ''; e.hidden = !n; });
  } catch (e) { /* badges are optional */ }
}
function go(tab) { if (!USER && !sessionStorage.getItem('guest')) tab = 'account'; TAB = tab; nav(); document.documentElement.lang = LANG === 'ta' ? 'ta' : 'en'; Promise.resolve(({home, plan, intercrop, protect, market, shop, services, account})[tab]()).catch(x => toast(x.message, 1)); window.scrollTo(0, 0); }

function home() {
  const items = [['plan', 'Crop Plan', 'Crop recommendation with reasons and cost / profit estimates'], ['intercrop', 'Intercrop', 'Visual planting layout with spacing and plant counts'],
    ['protect', 'Protect', 'Leaf photo screening, severity and treatment guidance'], ['market', 'Market', 'Indicative price pattern and best selling months'],
    ['shop', 'Marketplace', 'Direct selling, orders and bulk requests'], ['services', 'Services', 'Experts and technicians near you']];
  V().innerHTML = `<section class="hero"><h1>AgriShield AI</h1><p>${t('From Soil to Sale — one intelligent platform for farmers')}</p>${USER ? `<span class="pill">${esc(USER.name)} · ${t(USER.role)}</span>` : ''}</section><div id="dash"></div>
  <div class="cards">${items.map(([k, a, b]) => `<button class="card" data-go="${k}"><b>${t(a)}</b><span>${t(b)}</span></button>`).join('')}</div>
  <p class="note">Demo logins: farmer@demo.com · consumer@demo.com · buyer@demo.com · expert@demo.com (password demo123)</p><p class="note">${t('Estimates only. No yield, profit or price is guaranteed.')}</p>`;
  V().querySelectorAll('[data-go]').forEach(b => b.onclick = () => go(b.dataset.go));
  dash();
}
const stat = (a, b) => `<div class="stats">${a.map(([n, l]) => `<div class="${n > 0 && /New|Open|Offers/.test(l) ? 'hot' : ''}"><b>${n}</b>${t(l)}</div>`).join('')}</div><div class="sub">${b.map(([k, l]) => `<button data-go="${k}">${t(l)}</button>`).join('')}</div>`;
async function dash() {
  if (!USER) return;
  let h = '';
  try {
    if (role() === 'farmer') {
      const [l, o, r] = await Promise.all([api('/listings?mine=1'), api('/orders'), api('/requests')]);
      h = stat([[l.length, 'My listings'], [o.incoming.filter(x => x.status === 'placed').length, 'New orders'], [r.filter(x => x.status === 'open').length, 'Open bulk requests']], [['plan', 'Crop Plan'], ['protect', 'Protect'], ['shop', 'Marketplace']]);
    } else if (role() === 'consumer') {
      const o = await api('/orders');
      h = stat([[o.placed.length, 'My orders'], [o.placed.filter(x => x.status === 'placed').length, 'Pending']], [['shop', 'Buy fresh produce']]);
    } else if (role() === 'bulk_buyer') {
      const r = (await api('/requests')).filter(x => x.buyer_id === USER.id);
      h = stat([[r.length, 'My requests'], [r.reduce((a, x) => a + x.offers, 0), 'Offers received']], [['shop', 'Post / review requests']]);
    } else {
      const s = await api('/service-requests');
      h = stat([[s.filter(x => x.status === 'open').length, 'New service requests']], [['services', 'Manage services']]);
    }
  } catch (e) { return; }
  const d = $('#dash');
  if (d) { d.innerHTML = '<h2>Your dashboard</h2>' + h; d.querySelectorAll('[data-go]').forEach(b => b.onclick = () => go(b.dataset.go)); }
}

function plan() {
  const crops = Object.keys(META.crops), blank = '<option value="">—</option>';
  V().innerHTML = `<h2>${t('Crop Plan')}</h2><form id="f" class="grid">${sel('district', 'District', blank + opts(META.districts))}${sel('soil', 'Soil', blank + opts(META.soils))}${sel('water', 'Water', blank + opts(META.water))}${sel('season', 'Season', opts(META.seasons))}${inp('acres', 'Acres', 'number', 'value="1" min="0.1" step="any"')}<button>${t('Recommend')}</button></form><p class="note">Pick a district to auto-fill typical soil and water, or choose them yourself.</p><div id="out"></div>
  <h3>Cost, yield and profit estimate</h3><form id="g" class="grid">${sel('crop', 'Crop', opts(crops, '', cropName))}${inp('acres', 'Acres', 'number', 'value="1" min="0.1" step="any"')}${inp('price', 'Price (optional, ₹ per unit)', 'number', 'step="any"')}<button>${t('Calculate')}</button></form><div id="out2"></div>`;
  const f = $('#f'), g = $('#g');
  on(f, async () => {
    const r = await api('/recommend', {body: fd(f)});
    $('#out').innerHTML = r.results.length ? r.results.map(x => `<div class="card2"><h4>${esc(cropName(x.crop))} <small>(score ${x.score})</small></h4><ul>${x.reasons.map(y => `<li>${esc(y)}</li>`).join('')}</ul>
      <p>${t('Estimated profit')}: ${money(x.profit_range[0])} to ${money(x.profit_range[1])} · ${x.days} ${t('days')}</p><button class="sec" data-c="${esc(x.crop)}" data-a="${esc(f.elements.acres.value)}">${t('Details')}</button></div>`).join('') + `<p class="note">${esc(r.note)}</p>` : '<p>No strong match for these conditions.</p>';
    $('#out').querySelectorAll('[data-c]').forEach(b => b.onclick = () => { g.elements.crop.value = b.dataset.c; g.elements.acres.value = b.dataset.a; g.dispatchEvent(new Event('submit', {cancelable: true})); });
  });
  on(g, async () => {
    const e = await api('/economics', {body: fd(g)}), u = e.unit, row = (a, b) => `<tr><th>${a}</th><td>${b}</td></tr>`;
    $('#out2').innerHTML = `<table>${row('Cultivation cost', money(e.cost))}${row('Expected yield', e.yield_range[0] + ' – ' + e.yield_range[1] + ' ' + esc(u))}${row('Revenue range', money(e.revenue_range[0]) + ' – ' + money(e.revenue_range[1]))}
      ${row('Expected profit range', money(e.profit_expected_range[0]) + ' to ' + money(e.profit_expected_range[1]))}${row('Cautious case (low yield, price −15%)', money(e.profit_pessimistic))}${row('Optimistic case (high yield, price +15%)', money(e.profit_optimistic))}
      ${row('Break-even price', money(e.break_even_price) + ' per ' + esc(u))}${row('Crop duration', e.days + ' ' + t('days'))}</table><p class="note">${esc(e.note)}</p>`;
  });
}

function draw(r) {
  const W = r.width, L = r.length, sc = Math.min(640 / W, 440 / L), w = W * sc, h = L * sc, gap = Math.max(r.partner_spacing[0] * sc, 1);
  let s = `<svg class="layout" viewBox="0 0 ${w + 2} ${h + 2}" role="img" aria-label="Top-down planting layout"><rect x="1" y="1" width="${w}" height="${h}" fill="#f4f1e2" stroke="#2f6f3d" stroke-width="2"/>`;
  r.partner_rows.forEach(o => { const y = 1 + o.y * sc; s += `<line x1="${1 + o.x0 * sc}" x2="${1 + (o.x0 + (o.n - 1) * o.step) * sc}" y1="${y}" y2="${y}" stroke="#e3a72f" stroke-width="${Math.max(1.5, Math.min(4, gap * .6))}" stroke-linecap="round" stroke-dasharray="0.1 ${Math.max(gap - 0.1, 1)}"/>`; });
  const rad = Math.max(3, Math.min(r.main_spacing[0], r.main_spacing[1]) * sc * .35);
  r.main_points.forEach(p => { s += `<circle cx="${1 + p[0] * sc}" cy="${1 + p[1] * sc}" r="${rad}" fill="#2f6f3d"/>`; });
  return s + '</svg>';
}
function intercrop() {
  V().innerHTML = `<h2>${t('Intercrop')}</h2><form id="f" class="grid">${sel('main', 'Main crop', opts(Object.keys(META.intercrop)))}<label>${t('Intercrop')}<select name="partner"></select></label>${inp('width', 'Field width (m)', 'number', 'value="40" min="1" step="any"')}${inp('length', 'Field length (m)', 'number', 'value="30" min="1" step="any"')}<button>${t('Generate layout')}</button></form><div id="out"></div>`;
  const f = $('#f'), fill = () => { f.elements.partner.innerHTML = opts(META.intercrop[f.elements.main.value]); };
  f.elements.main.onchange = fill; fill();
  on(f, async () => {
    const r = await api('/intercrop', {body: fd(f)});
    $('#out').innerHTML = draw(r) + `<p class="note">● ${esc(r.main)} (${r.main_spacing[0]} × ${r.main_spacing[1]} m) &nbsp; <span style="color:#e3a72f">●</span> ${esc(r.partner)} (${r.partner_spacing[0]} × ${r.partner_spacing[1]} m)</p>
    <div class="stats"><div><b>${r.main_count}</b>${esc(r.main)} plants</div><div><b>${r.partner_count}</b>${esc(r.partner)} plants</div><div><b>${money(r.main_plant_cost + r.partner_plant_cost)}</b>planting material (estimate)</div></div><p class="note">${esc(r.note)}</p>`;
  });
}

function protect() {
  V().innerHTML = `<h2>${t('Protect')}</h2><form id="f" class="grid">${sel('crop', 'Crop', opts(Object.keys(META.crops), '', cropName))}<label>${t('Leaf photo')}<input type="file" name="image" accept="image/*" required></label>
  <fieldset><legend>${t('Symptoms you see')}</legend>${META.symptoms.map(s => `<label class="chk"><input type="checkbox" value="${esc(s)}"> ${esc(s)}</label>`).join('')}</fieldset><button>${t('Analyze')}</button></form><img id="pv" class="pv" alt="Leaf preview" hidden><div id="out"></div>`;
  const f = $('#f');
  f.elements.image.onchange = e => { const fl = e.target.files[0]; if (fl) { $('#pv').src = URL.createObjectURL(fl); $('#pv').hidden = false; } };
  on(f, async () => {
    const b = new FormData(); b.append('image', f.elements.image.files[0]); b.append('crop', f.elements.crop.value);
    b.append('symptoms', [...f.querySelectorAll('input[type=checkbox]:checked')].map(c => c.value).join(','));
    const r = await api('/detect', {body: b});
    $('#out').innerHTML = `<p><span class="badge ${r.status === 'healthy' ? 'ok' : ''}">${r.status === 'healthy' ? 'Looks healthy' : 'Possible issue'}</span> Affected leaf area ≈ ${r.affected_pct}% · severity: <b>${esc(r.severity)}</b></p><p>${esc(r.message)}</p>` +
      r.matches.map(m => `<div class="card2"><h4>${esc(m.name)} <small>(indicative match ${m.match_pct}%)</small></h4><p><b>Treatment:</b> ${esc(m.treatment)}</p><p><b>Prevention:</b> ${esc(m.prevention)}</p></div>`).join('') + `<p class="note">${esc(r.disclaimer)}</p>`;
  });
}

async function market() {
  V().innerHTML = `<h2>${t('Market')}</h2><form id="f" class="grid">${sel('crop', 'Crop', opts(Object.keys(META.crops), '', cropName))}</form><div id="out"></div>`;
  const f = $('#f'), MN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const load = async () => {
    try {
      const r = await api('/market?crop=' + encodeURIComponent(f.elements.crop.value)), mx = Math.max(...r.monthly);
      const bars = r.monthly.map((p, i) => { const h = 100 * p / mx; return `<rect x="${12 + i * 28}" y="${115 - h}" width="22" height="${h}" fill="${r.best_months.includes(i + 1) ? '#e3a72f' : '#2f6f3d'}"/><text x="${23 + i * 28}" y="132" font-size="9" text-anchor="middle">${MN[i]}</text>`; }).join('');
      $('#out').innerHTML = `<svg class="bars" viewBox="0 0 350 140" role="img" aria-label="Indicative monthly price pattern">${bars}</svg><p>Base price ${money(r.base_price)} per ${esc(r.unit)}. Best indicative selling months: <b>${r.best_months.map(m => MN[m - 1]).join(', ')}</b></p><p class="note">${esc(r.note)}</p>`;
    } catch (x) { toast(x.message, 1); }
  };
  f.elements.crop.onchange = load; load();
}

function shop() {
  const T = [['browse', 'Browse'], ...(role() === 'farmer' ? [['mine', 'My listings']] : []), ...(USER ? [['orders', 'Orders'], ['bulk', 'Bulk requests']] : [])];
  if (!T.some(x => x[0] === SUB)) SUB = 'browse';
  V().innerHTML = `<h2>${t('Marketplace')}</h2><div class="sub">${T.map(([k, l]) => `<button class="sec ${SUB === k ? 'on' : ''}" data-s="${k}">${t(l)}</button>`).join('')}</div><div id="pane"></div>`;
  V().querySelectorAll('[data-s]').forEach(b => b.onclick = () => { SUB = b.dataset.s; shop(); });
  ({browse, mine, orders, bulk})[SUB]().catch(x => toast(x.message, 1));
}
async function browse() {
  const P = $('#pane'), buy = ['consumer', 'bulk_buyer'].includes(role());
  P.innerHTML = `<form id="f" class="grid">${sel('crop', 'Crop', '<option value="">All</option>' + opts(Object.keys(META.crops)))}${sel('district', 'District', '<option value="">All</option>' + opts(META.districts))}<button>${t('Search')}</button></form>${USER ? '' : '<p class="note">Login as a consumer or bulk buyer to order.</p>'}<div id="list"></div>`;
  const load = async () => {
    const L = await api('/listings?' + new URLSearchParams(fd($('#f'))));
    $('#list').innerHTML = L.length ? L.map(l => `<div class="card2"><h4>${esc(l.crop)} · ${money(l.price_kg)}/kg</h4><p>${l.qty_kg} kg · ${esc(l.district)} · ${esc(l.farmer)}</p><p>${esc(l.note)}</p>${buy ? `<form class="ord" data-id="${l.id}"><input type="number" name="qty_kg" min="0.1" step="any" placeholder="kg" required><button>${t('Order')}</button></form>` : ''}</div>`).join('') : '<p>No listings found.</p>';
    $('#list').querySelectorAll('.ord').forEach(o => on(o, async () => { const r = await api('/orders', {body: {listing_id: +o.dataset.id, qty_kg: o.elements.qty_kg.value}}); toast('Order placed: ' + money(r.total)); load(); }));
  };
  on($('#f'), load); await load();
}
async function mine() {
  const P = $('#pane');
  P.innerHTML = `<form id="f" class="grid">${sel('crop', 'Crop', opts(Object.keys(META.crops)))}${inp('qty_kg', 'Quantity (kg)', 'number', 'min="1" step="any" required')}${inp('price_kg', 'Price (₹ per kg)', 'number', 'min="0.1" step="any" required')}${sel('district', 'District', opts(META.districts, USER.district))}${inp('note', 'Note')}<button>Add listing</button></form><div id="list"></div>`;
  const load = async () => { const L = await api('/listings?mine=1'); $('#list').innerHTML = L.map(l => `<div class="card2"><h4>${esc(l.crop)} · ${money(l.price_kg)}/kg</h4><p>${l.qty_kg} kg left · ${esc(l.district)} · <b>${esc(l.status)}</b></p></div>`).join('') || '<p>No listings yet.</p>'; };
  on($('#f'), async () => { await api('/listings', {body: fd($('#f'))}); toast('Listing added'); $('#f').reset(); load(); }); await load();
}
async function orders() {
  const o = await api('/orders'), P = $('#pane');
  const acts = (x, farmer) => { const m = farmer ? {placed: ['accepted', 'cancelled'], accepted: ['delivered', 'cancelled']} : {placed: ['cancelled']}; return (m[x.status] || []).map(s => `<button class="sec" data-o="${x.id}" data-st="${s}">${s}</button>`).join(' '); };
  const row = (x, farmer) => `<div class="card2${farmer && x.status === 'placed' ? ' hl' : ''}">${farmer && x.status === 'placed' ? '<span class="newtag">NEW</span>' : ''}<h4>#${x.id} ${esc(x.crop)} · ${x.qty_kg} kg · ${money(x.total)}</h4><p>${esc(farmer ? x.buyer : x.farmer)} · <b>${esc(x.status)}</b></p>${acts(x, farmer)}</div>`;
  P.innerHTML = (o.placed.length ? '<h3>My orders</h3>' + o.placed.map(x => row(x, false)).join('') : '') + (o.incoming.length ? '<h3>Incoming orders</h3>' + o.incoming.map(x => row(x, true)).join('') : '') || '<p>No orders yet.</p>';
  P.querySelectorAll('[data-o]').forEach(b => b.onclick = async () => { try { await api('/orders/' + b.dataset.o + '/status', {body: {status: b.dataset.st}}); orders(); } catch (x) { toast(x.message, 1); } });
}
async function bulk() {
  const P = $('#pane'), R = await api('/requests'), r = role();
  const hotq = q => (r === 'farmer' && q.status === 'open') || (r === 'bulk_buyer' && q.buyer_id === USER.id && q.status === 'open' && q.offers > 0);
  P.innerHTML = (r === 'bulk_buyer' ? `<form id="f" class="grid">${sel('crop', 'Crop', opts(Object.keys(META.crops)))}${inp('qty_kg', 'Quantity (kg)', 'number', 'min="1" step="any" required')}${inp('target_kg', 'Target price (₹ per kg)', 'number', 'min="0.1" step="any" required')}${sel('district', 'District', '<option value="">Any</option>' + opts(META.districts))}<button>Post request</button></form>` : '') +
    (R.map(q => `<div class="card2${hotq(q) ? ' hl' : ''}">${hotq(q) ? '<span class="newtag">' + (r === 'farmer' ? 'NEW' : 'OFFERS') + '</span>' : ''}<h4>#${q.id} ${esc(q.crop)} · ${q.qty_kg} kg · target ${money(q.target_kg)}/kg</h4><p>${esc(q.buyer)} · ${esc(q.district || 'Any district')} · <b>${esc(q.status)}</b> · ${q.offers} offer(s)</p>
    ${r === 'farmer' && q.status === 'open' ? `<form class="inl" data-r="${q.id}"><input name="price_kg" type="number" step="any" min="0.1" placeholder="₹/kg" required><input name="qty_kg" type="number" step="any" min="1" placeholder="kg" required><button>Send offer</button></form>` : ''}
    ${r === 'bulk_buyer' && q.buyer_id === USER.id ? `<button class="sec" data-v="${q.id}">View offers</button><div id="of${q.id}"></div>` : ''}</div>`).join('') || '<p>No open requests.</p>');
  if ($('#f')) on($('#f'), async () => { await api('/requests', {body: fd($('#f'))}); toast('Request posted'); bulk(); });
  P.querySelectorAll('.inl').forEach(f => on(f, async () => { await api('/offers', {body: {request_id: +f.dataset.r, price_kg: f.elements.price_kg.value, qty_kg: f.elements.qty_kg.value}}); toast('Offer sent'); bulk(); }));
  P.querySelectorAll('[data-v]').forEach(b => b.onclick = async () => {
    try {
      const O = await api('/requests/' + b.dataset.v + '/offers');
      $('#of' + b.dataset.v).innerHTML = O.map(o => `<p class="${o.status === 'pending' ? 'hlp' : ''}">${esc(o.farmer)}: ${money(o.price_kg)}/kg for ${o.qty_kg} kg · ${esc(o.status)} ${o.status === 'pending' ? `<button data-a="${o.id}">Accept</button>` : ''}</p>`).join('') || '<p>No offers yet.</p>';
      $('#of' + b.dataset.v).querySelectorAll('[data-a]').forEach(a => a.onclick = async () => { try { const d = await api('/offers/' + a.dataset.a + '/accept', {method: 'POST'}); toast('Deal confirmed: ' + money(d.deal.total)); bulk(); } catch (x) { toast(x.message, 1); } });
    } catch (x) { toast(x.message, 1); }
  });
}

async function services() {
  V().innerHTML = `<h2>${t('Services')}</h2><form id="f" class="grid">${sel('district', 'District', '<option value="">All</option>' + opts(META.districts, DIST))}<button>${t('Search')}</button></form><div id="list"></div><div id="mine"></div>`;
  const load = async () => {
    DIST = $('#f').elements.district.value;
    const L = await api('/services' + (DIST ? '?district=' + encodeURIComponent(DIST) : ''));
    $('#list').innerHTML = L.map(s => `<div class="card2"><h4>${esc(s.kind)}</h4><p>${esc(s.provider)} · ${esc(s.district)} · ${esc(s.phone)}</p><p>${esc(s.note)}</p>${role() === 'farmer' ? `<form class="inl" data-id="${s.id}"><input name="note" placeholder="What help do you need?"><button>Request</button></form>` : ''}</div>`).join('') || '<p>No services found.</p>';
    $('#list').querySelectorAll('.inl').forEach(f => on(f, async () => { await api('/service-requests', {body: {service_id: +f.dataset.id, note: f.elements.note.value}}); toast('Request sent'); loadMine(); }));
  };
  const loadMine = async () => {
    if (!USER) { $('#mine').innerHTML = '<p class="note">Login to request or offer services.</p>'; return; }
    let h = '';
    if (role() === 'service_provider') h += `<h3>Add service</h3><form id="s" class="grid">${inp('kind', 'Service (e.g. soil test, pump repair)', 'text', 'required')}${inp('note', 'Details')}${sel('district', 'District', opts(META.districts, USER.district))}<button>Add</button></form>`;
    if (['farmer', 'service_provider'].includes(role())) {
      const R = await api('/service-requests');
      h += '<h3>Requests</h3>' + (R.map(r => `<div class="card2${role() === 'service_provider' && r.status === 'open' ? ' hl' : ''}">${role() === 'service_provider' && r.status === 'open' ? '<span class="newtag">NEW</span>' : ''}<h4>${esc(r.kind)} · <b>${esc(r.status)}</b></h4><p>${esc(r.farmer)} ${esc(r.phone)} — ${esc(r.note)}</p>${role() === 'service_provider' ? ['accepted', 'done', 'declined'].map(s => `<button class="sec" data-r="${r.id}" data-st="${s}">${s}</button>`).join(' ') : ''}</div>`).join('') || '<p>None yet.</p>');
    }
    $('#mine').innerHTML = h;
    if ($('#s')) on($('#s'), async () => { await api('/services', {body: fd($('#s'))}); toast('Service added'); load(); loadMine(); });
    $('#mine').querySelectorAll('[data-r]').forEach(b => b.onclick = async () => { try { await api('/service-requests/' + b.dataset.r + '/status', {body: {status: b.dataset.st}}); loadMine(); } catch (x) { toast(x.message, 1); } });
  };
  on($('#f'), load); await load(); await loadMine();
}

async function account() {
  if (USER) {
    let h = `<h2>${t('Account')}</h2><div class="card2"><h4>${esc(USER.name)}</h4><p>${esc(USER.email)} · ${t(USER.role)} · ${esc(USER.district || '')}</p><button id="out">${t('Logout')}</button></div>`;
    if (role() === 'farmer') { const S = await api('/scans'); h += '<h3>Recent leaf scans</h3>' + (S.map(s => `<div class="card2"><b>${esc(s.crop)}</b> — ${esc(s.summary)} <span class="note">${esc(s.created)}</span></div>`).join('') || '<p>No scans yet.</p>'); }
    V().innerHTML = h; $('#out').onclick = () => logout(); return;
  }
  const guest = !!sessionStorage.getItem('guest');
  V().innerHTML = `<section class="hero"><h1>AgriShield AI</h1><p>${t('From Soil to Sale — one intelligent platform for farmers')}</p></section>
  <h2>${t('Login')}</h2><form id="l" class="grid">${inp('email', 'Email', 'email', 'required')}${inp('password', 'Password', 'password', 'required')}<button>${t('Login')}</button></form>
  <div class="sub"><button class="sec" id="showreg">New here? ${t('Register')}</button>${guest ? '' : '<button class="sec" id="guest">Continue as guest →</button>'}</div>
  <form id="r" class="grid" hidden>${inp('name', 'Name', 'text', 'required')}${inp('email', 'Email', 'email', 'required')}${inp('password', 'Password', 'password', 'minlength="6" required')}${inp('phone', 'Phone')}${sel('district', 'District', '<option value="">—</option>' + opts(META.districts))}${sel('role', 'Role', ['farmer', 'consumer', 'bulk_buyer', 'service_provider'].map(x => `<option value="${x}">${t(x)}</option>`).join(''))}<button>${t('Register')}</button></form>
  <h3>Quick demo login</h3><div class="sub">${[['farmer@demo.com', 'Farmer'], ['consumer@demo.com', 'Consumer'], ['buyer@demo.com', 'Bulk Buyer'], ['expert@demo.com', 'Service Provider']].map(([e, l]) => `<button class="sec" data-demo="${e}">${l}</button>`).join('')}</div>
  <p class="note">Guests can explore crop planning, intercrop layouts, leaf screening, market trends and browse listings. Log in to order, sell or request services.</p>`;
  const done = r => { setUser(r); toast('Welcome ' + r.user.name); nav(); go('home'); };
  V().querySelectorAll('[data-demo]').forEach(b => b.onclick = async () => { try { done(await api('/login', {body: {email: b.dataset.demo, password: 'demo123'}})); } catch (x) { toast(x.message, 1); } });
  on($('#l'), async () => done(await api('/login', {body: fd($('#l'))})));
  on($('#r'), async () => done(await api('/register', {body: fd($('#r'))})));
  $('#showreg').onclick = () => { $('#r').hidden = !$('#r').hidden; };
  if ($('#guest')) $('#guest').onclick = () => { sessionStorage.setItem('guest', '1'); nav(); go('home'); };
}

(async () => {
  $('#logout').onclick = () => logout();
  setInterval(() => { if (USER) refreshBadges(); }, 20000);
  $('#lang').onclick = () => { LANG = LANG === 'en' ? 'ta' : 'en'; localStorage.setItem('lang', LANG); go(TAB); };
  try { META = await fetch('/api/meta').then(r => r.json()); go('home'); } catch (e) { V().innerHTML = '<p>Could not reach the server. Start it with: uvicorn app.main:app</p>'; }
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
})();
