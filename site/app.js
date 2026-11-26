/* PontoAtivo – Mapa esportivo de Brasília/DF
 * Base de locais: data/locais.js (window.PA_LOCAIS), gerada a partir de fontes oficiais.
 * Cada registro traz fonte, link e data. Acessibilidade só é "verificada" com visita/fonte documentada.
 */

// ---------- Configuração dos tipos ----------
const TYPES = {
  cop:       { label: "Centro Olímpico e Paralímpico", short: "COP", color: "#2f78c8", ico: "🏅", featured: true },
  para:      { label: "Paradesporto",                 short: "Paradesporto", color: "#1f5fb0", ico: "♿", featured: true },
  estadio:   { label: "Estádio, ginásio ou complexo", short: "Complexo", color: "#172649", ico: "🏟️", featured: true },
  clube:     { label: "Clube / academia privada",     short: "Clube", color: "#8b5cf6", ico: "🏊", featured: true },
  parque:    { label: "Parque",                       short: "Parque", color: "#0b6e4f", ico: "🌳", featured: true },
  praca:     { label: "Praça",                        short: "Praça", color: "#6d8f3a", ico: "🌿" },
  pec:       { label: "PEC – Ponto de Encontro Comunitário", short: "PEC", color: "#34a853", ico: "💪" },
  ginastica: { label: "Aparelhos de ginástica",       short: "Ginástica", color: "#0f9d8a", ico: "🤸" },
  quadra:    { label: "Quadra poliesportiva",         short: "Quadra", color: "#f39200", ico: "🏀" },
  areia:     { label: "Quadra de areia",              short: "Areia", color: "#d4a000", ico: "🏐" },
  tenis:     { label: "Quadra de tênis",              short: "Tênis", color: "#c0392b", ico: "🎾" },
  campo:     { label: "Campo de futebol",             short: "Campo", color: "#5a9e2f", ico: "⚽" },
  skate:     { label: "Pista de skate",               short: "Skate", color: "#8e44ad", ico: "🛹" },
  parquinho: { label: "Parquinho (parque infantil)",  short: "Parquinho", color: "#e8590c", ico: "🛝" },
};
const ORDER = Object.keys(TYPES);
const ACC_LABELS = { rota: "Rota sem degraus", banheiro: "Banheiro acessível", tatil: "Piso tátil", vaga: "Vaga PcD", adaptado: "Esporte adaptado / PcD" };
const ACC_KEYS_EXT = {
  step_free_route: "Rota sem degraus",
  entry_barrier_free: "Entrada acessível",
  circulation: "Circulação livre",
  accessible_toilet: "Banheiro acessível",
  accessible_parking: "Vaga PcD",
  tactile_paving: "Piso tátil",
  signage: "Sinalização",
  adapted_equipment: "Equipamento adaptado",
  human_support: "Apoio humano",
};
const STATUS_LABEL = { ok: "verificado", info: "informado pela fonte, não verificado", unk: "desconhecido" };
const EVIDENCE_LEVELS = {
  oficial: { label: "Oficial", badge: "ev-oficial" },
  organizacao: { label: "Declarado pela organização", badge: "ev-organizacao" },
  colaborativo: { label: "Colaborativo", badge: "ev-colaborativo" },
  campo: { label: "Verificado em campo", badge: "ev-campo" },
  divergente: { label: "Divergente", badge: "ev-divergente" },
  desconhecido: { label: "Não informado", badge: "ev-desconhecido" },
};
const OWNERSHIP_LABELS = {
  public: { label: "Público", cls: "ownership-public" },
  social: { label: "Organização social", cls: "ownership-social" },
  private: { label: "Privado", cls: "ownership-private" },
};

const MODALIDADES = [
  { n: "Caminhada", d: "Parques e pistas por todo o DF", i: "🚶", t: "pec" },
  { n: "Exercícios no PEC", d: "403 pontos cadastrados", i: "💪", t: "pec" },
  { n: "Alongamento", d: "Para todas as idades", i: "🧘", t: "pec" },
  { n: "Corrida", d: "Parque da Cidade e parques", i: "🏃", t: "conv" },
  { n: "Futebol de campo", d: "Campos públicos e society", i: "⚽", t: "conv" },
  { n: "Futsal", d: "Quadras poliesportivas", i: "🥅", t: "conv" },
  { n: "Vôlei", d: "Quadras e areia", i: "🏐", t: "conv" },
  { n: "Basquete", d: "Quadras poliesportivas", i: "🏀", t: "conv" },
  { n: "Futevôlei e beach tennis", d: "Quadras de areia", i: "🏖️", t: "conv" },
  { n: "Skate e patins", d: "Pistas de skate", i: "🛹", t: "conv" },
  { n: "Natação", d: "Centro Olímpico da UnB", i: "🏊", t: "conv" },
  { n: "Bocha paralímpica", d: "CETEFE e COPs", i: "🎯", t: "adap" },
  { n: "Goalball", d: "Para pessoas com deficiência visual", i: "🔔", t: "adap" },
  { n: "Atletismo paralímpico", d: "CETEFE e COPs", i: "🏅", t: "adap" },
  { n: "Tênis em cadeira de rodas", d: "Festivais nos COPs", i: "🎾", t: "adap" },
  { n: "Basquete em cadeira de rodas", d: "Equipes e federação no DF", i: "♿", t: "adap" },
  { n: "Modalidades nos COPs", d: "12 centros gratuitos", i: "🏟️", t: "adap" },
];
const TAG = { conv: ["Convencional", "tag-conv", "#e3f4e6"], adap: ["Adaptada / paralímpica", "tag-adap", "#e2eefb"], pec: ["PEC / ar livre", "tag-pec", "#fff1d0"] };

// ---------- Utilidades ----------
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const norm = (s) => (s || "").normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (n) => n.toLocaleString("pt-BR");
function km(a, b) {
  const R = 6371, toR = (x) => (x * Math.PI) / 180;
  const dLat = toR(b[0] - a[0]), dLon = toR(b[1] - a[1]);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(toR(a[0])) * Math.cos(toR(b[0])) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

// ---------- Cabeçalho, menu, barra de acessibilidade ----------
const menuBtn = $(".menu-toggle");
menuBtn.addEventListener("click", () => {
  const open = $("#menu").classList.toggle("open");
  menuBtn.setAttribute("aria-expanded", open);
});
$$("#menu a").forEach((a) => a.addEventListener("click", () => { $("#menu").classList.remove("open"); menuBtn.setAttribute("aria-expanded", false); }));

// Cabeçalho: com zoom ou letra maior, logo, menu e conta podem não caber lado a lado.
// Mede o espaço real e, se não couber, os links descem para uma segunda linha (classe "duas-linhas").
const siteHeader = $(".site-header");
const navMenu = $("#menu");
function ajustarCabecalho() {
  siteHeader.classList.remove("duas-linhas");
  if (matchMedia("(max-width: 1220px)").matches) return; // abaixo disso o CSS já usa o ☰
  const marca = $(".brand").getBoundingClientRect();
  const links = [...navMenu.children].filter((el) => el.getClientRects().length);
  const conta = [...siteHeader.querySelectorAll(".account-login, .account-menu")]
    .find((el) => !el.hidden && el.getClientRects().length);
  const primeiro = links[0] && links[0].getBoundingClientRect();
  const ultimo = links.length && links[links.length - 1].getBoundingClientRect();
  const folga = 12;
  const naoCabe = (primeiro && primeiro.left < marca.right + folga)
    || (ultimo && conta && ultimo.right > conta.getBoundingClientRect().left - folga);
  if (naoCabe) siteHeader.classList.add("duas-linhas");
}
let ajusteAgendado = 0;
const agendarAjuste = () => { clearTimeout(ajusteAgendado); ajusteAgendado = setTimeout(ajustarCabecalho, 30); };
if ("ResizeObserver" in window) {
  const observador = new ResizeObserver(agendarAjuste);
  observador.observe($(".header-inner"));
  siteHeader.querySelectorAll(".account-login, .account-menu").forEach((el) => observador.observe(el));
}
new MutationObserver(agendarAjuste).observe(siteHeader, { attributes: true, subtree: true, attributeFilter: ["hidden"] });
window.addEventListener("resize", agendarAjuste);
if (document.fonts && document.fonts.ready) document.fonts.ready.then(agendarAjuste);

let fontPx = parseInt(localStorage.getItem("pa-font") || "18", 10);
const applyFont = () => { document.documentElement.style.setProperty("--fs", fontPx + "px"); agendarAjuste(); };
applyFont();
const toggles = { contrast: "high-contrast", motion: "no-motion" };
// Painel flutuante de acessibilidade: abre no botão flutuante, fecha com Esc ou clicando fora.
const a11yToggle = $("#a11y-toggle");
const a11yPanel = $("#a11y-panel");
const openA11y = (open) => { a11yPanel.hidden = !open; a11yToggle.setAttribute("aria-expanded", String(open)); };
a11yToggle.addEventListener("click", () => openA11y(a11yPanel.hidden));
document.addEventListener("click", (e) => { if (!e.target.closest(".a11y-float")) openA11y(false); });
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !a11yPanel.hidden) { openA11y(false); a11yToggle.focus(); }
});
for (const [k, cls] of Object.entries(toggles)) {
  if (localStorage.getItem("pa-" + k) === "1") { document.body.classList.add(cls); $(`[data-a11y="${k}"]`).setAttribute("aria-pressed", "true"); }
}
$$("[data-a11y]").forEach((b) => b.addEventListener("click", () => {
  const k = b.dataset.a11y;
  if (k === "font-up") fontPx = Math.min(24, fontPx + 2);
  else if (k === "font-down") fontPx = Math.max(16, fontPx - 2);
  else {
    const on = document.body.classList.toggle(toggles[k]);
    b.setAttribute("aria-pressed", on);
    localStorage.setItem("pa-" + k, on ? "1" : "0");
    return;
  }
  localStorage.setItem("pa-font", fontPx);
  applyFont();
}));

// ---------- Palavra rotativa ----------
const words = ["jogar", "caminhar", "treinar no PEC", "jogar bola", "andar de skate", "correr", "jogar vôlei"];
let wi = 0;
const wordEl = $("#rotating-word");
// As frases ocupam a mesma célula. A mais alta define o espaço da animação.
for (const phrase of words) {
  const measure = document.createElement("span");
  measure.className = "rotator-measure";
  measure.setAttribute("aria-hidden", "true");
  measure.textContent = phrase;
  wordEl.parentElement.append(measure);
}
setInterval(() => {
  if (document.body.classList.contains("no-motion") || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  wordEl.classList.add("out");
  setTimeout(() => { wi = (wi + 1) % words.length; wordEl.textContent = words[wi]; wordEl.classList.remove("out"); }, 300);
}, 2400);

// ---------- Modalidades ----------
function modCard(m, hidden) {
  const [label, cls, bg] = TAG[m.t];
  return `<article class="mod-card"${hidden ? ' aria-hidden="true"' : ""}>
    <h3>${esc(m.n)}</h3><p>${esc(m.d)}</p><span class="tag ${cls}">${label}</span></article>`;
}
const half = Math.ceil(MODALIDADES.length / 2);
[[$("#mq1"), MODALIDADES.slice(0, half)], [$("#mq2"), MODALIDADES.slice(half)]].forEach(([el, list]) => {
  el.innerHTML = list.map((m) => modCard(m, false)).join("") + list.map((m) => modCard(m, true)).join("");
});

// ---------- Dados ----------
const LOCAIS = (window.PA_LOCAIS || []).map((r) => ({
  ...r,
  _s: norm([r.n, r.end, r.ra, (r.mods || []).join(" "), TYPES[r.t]?.label].join(" ")),
}));
const counts = LOCAIS.reduce((acc, r) => ((acc[r.t] = (acc[r.t] || 0) + 1), acc), {});
const RAS = [...new Set(LOCAIS.map((r) => r.ra).filter(Boolean))].sort((a, b) => a.localeCompare(b, "pt-BR"));
const pendentes = LOCAIS.filter((r) => r.lat == null).length;

$$("[data-count]").forEach((el) => {
  const k = el.dataset.count;
  const v = k === "quadras" ? (counts.quadra || 0) + (counts.areia || 0) + (counts.tenis || 0) : counts[k] || 0;
  if (v) el.textContent = fmt(v);
});
$("#mapa-sub").textContent = `${fmt(LOCAIS.length)} locais em ${RAS.length} regiões administrativas do DF. Filtre por tipo, região e condições; o mapa e a lista mostram os mesmos resultados.`;
$("#gap-pend").textContent = `${pendentes} parques da lista do Ibram ainda estão sem localização exata e aparecem só na lista.`;

// Cobertura na seção Fontes: tipos agrupados por tema, com o mesmo pino do mapa.
// Cada tipo abre o mapa já filtrado por ele.
const COBERTURA = [
  { titulo: "Esporte organizado", desc: "Centros com aulas, paradesporto e grandes equipamentos", tipos: ["cop", "para", "estadio", "clube"],
    nota: "Os Centros Olímpicos são gratuitos e têm vagas para pessoas com deficiência." },
  { titulo: "Exercício ao ar livre", desc: "PECs, aparelhos, parques e praças para treinar e caminhar", tipos: ["pec", "ginastica", "parque", "praca"] },
  { titulo: "Quadras, campos e pistas", desc: "Espaços para jogar em grupo ou andar de skate", tipos: ["campo", "quadra", "areia", "tenis", "skate"] },
  { titulo: "Para as crianças", desc: "Parques infantis do cadastro oficial", tipos: ["parquinho"],
    nota: "Levantamento oficial de 2015 e 2017: os brinquedos e o estado de cada parquinho podem ter mudado. " +
      "Confirme no local e, se puder, use “Colaborar” no mapa para atualizar." },
];
const totalTipos = ORDER.filter((t) => counts[t]).length;
const totalFontes = document.querySelectorAll("#fontes .source").length;
$("#stats").innerHTML = `
  <div class="cov-resumo">
    <div><strong>${fmt(LOCAIS.length)}</strong><span>locais no mapa</span></div>
    <div><strong>${RAS.length}</strong><span>regiões administrativas</span></div>
    <div><strong>${totalTipos}</strong><span>tipos de espaço</span></div>
    <div><strong>${totalFontes}</strong><span>grupos de fontes</span></div>
  </div>
  <div class="cov-grupos">${COBERTURA.map((g) => {
    const tipos = g.tipos.filter((t) => counts[t]);
    if (!tipos.length) return "";
    const soma = tipos.reduce((n, t) => n + counts[t], 0);
    const maior = Math.max(...tipos.map((t) => counts[t]));
    return `<section class="cov-grupo" aria-label="${esc(g.titulo)}">
      <header><h3>${esc(g.titulo)}</h3><span class="cov-soma">${fmt(soma)}</span></header>
      <p>${esc(g.desc)}</p>
      <ul>${tipos.map((t) => `<li><button type="button" class="cov-tipo" data-cov-tipo="${t}" title="Ver ${esc(TYPES[t].label)} no mapa">
        <span class="cov-pino" style="--pin:${TYPES[t].color}" aria-hidden="true"><span></span></span>
        <span class="cov-nome">${esc(TYPES[t].label)}</span>
        <strong>${fmt(counts[t])}</strong>
        <span class="cov-barra" aria-hidden="true"><i style="width:${Math.max(4, Math.round((counts[t] / maior) * 100))}%;background:${TYPES[t].color}"></i></span>
      </button></li>`).join("")}</ul>
      ${g.nota ? `<p class="cov-nota">${esc(g.nota)}</p>` : ""}
    </section>`;
  }).join("")}</div>
  <p class="cov-dica">Toque em um tipo para ver só esses locais no mapa.</p>`;
$("#stats").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-cov-tipo]");
  if (!btn) return;
  document.querySelectorAll("#f-tipos input").forEach((i) => (i.checked = i.value === btn.dataset.covTipo));
  update();
  window.PontoAtivoTelas.ir("mapa");
});

// ---------- Filtros ----------
$("#f-tipos").innerHTML = ORDER.filter((t) => counts[t]).map((t) =>
  `<label><input type="checkbox" name="tipo" value="${t}" checked /> <i class="sw" style="background:${TYPES[t].color}"></i> ${TYPES[t].label} <small>(${fmt(counts[t])})</small></label>`).join("");
RAS.forEach((ra) => $("#f-ra").insertAdjacentHTML("beforeend", `<option>${esc(ra)}</option>`));
$("#f-all").addEventListener("click", () => { $$('#f-tipos input').forEach((i) => (i.checked = true)); update(); });
$("#f-none").addEventListener("click", () => { $$('#f-tipos input').forEach((i) => (i.checked = false)); update(); });

// ---------- Barra de filtros ----------
// "Tipo de espaço" e "Mais filtros" abrem painéis; um painel aberto fecha o outro,
// e clicar fora ou apertar Esc fecha os dois.
$$(".fb-pop").forEach((d) => d.addEventListener("toggle", () => {
  if (d.open) $$(".fb-pop[open]").forEach((o) => { if (o !== d) o.open = false; });
}));
document.addEventListener("click", (e) => {
  $$(".fb-pop[open]").forEach((d) => { if (!d.contains(e.target)) d.open = false; });
});
document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  $$(".fb-pop[open]").forEach((d) => { d.open = false; d.querySelector("summary").focus(); });
});

// Resumo do que está escolhido em cada painel, mostrado no próprio botão.
function syncFilterSummary() {
  const boxes = $$("#f-tipos input");
  const on = boxes.filter((i) => i.checked);
  const name = (i) => i.closest("label").textContent.replace(/\(\s*[\d.]+\s*\)\s*$/, "").trim();
  $("#f-tipos-resumo").textContent = on.length === boxes.length ? "Todos os tipos"
    : on.length === 0 ? "Nenhum tipo" : on.length === 1 ? name(on[0]) : `${on.length} tipos`;
  const f = getFilters();
  const active = $$("#f-origem input").filter((i) => !i.checked).length + (f.evidencia ? 1 : 0) +
    [f.gratis, f.luz, f.bom, f.pcd].filter(Boolean).length;
  $("#f-mais-resumo").textContent = active
    ? `${active} ${active === 1 ? "filtro ativo" : "filtros ativos"}` : "Origem, evidência e condições";
}

function getFilters() {
  return {
    tipos: new Set($$('#f-tipos input:checked').map((i) => i.value)),
    origens: new Set($$('#f-origem input:checked').map((i) => i.value)),
    evidencia: $("#f-evidencia") ? $("#f-evidencia").value : "",
    ra: $("#f-ra").value,
    q: norm($("#f-q").value.trim()),
    gratis: $("#f-gratis").checked,
    luz: $("#f-luz").checked,
    bom: $("#f-bom").checked,
    pcd: $("#f-pcd").checked,
  };
}
function applyFilters(f) {
  const terms = f.q ? f.q.split(/\s+/) : [];
  return LOCAIS.filter((r) => {
    if (!f.tipos.has(r.t)) return false;
    const orig = r.ownership || (r.t === "para" ? "social" : "public");
    if (f.origens && f.origens.size && !f.origens.has(orig)) return false;
    if (f.evidencia) {
      const levs = r.evidence ? Object.values(r.evidence).map((e) => e && e.level).filter(Boolean) : [];
      if (!levs.includes(f.evidencia)) return false;
    }
    if (f.ra && r.ra !== f.ra) return false;
    if (terms.length && !terms.every((t) => r._s.includes(t))) return false;
    if (f.gratis && !r.gratis) return false;
    if (f.luz && r.luz !== true) return false;
    if (f.bom && norm(r.cons) !== "bom") return false;
    if (f.pcd) {
      const hasPcd = (r.acc && r.acc.adaptado) ||
        (r.evidence && r.evidence.accessibility_attributes && r.evidence.accessibility_attributes.adapted_equipment && r.evidence.accessibility_attributes.adapted_equipment.value);
      if (!hasPcd) return false;
    }
    return true;
  });
}

// ---------- Mapa ----------
const DF_BOUNDS = [[-16.08, -48.32], [-15.47, -47.28]];
const START_VIEW = { center: [-15.80, -47.92], zoom: 11 };
let map, cluster, userLayer, meetLayer, userPos = null;
const markerById = new Map();
const placeByMarkerId = new Map();
// Encontros futuros por local, recebidos de encontros.js pelo evento "pa:encontros".
const meetupsByPlace = new Map();
const meetupDate = new Intl.DateTimeFormat("pt-BR", {
  timeZone: "America/Sao_Paulo", weekday: "short", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
});

function initMap() {
  if (!window.L) { $("#map").innerHTML = '<p style="padding:1rem">Não foi possível carregar o mapa. Use a lista abaixo.</p>'; return; }
  map = L.map("map", { scrollWheelZoom: false, maxBounds: DF_BOUNDS, maxBoundsViscosity: 0.8, minZoom: 9 }).setView(START_VIEW.center, START_VIEW.zoom);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "&copy; colaboradores do OpenStreetMap" }).addTo(map);
  map.on("focus", () => map.scrollWheelZoom.enable());
  map.on("blur", () => map.scrollWheelZoom.disable());
  cluster = L.markerClusterGroup
    ? L.markerClusterGroup({ chunkedLoading: true, showCoverageOnHover: false, maxClusterRadius: 45, disableClusteringAtZoom: 16 })
    : L.layerGroup();
  map.addLayer(cluster);
  // Locais com encontros ficam fora dos agrupamentos, sempre visíveis.
  meetLayer = L.layerGroup().addTo(map);
  userLayer = L.layerGroup().addTo(map);
  const ClearControl = L.Control.extend({
    options: { position: "topright" },
    onAdd() {
      const button = L.DomUtil.create("button", "map-clear");
      button.type = "button";
      button.hidden = true;
      button.dataset.clearSearch = "";
      button.textContent = "✕ Limpar busca";
      L.DomEvent.disableClickPropagation(button);
      return button;
    },
  });
  map.addControl(new ClearControl());
  watchPopupFit();
}

function meetupCount(r) {
  return (meetupsByPlace.get(r.id) || []).length;
}

function icon(r) {
  const t = TYPES[r.t];
  const n = meetupCount(r);
  // Gota girada 45°: a ponta fica a meio lado + meia diagonal do topo (≈ 1,21 × tamanho).
  const pin = (size, extra = "") => L.divIcon({
    className: "", iconSize: [size, size], iconAnchor: [size / 2, Math.round(size * 1.21)],
    popupAnchor: [0, -Math.round(size * 1.1)],
    html: `<span class="mk-pin ${extra}" style="--pin:${t.color}"><span>${t.ico}</span></span>` +
      (n ? `<span class="mk-badge">${n}</span>` : ""),
  });
  if (n) return pin(38, "mk-pin-meet");
  return t.featured ? pin(34) : pin(26, "mk-pin-sm");
}

function accTags(r) {
  return Object.entries(ACC_LABELS).map(([k, label]) => {
    const st = (r.acc && r.acc[k]) || "unk";
    const sym = st === "ok" ? "✓" : st === "info" ? "!" : "?";
    return `<span class="${st}" title="${label}: ${STATUS_LABEL[st]}">${label} ${sym}<span class="sr-only"> (${STATUS_LABEL[st]})</span></span>`;
  }).join("");
}
const routeUrl = (r, from) => `https://www.google.com/maps/dir/?api=1${from ? `&origin=${from[0]},${from[1]}` : ""}&destination=${r.lat},${r.lon}`;
const wazeUrl = (r) => `https://waze.com/ul?ll=${r.lat},${r.lon}&navigate=yes`;
const routeLinks = (r, from) => `<a class="go go-gmaps" href="${routeUrl(r, from)}" target="_blank" rel="noopener" aria-label="Abrir rota no Google Maps para ${esc(r.n)}">🗺️ Google Maps</a><a class="go go-waze" href="${wazeUrl(r)}" target="_blank" rel="noopener" aria-label="Abrir rota no Waze para ${esc(r.n)}">🚗 Waze</a>`;

// A acessibilidade fica recolhida em "Ver acessibilidade", com o resumo do que é conhecido.
function accMore(inner, known, total) {
  const resumo = known ? `${known} de ${total} informados` : "nada verificado ainda";
  return `<details class="acc-more"><summary>♿ Ver acessibilidade <small>(${resumo})</small></summary>${inner}</details>`;
}

function renderAccessibilityMatrix(r) {
  const attrs = (r.evidence && r.evidence.accessibility_attributes) || {};
  const hasAttrs = Object.keys(attrs).length > 0;
  if (!hasAttrs) {
    const keys = Object.keys(ACC_LABELS);
    const known = keys.filter((k) => r.acc && r.acc[k] && r.acc[k] !== "unk").length;
    return accMore(`<div class="acc-tags">${accTags(r)}</div>`, known, keys.length);
  }
  const cells = Object.entries(ACC_KEYS_EXT).map(([k, label]) => {
    const item = attrs[k] || { level: "desconhecido", value: null };
    const val = item.value;
    const isOk = val === "ok" || val === true;
    const isInfo = val === "info";
    const stCls = isOk ? "status-ok" : isInfo ? "status-info" : "status-unk";
    const stSym = isOk ? "✓" : isInfo ? "!" : "?";
    const lev = item.level || "desconhecido";
    const badgeCls = EVIDENCE_LEVELS[lev]?.badge || "ev-desconhecido";
    return `<div class="acc-cell ${stCls}">
      <span class="acc-name">${label}</span>
      <span class="acc-status">
        <strong>${stSym}</strong>
        <span class="badge-ev ${badgeCls}">${lev}</span>
      </span>
    </div>`;
  }).join("");
  const keys = Object.keys(ACC_KEYS_EXT);
  const known = keys.filter((k) => attrs[k] && (attrs[k].value === "ok" || attrs[k].value === true || attrs[k].value === "info")).length;
  return accMore(`<div class="acc-matrix" role="group" aria-label="Atributos de acessibilidade">${cells}</div>`, known, keys.length);
}

function details(r, compact) {
  const t = TYPES[r.t] || { label: r.t, color: "#172649", short: r.t };
  const orig = r.ownership || (r.t === "para" ? "social" : "public");
  const origInfo = OWNERSHIP_LABELS[orig] || { label: orig, cls: "ownership-public" };
  const meta = [r.ra, r.dist != null ? `${r.dist.toFixed(1)} km` : null, r.custo].filter(Boolean).map(esc).join(" · ");
  const cond = [
    r.cons ? `Conservação: ${esc(r.cons)}` : null,
    r.luz === true ? "Iluminação pública ✓" : r.luz === false ? "Sem iluminação pública" : null,
  ].filter(Boolean).join(" · ");
  const revDate = r.reviewed_at ? ` · Revisado em: ${esc(r.reviewed_at)}` : "";
  const isRep = r.geo && r.geo.includes("representativo");
  return `
    <p class="meta">${meta} <span class="ownership-badge ${origInfo.cls}">${origInfo.label}</span></p>
    ${r.end ? `<p class="meta">📍 ${esc(r.end)}${isRep ? " <em>(ponto representativo da área)</em>" : r.aprox ? " <em>(posição aproximada)</em>" : ""}</p>` : ""}
    ${r.mods ? `<p class="meta">Modalidades: ${esc(r.mods.join(", "))}${r.mods_inferidas ? ' <em title="Deduzidas pelo tipo de equipamento">(pelo tipo de equipamento)</em>' : ""}</p>` : ""}
    ${cond ? `<p class="meta">${cond}</p>` : ""}
    ${r.tel ? `<p class="meta">☎ ${esc(r.tel)}</p>` : ""}
    ${r.obs && !compact ? `<p class="meta obs">${esc(r.obs)}</p>` : ""}
    ${renderAccessibilityMatrix(r)}
    <p class="src">Fonte: <a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.fonte)}</a>${r.data ? ` · Dados de ${esc(r.data)}` : ""}${r.lat == null ? " · <strong>Localização exata pendente</strong>" : ""}${revDate}</p>`;
}

function meetupsHtml(r) {
  const events = meetupsByPlace.get(r.id) || [];
  if (!events.length) return "";
  const shown = events.slice(0, 3);
  const items = shown.map((e) => {
    const vagas = e.estado === "lotado" ? "Lotado" : `${e.vagas} ${e.vagas === 1 ? "vaga" : "vagas"}`;
    const action = e.meu ? '<span class="pop-meet-mine">Você organiza</span>'
      : e.participando ? '<span class="pop-meet-mine">Você vai</span>'
      : e.estado === "aberto" ? `<button type="button" data-event-action="participacao" data-event-id="${esc(e.id)}">Participar</button>`
      : "";
    return `<li><span><b>${esc(e.esporte)}</b> · ${esc(meetupDate.format(new Date(e.inicio)))}<br>
      <small>${esc(vagas)} · ${e.participantes}/${e.capacidade} pessoas</small></span>${action}</li>`;
  }).join("");
  const more = events.length > shown.length ? `<p class="meta">+ ${events.length - shown.length} no mesmo local</p>` : "";
  const notice = meetupNotice && meetupNotice.until > Date.now() && events.some((e) => e.id === meetupNotice.eventId)
    ? meetupNotice.text : "";
  return `<div class="pop-meet"><p class="pop-meet-title">📅 ${events.length === 1 ? "1 encontro marcado" : `${events.length} encontros marcados`}</p>
    <ul>${items}</ul>${more}<p class="pop-meet-status" role="status" aria-live="polite">${esc(notice)}</p>
    <a href="#encontros">Ver todos os encontros</a></div>`;
}

// Encontros esportivos são para maiores de 18 anos; parquinhos ficam fora da agenda.
const podeMarcarEncontro = (r) => r.t !== "parquinho";

function popupHtml(r) {
  return `<div class="pop"><div class="pop-head"><div><b>${esc(r.n)}</b><br><small style="color:${TYPES[r.t].color};font-weight:700">${TYPES[r.t].label}</small></div>
      ${podeMarcarEncontro(r) ? `<button type="button" class="pop-meet-add" data-meeting-place="${esc(r.id)}" title="Marcar um encontro esportivo neste local"><span aria-hidden="true">📅</span> Marcar encontro</button>` : ""}</div>
    ${meetupsHtml(r)}
    ${details(r, true)}
    ${r.lat != null && rotasDisponiveis ? `<div class="pop-rotas" role="group" aria-label="Traçar rota até ${esc(r.n)}">
      <button type="button" data-rota="${esc(r.id)}" data-perfil="cadeira_de_rodas">♿ Rota para cadeira de rodas</button>
      <button type="button" data-rota="${esc(r.id)}" data-perfil="a_pe">🚶 Rota a pé</button>
    </div>` : ""}
    <div class="place-actions">
      ${r.lat != null ? routeLinks(r) : ""}
      <button type="button" class="btn-contribute" data-contribute-id="${esc(r.id)}" data-contribute-name="${esc(r.n)}">✍️ Colaborar</button>
    </div></div>`;
}

// ---------- Rotas a pé e para cadeira de rodas (openrouteservice, pelo servidor) ----------
// A origem é a localização da pessoa: só é usada depois que ela permite, e vai
// para o servidor no corpo da requisição, nunca na URL.
let rotasDisponiveis = false;
let routeLayer = null;
fetch("/api/servicos", { headers: { Accept: "application/json" } })
  .then((r) => (r.ok ? r.json() : {}))
  .then((d) => { rotasDisponiveis = Boolean(d.rotas); })
  .catch(() => {});

function askLocation() {
  if (userPos && !askSetPos) return Promise.resolve(userPos);
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) { reject(new Error("Seu navegador não informa a localização.")); return; }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve([pos.coords.latitude, pos.coords.longitude]),
      () => reject(new Error("Sem permissão de localização, não dá para traçar a rota.")),
      { timeout: 10000 });
  });
}

function fmtDist(m) { return m >= 1000 ? `${(m / 1000).toFixed(1).replace(".", ",")} km` : `${m} m`; }
function fmtTempo(s) { const min = Math.max(1, Math.round(s / 60)); return min >= 60 ? `${Math.floor(min / 60)} h ${min % 60} min` : `${min} min`; }

function showRouteInfo(html) {
  let box = $("#route-info");
  if (!box) {
    box = document.createElement("div");
    box.id = "route-info";
    box.className = "route-info";
    box.setAttribute("role", "status");
    box.setAttribute("aria-live", "polite");
    $("#map").parentElement.append(box);
  }
  box.innerHTML = html;
  box.hidden = false;
}

function clearRoute() {
  if (routeLayer) { routeLayer.remove(); routeLayer = null; }
  const box = $("#route-info");
  if (box) box.hidden = true;
}

async function traceRoute(placeId, perfil) {
  const r = LOCAIS.find((x) => x.id === placeId);
  if (!r || r.lat == null || !map) return;
  const nome = perfil === "cadeira_de_rodas" ? "para cadeira de rodas" : "a pé";
  showRouteInfo(`<p>Pedindo sua localização para traçar a rota ${nome}…</p>`);
  try {
    const origem = await askLocation();
    showRouteInfo(`<p>Traçando a rota ${nome} até ${esc(r.n)}…</p>`);
    const response = await fetch("/api/rota", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ de: origem, para: [r.lat, r.lon], perfil }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.erro || "Não foi possível traçar a rota agora.");
    clearRoute();
    routeLayer = L.layerGroup([
      L.polyline(data.linha, { color: perfil === "cadeira_de_rodas" ? "#1f5fb0" : "#0f6e2b", weight: 6, opacity: .85 }),
      L.circleMarker(origem, { radius: 8, color: "#fff", fillColor: "#2f78c8", fillOpacity: 1, weight: 3 }).bindTooltip("Você"),
    ]).addTo(map);
    map.closePopup();
    map.fitBounds(L.latLngBounds(data.linha), { padding: [40, 40] });
    const passos = data.passos.map((p) => `<li>${esc(p.instrucao)} <small>(${fmtDist(p.distancia_m)})</small></li>`).join("");
    showRouteInfo(`<div class="route-head"><strong>Rota ${nome} até ${esc(r.n)}</strong>
        <button type="button" data-route-clear aria-label="Apagar a rota">✕</button></div>
      <p>${fmtDist(data.distancia_m)} · cerca de ${fmtTempo(data.duracao_s)}</p>
      ${passos ? `<details><summary>Ver o passo a passo</summary><ol>${passos}</ol></details>` : ""}
      <p class="route-src">Rota calculada pelo openrouteservice com dados do OpenStreetMap. ${perfil === "cadeira_de_rodas" ? "Confira o trajeto: calçadas e rampas podem não estar mapeadas." : ""}</p>`);
  } catch (error) {
    showRouteInfo(`<div class="route-head"><strong>Rota ${nome}</strong><button type="button" data-route-clear aria-label="Fechar">✕</button></div><p>${esc(error.message)}</p>`);
  }
}

document.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-rota]");
  if (btn) { traceRoute(btn.dataset.rota, btn.dataset.perfil); return; }
  if (e.target.closest("[data-route-clear]")) clearRoute();
});

// O balão nunca passa da altura do mapa: o que não couber rola por dentro dele.
// Desconta o pino, a seta do balão e uma folga para o mapa não precisar se mover tanto.
function popupOptions() {
  const height = map ? map.getSize().y : 430;
  // autoPan desligado: o deslocamento é feito por fitPopupInMap, respeitando os limites do DF.
  return { maxWidth: 300, maxHeight: Math.max(200, height - 110), autoPan: false };
}

// O mapa fica preso aos limites do DF, então nem sempre consegue se mover para
// mostrar o balão inteiro. Depois que ele termina de se mover, o balão encolhe
// para o espaço que sobrou acima do pino e o resto rola por dentro.
const POPUP_PAD = 12;
const POPUP_PAD_LEFT = 52; // deixa livres os botões + e − do zoom

function popupOverflow(el) {
  const m = map.getContainer().getBoundingClientRect();
  const p = el.getBoundingClientRect();
  return {
    x: p.left < m.left + POPUP_PAD_LEFT ? p.left - m.left - POPUP_PAD_LEFT : p.right > m.right - POPUP_PAD ? p.right - m.right + POPUP_PAD : 0,
    y: p.top < m.top + POPUP_PAD ? p.top - m.top - POPUP_PAD : 0,
  };
}

// Ao abrir um balão, o mapa desliza até deixá-lo no centro (ou com o topo à
// vista, se o balão for mais alto que o mapa), sem sair dos limites do DF.
function shrinkPopupIfNeeded(popup) {
  const el = popup.getElement();
  if (!el || !map) return;
  // Se ainda faltar espaço acima, o balão encolhe e o resto rola por dentro.
  const rest = popupOverflow(el).y;
  if (rest < 0) {
    popup.options.maxHeight = Math.max(160, popup.options.maxHeight + rest);
    popup.update();
  }
}

function fitPopupInMap(popup) {
  const el = popup.getElement();
  if (!el || !map) return;
  const m = map.getContainer().getBoundingClientRect();
  const p = el.getBoundingClientRect();
  const dx = p.left + p.width / 2 - (m.left + m.width / 2);
  const tall = p.height > m.height - 2 * POPUP_PAD;
  const dy = tall ? p.top - m.top - POPUP_PAD : p.top + p.height / 2 - (m.top + m.height / 2);
  const zoom = map.getZoom();
  const target = map.containerPointToLatLng(map.getSize().divideBy(2).add([dx, dy]));
  const center = map.options.maxBounds && map._limitCenter
    ? map._limitCenter(target, zoom, map.options.maxBounds) : target;
  const shift = map.latLngToContainerPoint(center).distanceTo(map.getSize().divideBy(2));
  const calm = document.body.classList.contains("no-motion") || matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (shift > 4) {
    map.once("moveend", () => shrinkPopupIfNeeded(popup));
    map.panTo(center, { animate: !calm, duration: 0.35 });
  } else {
    shrinkPopupIfNeeded(popup);
  }
  // Se o mapa não estiver inteiro na tela, a página rola até ele.
  if (m.top < 0 || m.bottom > innerHeight) {
    map.getContainer().scrollIntoView({ block: "center", behavior: calm ? "auto" : "smooth" });
  }
}

function watchPopupFit() {
  map.on("popupopen", (e) => {
    e.popup.options.maxHeight = popupOptions().maxHeight;
    e.popup.update();
    // setTimeout em vez de requestAnimationFrame: este último fica pausado em abas em segundo plano.
    setTimeout(() => fitPopupInMap(e.popup), 0);
  });
}

function makeMarker(r) {
  const n = meetupCount(r);
  const title = n ? `${r.n} · ${n === 1 ? "1 encontro marcado" : `${n} encontros marcados`}` : r.n;
  const m = L.marker([r.lat, r.lon], { icon: icon(r), title, alt: title, keyboard: false,
    zIndexOffset: n ? 2000 : TYPES[r.t].featured ? 1000 : 0 });
  m.bindPopup(() => popupHtml(r), popupOptions());
  markerById.set(r.id, m);
  placeByMarkerId.set(r.id, r);
  return m;
}

function drawMarkers(list) {
  if (!map) return;
  cluster.clearLayers();
  meetLayer.clearLayers();
  markerById.clear();
  placeByMarkerId.clear();
  const ms = [];
  for (const r of list) {
    if (r.lat == null) continue;
    const m = makeMarker(r);
    if (meetupCount(r)) meetLayer.addLayer(m); else ms.push(m);
  }
  cluster.addLayers ? cluster.addLayers(ms) : ms.forEach((m) => cluster.addLayer(m));
}

// Atualiza só os pinos cujos encontros mudaram, sem redesenhar o mapa inteiro.
function signature(events) {
  return JSON.stringify((events || []).map((e) => [e.id, e.estado, e.vagas, e.participando, e.meu]));
}

document.addEventListener("pa:encontros", (event) => {
  const next = new Map();
  for (const e of event.detail.encontros || []) {
    if (!["aberto", "lotado"].includes(e.estado) || !e.local || !e.local.id) continue;
    if (!next.has(e.local.id)) next.set(e.local.id, []);
    next.get(e.local.id).push(e);
  }
  for (const events of next.values()) events.sort((a, b) => a.inicio.localeCompare(b.inicio));
  const changed = new Set([...meetupsByPlace.keys(), ...next.keys()]
    .filter((id) => signature(meetupsByPlace.get(id)) !== signature(next.get(id))));
  meetupsByPlace.clear();
  for (const [id, events] of next) meetupsByPlace.set(id, events);
  if (!map) return;
  for (const id of changed) {
    const old = markerById.get(id);
    const r = placeByMarkerId.get(id);
    if (!old || !r) continue;
    const wasOpen = old.isPopupOpen();
    cluster.removeLayer(old);
    meetLayer.removeLayer(old);
    const m = makeMarker(r);
    if (meetupCount(r)) meetLayer.addLayer(m); else cluster.addLayer(m);
    if (wasOpen) m.openPopup();
  }
});


// ---------- Painel "Encontros de hoje e amanhã" ----------
const MEET_LEVELS = { iniciante: "Iniciante", intermediario: "Intermediário", avancado: "Avançado", todos: "Todos os níveis" };
const meetDayKey = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Sao_Paulo" }); // aaaa-mm-dd em Brasília
const meetDayName = new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", day: "2-digit", month: "short" });
const meetHour = new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit" });
let allMeetups = [];

function meetCard(e, today, tomorrow) {
  const start = new Date(e.inicio);
  const key = meetDayKey.format(start);
  const day = key === today ? "Hoje" : key === tomorrow ? "Amanhã" : meetDayName.format(start).replace(".", "");
  const few = e.estado === "aberto" && e.vagas <= Math.max(1, Math.floor(e.capacidade / 4));
  const [chip, tone] = e.estado === "lotado" ? ["Lotado", "full"] : few ? ["Poucas vagas", "few"] : ["Vagas abertas", "open"];
  const pct = Math.min(100, Math.round((100 * e.participantes) / e.capacidade));
  const action = e.meu ? '<span class="mm-mine">Você organiza</span>'
    : e.participando ? '<span class="mm-mine">Você vai</span>'
    : e.estado === "aberto" ? `<button type="button" class="btn btn-primary mm-join" data-event-action="participacao" data-event-id="${esc(e.id)}">Participar</button>`
    : "";
  const place = LOCAIS.find((r) => r.id === e.local.id);
  const focus = place && place.lat != null
    ? `<button type="button" class="mm-see" data-meet-focus="${esc(e.local.id)}">Ver no mapa</button>` : "";
  const organizer = e.organizador || "?";
  return `<li class="mm-card">
    <div class="mm-chips"><span class="mm-sport">${esc(e.esporte)}</span><span class="mm-state mm-${tone}">${chip}</span></div>
    <h4>${esc(e.local.nome)}</h4>
    <p class="mm-where">${esc(e.local.regiao || "Distrito Federal")}</p>
    <div class="mm-row">
      <span><b>${day} • ${meetHour.format(start)}</b><br>${esc(MEET_LEVELS[e.nivel] || "")}</span>
      <span class="mm-count"><b>${e.participantes}/${e.capacidade} pessoas</b><br>${e.vagas} ${e.vagas === 1 ? "vaga" : "vagas"}</span>
    </div>
    <div class="mm-bar mm-bar-${tone}" aria-hidden="true"><i style="width:${pct}%"></i></div>
    <div class="mm-foot">
      <span class="mm-by"><span class="mm-avatar" aria-hidden="true">${esc(organizer[0].toUpperCase())}</span>por ${esc(organizer)}</span>
      <span class="mm-actions">${action}${focus}</span>
    </div>
  </li>`;
}

function renderMeetPanel() {
  const list = $("#map-meet-list");
  if (!list) return;
  const now = new Date();
  const today = meetDayKey.format(now);
  const tomorrow = meetDayKey.format(new Date(now.getTime() + 864e5));
  const soon = allMeetups.filter((e) => [today, tomorrow].includes(meetDayKey.format(new Date(e.inicio))));
  // Sem encontros hoje ou amanhã, mostra os próximos para o painel não ficar vazio.
  const shown = (soon.length ? soon : allMeetups).slice(0, 8);
  $("#map-meet-title").textContent = soon.length || !allMeetups.length ? "Encontros de hoje e amanhã" : "Próximos encontros";
  list.innerHTML = shown.length ? shown.map((e) => meetCard(e, today, tomorrow)).join("")
    : '<li class="map-meet-empty">Nenhum encontro marcado ainda.<br>Clique em um local do mapa e use <b>Marcar encontro</b>.</li>';
}

document.addEventListener("pa:encontros", (event) => {
  allMeetups = (event.detail.encontros || [])
    .filter((e) => ["aberto", "lotado"].includes(e.estado) && e.local && e.local.id)
    .sort((a, b) => a.inicio.localeCompare(b.inicio));
  renderMeetPanel();
});
document.addEventListener("pa:aviso-encontro", (event) => { $("#map-meet-status").textContent = event.detail.text; });
$("#map-meet-list").addEventListener("click", (e) => {
  const focus = e.target.closest("[data-meet-focus]");
  if (focus) window.PontoAtivoFocus(focus.dataset.meetFocus);
});

// Mensagem de confirmação ou erro de uma ação feita no balão (vem de encontros.js).
let meetupNotice = null;
document.addEventListener("pa:aviso-encontro", (event) => {
  meetupNotice = { ...event.detail, until: Date.now() + 10000 };
  for (const [placeId, events] of meetupsByPlace) {
    if (!events.some((e) => e.id === meetupNotice.eventId)) continue;
    const m = markerById.get(placeId);
    if (m && m.isPopupOpen()) m.getPopup().update();
  }
});

// ---------- Lista ----------
// A lista começa curta para não empurrar o resto da página; "Mostrar mais" amplia.
const FIRST_PAGE = 2;
const PAGE = 24;
let current = [], shown = 0;

function sortList(list) {
  if (userPos) {
    return list.map((r) => ({ ...r, dist: r.lat != null ? km(userPos, [r.lat, r.lon]) : Infinity })).sort((a, b) => a.dist - b.dist);
  }
  const rank = (r) => (TYPES[r.t].featured ? 0 : 1);
  return list.slice().sort((a, b) => rank(a) - rank(b) || ORDER.indexOf(a.t) - ORDER.indexOf(b.t) || (a.ra || "").localeCompare(b.ra || "", "pt-BR"));
}

function cardHtml(r) {
  const t = TYPES[r.t] || { short: r.t, color: "#172649" };
  return `<li class="place" id="place-${esc(r.id)}">
    <header><h3>${esc(r.n)}</h3><span class="type-badge" style="background:${t.color}">${t.short}</span></header>
    ${details(r, false)}
    <div class="place-actions">${podeMarcarEncontro(r) ? `<button type="button" data-meeting-place="${esc(r.id)}">Marcar encontro</button>` : ""}
      ${r.lat != null ? `<button type="button" data-focus="${esc(r.id)}">Ver no mapa</button>${routeLinks(r)}` : ""}
      <button type="button" class="btn-contribute" data-contribute-id="${esc(r.id)}" data-contribute-name="${esc(r.n)}">✍️ Colaborar / verificar</button>
    </div>
  </li>`;
}

function renderList(reset) {
  if (reset) { shown = 0; $("#place-list").innerHTML = ""; }
  const next = current.slice(shown, shown + (shown === 0 ? FIRST_PAGE : PAGE));
  $("#place-list").insertAdjacentHTML("beforeend", next.map(cardHtml).join(""));
  shown += next.length;
  const more = $("#btn-more");
  more.hidden = shown >= current.length;
  more.textContent = `Mostrar mais (${fmt(current.length - shown)} restantes)`;
  if (!current.length) {
    $("#place-list").innerHTML = '<li class="place">Nenhum local atende a todos os filtros. Tente remover algum critério ou escolher outra região.</li>';
  }
}

function update() {
  const f = getFilters();
  syncFilterSummary();
  current = sortList(applyFilters(f));
  const semPino = current.filter((r) => r.lat == null).length;
  $("#results-count").textContent = `${fmt(current.length)} ${current.length === 1 ? "local encontrado" : "locais encontrados"}` +
    (userPos ? " · ordenados por distância" : "") + (semPino ? ` · ${semPino} sem localização exata (só na lista)` : "");
  drawMarkers(current);
  renderList(true);
  if (map && f.ra) {
    const pts = current.filter((r) => r.lat != null).map((r) => [r.lat, r.lon]);
    if (pts.length) map.fitBounds(pts, { padding: [30, 30], maxZoom: 15 });
  }
  syncClearSearch();
}

// ---------- Limpar busca ----------
// Há busca ativa quando há pergunta respondida ou algum filtro tira locais do mapa.
function searchActive() {
  const f = getFilters();
  return Boolean(f.q || f.ra || f.evidencia || f.gratis || f.luz || f.bom || f.pcd) ||
    $$("#f-tipos input, #f-origem input").some((i) => !i.checked) ||
    !$("#ask-answer").hidden || Boolean($("#ask-q").value.trim()) || Boolean(refLayer);
}

function syncClearSearch() {
  const active = searchActive();
  $$("[data-clear-search]").forEach((b) => (b.hidden = !active));
}

function clearSearch() {
  clearTimeout(t);
  $("#map-pref-note").hidden = true;
  askSeq += 1; // uma consulta em andamento não preenche mais a caixa
  askPending = false;
  $("#ask-q").value = "";
  $("#ask-status").textContent = "";
  $("#ask-answer").replaceChildren();
  $("#ask-answer").hidden = true;
  lastAnswerText = "";
  if ("speechSynthesis" in window) speechSynthesis.cancel();
  $("#filters").reset();
  // A localização pedida em "Usar minha localização" continua; a da pergunta, não.
  if (askSetPos) { userPos = null; askSetPos = false; }
  if (refLayer) { refLayer.remove(); refLayer = null; }
  update();
  if (map) {
    map.closePopup();
    map.setView(START_VIEW.center, START_VIEW.zoom);
  }
  $("#f-q").focus({ preventScroll: true });
}
document.addEventListener("click", (e) => {
  if (e.target.closest("[data-clear-search]")) clearSearch();
});

// ---------- Preferências da conta ----------
// Esportes das preferências (encontros.js) -> tipos de local do mapa.
const SPORT_TYPES = {
  "Futebol": ["campo", "quadra"], "Futsal": ["quadra"], "Vôlei": ["quadra", "areia"],
  "Vôlei de areia": ["areia"], "Basquete": ["quadra"], "Tênis": ["tenis", "clube"],
  "Beach tennis": ["areia"], "Futevôlei": ["areia"], "Caminhada": ["parque", "pec"],
  "Corrida": ["parque"], "Skate": ["skate"], "Exercícios no PEC": ["pec", "ginastica"],
  "Alongamento": ["pec", "parque"], "Natação": ["cop", "clube"],
  "Bocha paralímpica": ["cop", "para"], "Goalball": ["cop", "para"], "Atletismo": ["cop", "estadio"],
  "Tênis em cadeira de rodas": ["tenis", "para"], "Basquete em cadeira de rodas": ["quadra", "para"],
};
let mapPrefsApplied = false;

// Aplica as preferências só se o mapa ainda não tem busca ou filtro da pessoa.
document.addEventListener("pa:preferencias", (event) => {
  const prefs = event.detail || {};
  // Filtros que vieram das preferências podem ser trocados; os da pessoa, não.
  const fromPrefs = mapPrefsApplied && !$("#map-pref-note").hidden;
  if (searchActive() && !fromPrefs) return;
  if (fromPrefs) {
    $$("#f-tipos input").forEach((i) => (i.checked = true));
    $("#f-ra").value = "";
    $("#map-pref-note").hidden = true;
  }
  const tipos = new Set((prefs.esportes || []).flatMap((s) => SPORT_TYPES[s] || []));
  const ra = RAS.includes(prefs.regiao) ? prefs.regiao : "";
  if (!tipos.size && !ra) { update(); return; }
  if (tipos.size) $$("#f-tipos input").forEach((i) => (i.checked = tipos.has(i.value)));
  $("#f-ra").value = ra;
  const note = $("#map-pref-note");
  const label = document.createElement("span");
  label.textContent = "Mapa filtrado pelas suas preferências: " +
    [ra, (prefs.esportes || []).join(", ")].filter(Boolean).join(" · ") + ". ";
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = "Ver todos os locais";
  button.addEventListener("click", clearSearch);
  note.replaceChildren(label, button);
  note.hidden = false;
  mapPrefsApplied = true;
  update();
});
document.addEventListener("pa:preferencias-limpas", () => {
  if (mapPrefsApplied && !$("#map-pref-note").hidden) clearSearch();
});

let t;
$("#filters").addEventListener("input", () => { clearTimeout(t); t = setTimeout(update, 180); });
$("#filters").addEventListener("submit", (e) => e.preventDefault());
$("#btn-more").addEventListener("click", () => renderList(false));
function focusPlace(id) {
  if (!id || !map) return;
  const m = markerById.get(id);
  if (!m) return;
  $("#map").scrollIntoView({ behavior: "smooth", block: "center" });
  const open = () => { m.openPopup(); };
  if (cluster.zoomToShowLayer) cluster.zoomToShowLayer(m, open); else { map.setView(m.getLatLng(), 16); open(); }
}
$("#place-list").addEventListener("click", (e) => focusPlace(e.target.dataset && e.target.dataset.focus));

// Localização só após ação do usuário (RNF09)
$("#btn-near").addEventListener("click", () => {
  const btn = $("#btn-near");
  if (!navigator.geolocation) { btn.textContent = "Localização indisponível – use a região"; return; }
  btn.textContent = "Obtendo localização…";
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      userPos = [pos.coords.latitude, pos.coords.longitude];
      askSetPos = false;
      btn.textContent = "Ordenado por proximidade";
      if (map) {
        userLayer.clearLayers();
        L.circleMarker(userPos, { radius: 9, color: "#fff", fillColor: "#2f78c8", fillOpacity: 1, weight: 3 }).bindPopup("Você está aqui").addTo(userLayer);
        map.setView(userPos, 14);
      }
      update();
    },
    () => { btn.textContent = "Permissão negada – use a região"; },
    { timeout: 10000 });
});

// ---------- Pergunte ao PontoAtivo (texto ou voz) ----------
// Interpreta a pergunta com regras simples e transparentes (mostra o que entendeu),
// localiza o endereço citado e lista as opções mais próximas com rota no Google Maps ou Waze.
const ASK_TYPES = [
  { re: /\bpecs?\b|ponto de encontro|academia (ao ar livre|da terceira idade|publica|comunitaria)|\bati\b/, tipos: ["pec"], nome: "PEC" },
  { re: /aparelhos?|ginastica|malhar|musculacao|exercicios?/, tipos: ["pec", "ginastica"], nome: "PEC e aparelhos de ginástica" },
  { re: /areia|futevolei|beach|altinha/, tipos: ["areia"], nome: "quadra de areia" },
  { re: /volei/, tipos: ["quadra", "areia"], nome: "vôlei" },
  { re: /basquete|futsal|handebol|quadras?|poliesportiva/, tipos: ["quadra"], nome: "quadra" },
  { re: /\bcampos?\b|campinho|gramado|society|sintetico|varzea/, tipos: ["campo"], nome: "campo de futebol" },
  { re: /futebol|pelada|bola|\bfut\b/, tipos: ["campo", "quadra"], nome: "futebol" },
  { re: /skate|patins|patinete|bmx|roller/, tipos: ["skate"], nome: "pista de skate" },
  { re: /\btenis\b/, tipos: ["tenis"], nome: "tênis" },
  { re: /parquinhos?|parques? infant(il|is)|playgrounds?|brinquedos?|escorregador|balanco|gangorra/, tipos: ["parquinho"], nome: "parquinho" },
  { re: /parques?|caminhada|caminhar|correr|corrida|trilha|pedalar|bicicleta|ciclovia/, tipos: ["parque", "pec"], nome: "parque / caminhada" },
  { re: /\bpracas?\b/, tipos: ["praca"], nome: "praça" },
  { re: /natacao|piscina|nadar|hidroginastica/, tipos: ["cop", "estadio"], nome: "natação" },
  { re: /centros? olimpicos?|\bcops?\b/, tipos: ["cop"], nome: "Centro Olímpico" },
  { re: /estadio|ginasio|complexo/, tipos: ["estadio"], nome: "estádio / ginásio" },
  { re: /paradesporto|paralimpic|cadeira de rodas|deficien|\bpcd\b|adaptad|goalball|bocha/, tipos: ["cop", "para"], nome: "esporte adaptado", pcd: true },
];
const ASK_RA_EXTRA = { "asa sul": "Plano Piloto", "asa norte": "Plano Piloto", "plano piloto": "Plano Piloto", "noroeste": "Plano Piloto",
  "riacho fundo 2": "Riacho Fundo Ii", "sobradinho 2": "Sobradinho Ii", "estrutural": "SCIA/Estrutural", "por do sol": "Sol Nascente/Pôr do Sol",
  "vila planalto": "Plano Piloto", "lago paranoa": "Lago Sul", "octogonal": "Sudoeste/octogonal" };
const ADDR_RE = /\b((?:sqsw|sqnw|sqs|sqn|shis|shin|shcgn|cln|cls|crs|crn|eqnm|eqnn|eqno|eqnp|eqs|eqn|qnn|qnm|qno|qnp|qnr|qnq|qna|qnb|qnc|qnd|qne|qnf|qng|qnh|qnj|qnl|qsa|qsb|qsc|qsd|qse|qsf|qmsw|qms|qr|qs|qi|qe|ql|qd|qn|qc|aos|sgas|sgan|quadra)\s*\d+[a-z]?(?:\s*(?:conjunto|conj|cj|bloco|bl|lote|lt|casa)\s*[a-z0-9]+)*)/;

// Aliases de RA: nome normalizado, partes separadas por "/" e extras (mais longos primeiro)
const RA_ALIASES = (() => {
  const out = [];
  for (const ra of RAS) {
    const n = norm(ra);
    out.push([n, ra]);
    if (n.includes("/")) n.split("/").forEach((p) => out.push([p.trim(), ra]));
  }
  for (const [a, ra] of Object.entries(ASK_RA_EXTRA)) out.push([a, ra]);
  return out.sort((a, b) => b[0].length - a[0].length);
})();

function parseQuestion(raw) {
  const q = " " + norm(raw).replace(/[?!.,;:]/g, " ").replace(/\s+/g, " ") + " ";
  const res = { tipos: new Set(), nomes: [], pcd: false, ras: [], raNome: "", bairro: "", endereco: "", pertoDeMim: false, atividadeNaoCatalogada: "" };
  const addrM = q.match(ADDR_RE);
  for (const [alias, ra] of RA_ALIASES) {
    const m = q.match(new RegExp(`\\b${alias.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b(\\s+(norte|sul|leste|oeste|centro|expansao))?`));
    if (m) {
      res.raNome = ra;
      res.ras = RAS.filter((r) => norm(r).split("/")[0] === norm(ra).split("/")[0]);
      if (m[1] || ASK_RA_EXTRA[alias]) res.bairro = m[0].trim();
      break;
    }
  }
  res.pertoDeMim = /perto de mim|perto daqui|aqui perto|minha localizacao|onde estou|mais proximo de mim|proximo de mim/.test(q);
  if (addrM) res.endereco = addrM[1].trim();
  else {
    const p = q.match(/(?:perto d[aoe]s?|proximo (?:a|ao|a|da|do|de)|no endereco|endereco|na rua|na avenida)\s+(.+?)\s*$/);
    if (p && !res.pertoDeMim) {
      let e = p[1].replace(/\b(no|na|em)\s+(o\s+)?(df|distrito federal|brasilia)\b/g, "").trim();
      if (res.bairro) e = e.replace(res.bairro, "").trim();
      if (e.length > 2 && !RA_ALIASES.some(([al]) => al === e)) res.endereco = e;
    }
  }
  const qt = res.endereco ? q.replace(res.endereco, " ") : q; // "quadra 12" ou "parque da cidade" é endereço, não tipo
  for (const t of ASK_TYPES) if (t.re.test(qt)) { t.tipos.forEach((x) => res.tipos.add(x)); res.nomes.push(t.nome); if (t.pcd) res.pcd = true; }
  if (/areia/.test(qt) && !/poliesportiva|basquete|futsal/.test(qt)) res.tipos.delete("quadra");
  if (/\bcampos?\b|campinho|gramado|society|sintetico|varzea/.test(qt) && !/quadra|futsal/.test(qt)) res.tipos.delete("quadra");
  if (/\bpecs?\b|ponto de encontro/.test(qt) && !/aparelho|ginastica/.test(qt)) res.tipos.delete("ginastica");
  // "parque infantil" é parquinho, não parque de caminhada
  if (/parques? infant(il|is)/.test(qt) && !/caminhada|caminhar|correr|corrida|trilha|parques? (urbano|ecologico|da cidade)/.test(qt)) {
    res.tipos.delete("parque"); res.tipos.delete("pec");
    res.nomes = res.nomes.filter((n) => n !== "parque / caminhada");
  }
  const naoCatalogadas = [
    [/\bringue\b|boxe|boxing|porrada|luta|briga/, "ringue ou espaço para lutas"],
    [/artes marciais|jiu[\s-]?jitsu|jud[oô]|karate|karat[eê]|taekwondo|muay thai/, "artes marciais"],
    [/\bacademia\b(?!\s+(?:ao ar livre|da terceira idade|publica|comunitaria))/, "academia"],
    [/crossfit|yoga|pilates|danca|escalada|rugby|cricket|badminton|squash/, "essa modalidade"],
  ];
  for (const [re, nome] of naoCatalogadas) {
    if (re.test(qt)) { res.atividadeNaoCatalogada = nome; break; }
  }

  return res;
}

const geoCache = new Map();
async function geocode(text) {
  if (geoCache.has(text)) return geoCache.get(text);
  const url = "https://nominatim.openstreetmap.org/search?" + new URLSearchParams({
    q: text + ", Distrito Federal, Brasil", format: "json", limit: "1", countrycodes: "br",
    viewbox: "-48.29,-15.49,-47.30,-16.06", bounded: "1", "accept-language": "pt-BR" });
  try {
    const r = await fetch(url, { headers: { Accept: "application/json" } });
    const d = await r.json();
    const hit = d && d[0] ? { pos: [+d[0].lat, +d[0].lon], label: d[0].display_name.split(",").slice(0, 3).join(",") } : null;
    geoCache.set(text, hit);
    return hit;
  } catch { return null; }
}
// Plano B sem internet: usa os próprios endereços da base (ex.: "QNP 28")
function localAddress(addr, ras) {
  const a = norm(addr);
  const hits = LOCAIS.filter((r) => r.lat != null && norm(r.end).includes(a) && (!ras.length || ras.includes(r.ra)));
  if (!hits.length) return null;
  return { pos: [hits.reduce((s, r) => s + r.lat, 0) / hits.length, hits.reduce((s, r) => s + r.lon, 0) / hits.length], label: addr.toUpperCase() };
}
function getMyPosition() {
  return new Promise((ok) => {
    if (!navigator.geolocation) return ok(null);
    navigator.geolocation.getCurrentPosition((p) => ok([p.coords.latitude, p.coords.longitude]), () => ok(null), { timeout: 10000 });
  });
}

let refLayer = null, lastAnswerText = "", askSetPos = false;
function plural(n, s, p) { return `${fmt(n)} ${n === 1 ? s : p}`; }

let askPending = false;
let askSeq = 0;

// As duas barras de perguntas usam as mesmas funções; "target" escolhe a caixa.
function showChatMessage(message, target = "#ask-answer") {
  const box = $(target);
  const paragraph = document.createElement("p");
  paragraph.textContent = message;
  box.replaceChildren(paragraph);
  box.hidden = false;
  if (target === "#ask-answer") lastAnswerText = message;
}

// O servidor cita os trechos como [F1]…[F5], na ordem em que foram buscados. Na tela
// viram números sobrescritos 1, 2, 3 na ordem da lista de fontes abaixo da resposta.
const CITATION = /\s*((?:\[F\d+\])+)/g;

function citationNumbers(fontes) {
  return new Map(fontes.map((source, i) => [source.referencia, i + 1]));
}

function renderCitedText(text, numbers) {
  const fragment = document.createDocumentFragment();
  let last = 0;
  for (const match of text.matchAll(CITATION)) {
    fragment.append(text.slice(last, match.index));
    const refs = [...new Set([...match[1].matchAll(/F\d+/g)].map((m) => m[0]))];
    const nums = refs.map((ref) => numbers.get(ref)).filter(Boolean);
    if (nums.length) {
      const sup = document.createElement("sup");
      sup.className = "cite";
      sup.textContent = nums.join(",");
      sup.title = "Fonte " + nums.join(" e ") + " na lista abaixo";
      fragment.append(sup);
    }
    last = match.index + match[0].length;
  }
  fragment.append(text.slice(last));
  return fragment;
}

function showDocumentAnswer(result, target = "#ask-answer") {
  const box = $(target);
  const numbers = citationNumbers(result.fontes);
  const paragraph = document.createElement("p");
  paragraph.append(renderCitedText(result.resposta, numbers));
  box.replaceChildren(paragraph);
  box.hidden = false;
  // Leitura em voz alta sem os marcadores.
  if (target === "#ask-answer") lastAnswerText = result.resposta.replace(CITATION, "");
  if (!result.fontes.length) return;
  const heading = document.createElement("p");
  heading.className = "cite-heading";
  heading.textContent = "Fontes";
  const list = document.createElement("ol");
  list.className = "cite-list";
  for (const source of result.fontes) {
    const item = document.createElement("li");
    const label = `${source.titulo}${source.paginas ? ` · p. ${source.paginas}` : ""}`;
    if (/^https?:\/\//i.test(source.url)) {
      const link = document.createElement("a");
      link.href = source.url;
      link.target = "_blank";
      link.rel = "noopener";
      link.textContent = label;
      item.append(link);
    } else {
      item.textContent = label;
    }
    if (source.trecho) {
      const excerpt = document.createElement("p");
      excerpt.textContent = source.trecho;
      item.append(excerpt);
    }
    list.append(item);
  }
  box.append(heading, list);
}

// A barra do mapa indica a pesquisa de dúvidas quando a pergunta é complexa.
function suggestDuvidas(question) {
  showChatMessage("Essa é uma dúvida mais complexa, sobre regras, matrícula ou programas. " +
    "A pesquisa de dúvidas responde com base nos documentos oficiais.");
  const button = document.createElement("button");
  button.type = "button";
  button.className = "btn btn-outline ask-go-duvidas";
  button.textContent = "Pesquisar nas dúvidas";
  button.addEventListener("click", () => {
    $("#duv-q").value = question;
    window.PontoAtivoTelas.ir("pergunte-duvidas");
    askDuvida(question);
  });
  $("#ask-answer").append(button);
}

let duvPending = false;
let duvController = null;

function syncDuvClear() {
  $("#duv-clear").hidden = !(duvPending || !$("#duv-answer").hidden || $("#duv-q").value.trim());
}

function clearDuvida() {
  if (duvController) duvController.abort(); // para de esperar a resposta
  $("#duv-q").value = "";
  $("#duv-status").textContent = "";
  $("#duv-answer").replaceChildren();
  $("#duv-answer").hidden = true;
  syncDuvClear();
  $("#duv-q").focus({ preventScroll: true });
}

async function askDuvida(raw) {
  if (duvPending) return;
  const status = $("#duv-status"), target = "#duv-answer";
  const question = raw.trim();
  if (!question) { status.textContent = "Digite sua dúvida."; return; }
  duvPending = true;
  duvController = new AbortController();
  const { signal } = duvController;
  $(target).hidden = true;
  syncDuvClear();
  const started = Date.now();
  const tick = () => {
    const seconds = Math.round((Date.now() - started) / 1000);
    status.textContent = `Pesquisando nos documentos oficiais… ${seconds} s (pode levar até 2 minutos)`;
  };
  tick();
  const timer = setInterval(tick, 1000);
  try {
    const response = await fetch("/api/perguntar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pergunta: question, foco: "duvidas" }),
      signal,
    });
    if (!response.headers.get("content-type")?.includes("application/json")) {
      throw new Error("Servidor de consulta indisponível");
    }
    const result = await response.json();
    if (!response.ok) {
      showChatMessage(result.erro, target);
    } else if (result.rota === "fora_escopo") {
      showChatMessage(result.termo
        ? `Sua dúvida tem um termo impróprio ("${result.termo}"), então não fiz a pesquisa. Reformule sem esse termo.`
        : "Essa dúvida está fora do escopo do PontoAtivo, que trata de esporte, lazer e acessibilidade no DF.", target);
    } else {
      showDocumentAnswer(result, target);
    }
  } catch {
    if (!signal.aborted) showChatMessage("A pesquisa de dúvidas está indisponível agora. Tente de novo em instantes.", target);
  } finally {
    clearInterval(timer);
    duvPending = false;
    duvController = null;
    if (!signal.aborted) status.textContent = "";
    syncDuvClear();
  }
}

async function ask(raw) {
  if (askPending) return;
  const status = $("#ask-status");
  const question = raw.trim();
  if (!question) { status.textContent = "Digite ou fale sua pergunta."; return; }
  askPending = true;
  const seq = ++askSeq;
  $("#ask-answer").hidden = true;
  status.textContent = "Interpretando sua pergunta…";
  const outsideScope = "Esse pedido está fora do escopo do PontoAtivo. Posso ajudar a encontrar espaços e atividades esportivas, de lazer ou de acessibilidade.";
  try {
    const response = await fetch("/api/perguntar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pergunta: question, foco: "locais" }),
    });
    if (!response.headers.get("content-type")?.includes("application/json")) {
      throw new Error("Servidor de consulta indisponível");
    }
    const result = await response.json();
    if (seq !== askSeq) return; // a busca foi limpa enquanto esperava
    if (!response.ok) {
      showChatMessage(result.erro);
    } else if (result.rota === "fora_escopo" && result.motivo === "termo_improprio") {
      showChatMessage(`Sua pergunta tem um termo impróprio ("${result.termo}"), então não fiz a busca. ` +
        "O PontoAtivo ajuda só com espaços e atividades de esporte, lazer e acessibilidade. Reformule sem esse termo.");
    } else if (result.rota === "fora_escopo") {
      showChatMessage(outsideScope);
    } else if (result.rota === "esclarecer") {
      showChatMessage("Qual atividade, espaço ou informação você procura? Se quiser encontrar um local, informe também a região.");
    } else if (result.rota === "duvidas") {
      suggestDuvidas(question);
    } else if (result.rota === "documentos") {
      showDocumentAnswer(result);
    } else if (result.rota === "mapa") {
      status.textContent = "Buscando no mapa…";
      await searchMap(result.busca);
    }
  } catch {
    if (seq === askSeq) showChatMessage("A consulta está indisponível agora. Você pode procurar espaços usando os filtros do mapa.");
  } finally {
    if (seq === askSeq) {
      askPending = false;
      status.textContent = "";
    }
    syncClearSearch();
  }
}

const PISOS = [
  { re: /\b(sinteticos?|sinteticas?|society|grama sintetica)\b/, chave: "sintetico", nome: "sintético" },
  { re: /\b(terra batida|de terra|varzea)\b/, chave: "terra batida", nome: "terra batida" },
];

function pisoDaPergunta(query) {
  return PISOS.find((p) => p.re.test(query)) || null;
}

async function searchMap(raw) {
  const status = $("#ask-status"), box = $("#ask-answer");
  const p = parseQuestion(raw);
  if (p.atividadeNaoCatalogada && !p.tipos.size) {
    const regiao = p.raNome ? ` na região ${esc(p.raNome)}` : "";
    const dica = `Não encontrei ${esc(p.atividadeNaoCatalogada)} cadastrado${regiao} na base atual. A base do PontoAtivo não possui registros específicos dessa modalidade; por isso não vou substituir a resposta por parques ou quadras de outro tipo.`;
    box.innerHTML = `<div class="ask-understood">Entendi: atividade: <b>${esc(p.atividadeNaoCatalogada)}</b>${p.raNome ? ` · região: <b>${esc(p.raNome)}</b>` : ""}</div><p>${dica}</p>`;
    box.hidden = false;
    status.textContent = "";
    lastAnswerText = dica;
    return;
  }

  const query = norm(raw);
  const gratis = /\b(gratis|gratuit[oa]s?|sem custo)\b/.test(query);
  const luz = /\b(iluminad[oa]s?|com iluminacao)\b/.test(query);
  const bom = /\b(em bom estado|bem conservad[oa]s?)\b/.test(query);
  // Piso do campo: só o cadastro de mobiliário da IDE-DF informa ("Campo sintético",
  // "Campo de terra batida"); os demais campos não entram nesse filtro.
  const piso = pisoDaPergunta(query);

  // Ponto de referência: endereço > bairro > minha localização
  let ref = null, refFrom = "";
  if (p.endereco) {
    ref = await geocode([p.endereco, p.bairro || p.raNome].filter(Boolean).join(", "));
    if (!ref) ref = localAddress(p.endereco, p.ras);
    if (ref) refFrom = "endereco";
  }
  if (!ref && p.bairro) { ref = await geocode(p.bairro); if (ref) refFrom = "bairro"; }
  if (!ref && p.pertoDeMim) {
    status.textContent = "Pedindo sua localização ao navegador…";
    const me = await getMyPosition();
    if (me) { ref = { pos: me, label: "sua localização" }; refFrom = "me"; }
  }

  if (!ref && askSetPos) { userPos = null; askSetPos = false; } // não herda o endereço da pergunta anterior
  const tipos = p.tipos.size ? p.tipos : new Set(ORDER);
  let list = LOCAIS.filter((r) => r.lat != null && tipos.has(r.t) &&
    (!p.pcd || r.acc?.adaptado || r.evidence?.accessibility_attributes?.adapted_equipment?.value) &&
    (!gratis || r.gratis) && (!luz || r.luz === true) && (!bom || norm(r.cons) === "bom") &&
    (!piso || norm(r.n).includes(piso.chave)));
  let raio = null;
  let totalNoDf = 0;
  let locaisNoDf = [];
  if (ref) {
    list = list.map((r) => ({ ...r, dist: km(ref.pos, [r.lat, r.lon]) })).sort((a, b) => a.dist - b.dist);
    raio = list.length && list[0].dist > 5 ? null : 5;
    const perto = raio ? list.filter((r) => r.dist <= raio) : list;
    list = (perto.length >= 3 ? perto : list).slice(0, 8);
  } else if (p.ras.length) {
    list = sortList(list.filter((r) => p.ras.includes(r.ra))).slice(0, 8);
  } else if (list.length <= 15) {
    list = sortList(list); // poucos locais no DF todo (ex.: Centros Olímpicos, paradesporto): mostra todos
  } else if (p.tipos.size && !p.endereco && !p.pertoDeMim) {
    locaisNoDf = sortList(list);
    totalNoDf = locaisNoDf.length;
    list = locaisNoDf.slice(0, 8);
  } else {
    list = [];
  }

  // O que foi entendido (transparência)
  const entendi = [
    p.tipos.size ? `<span>Tipo: <b>${esc(ORDER.filter((t) => p.tipos.has(t)).map((t) => TYPES[t].short).join(", "))}</b></span>` : `<span>Tipo: <b>todos</b></span>`,
    piso ? `<span>Piso: <b>${esc(piso.nome)}</b></span>` : "",
    p.raNome ? `<span>Região: <b>${esc(p.raNome)}</b>${p.bairro && norm(p.bairro) !== norm(p.raNome) ? ` (${esc(p.bairro)})` : ""}</span>` : "",
    p.endereco ? `<span>Endereço: <b>${esc(p.endereco.toUpperCase())}</b>${refFrom === "endereco" ? "" : " <em>(não localizado)</em>"}</span>` : "",
    refFrom === "me" ? "<span>Referência: <b>sua localização</b></span>" : "",
  ].filter(Boolean).join("");

  if (!list.length) {
    const dica = !p.raNome && !ref
      ? "Diga a região ou o endereço (ex.: “PEC na Ceilândia, QNN 12”) ou peça “perto de mim”."
      : "Não achei esse tipo de local com esses critérios. Tente outro tipo ou uma região vizinha.";
    box.innerHTML = `<div class="ask-understood">Entendi: ${entendi}</div><p>${dica}</p>`;
    box.hidden = false; status.textContent = ""; lastAnswerText = dica;
    // Sem resultado, o filtro de piso da pergunta anterior não fica preso ao mapa.
    if (PISOS.some((x) => x.nome === $("#f-q").value)) { $("#f-q").value = ""; update(); }
    return;
  }

  const oque = p.tipos.size ? ORDER.filter((t) => p.tipos.has(t)).map((t) => TYPES[t].short).join(", ") : "locais";
  const onde = ref ? (refFrom === "me" ? "perto de você" : `perto de ${ref.label}`) : p.raNome ? `em ${p.raNome}` : "no DF";
  const titulo = `${plural(totalNoDf || list.length, "opção", "opções")} de ${oque} ${onde}` + (ref ? (raio ? `, até ${raio} km, da mais próxima para a mais distante` : ", da mais próxima para a mais distante") : "");
  const from = ref && refFrom !== "me" ? ref.pos : null; // "minha localização": o app de rota usa o GPS na hora
  box.innerHTML = `
    <div class="ask-understood">Entendi: ${entendi}</div>
    <div class="ask-head"><h4>${esc(titulo)}</h4><button type="button" class="ask-speak" id="ask-speak">Ouvir resposta</button></div>
    ${totalNoDf ? `<p>Mostrando ${list.length} opções. Veja as demais no mapa ou indique uma região para refinar.</p>` : ""}
    <ol class="ask-list">${list.map((r) => `
      <li>
        <div class="ask-item-top"><b>${esc(r.n)}</b><span class="type-badge" style="background:${TYPES[r.t].color}">${TYPES[r.t].short}</span></div>
        <p class="meta">${[r.dist != null ? `${r.dist.toFixed(1).replace(".", ",")} km` : null, r.ra, r.end].filter(Boolean).map(esc).join(" · ")}${r.aprox ? " <em>(posição aproximada)</em>" : ""}</p>
        <div class="place-actions">${podeMarcarEncontro(r) ? `<button type="button" data-meeting-place="${esc(r.id)}">Marcar encontro</button>` : ""}<button type="button" data-ask-focus="${esc(r.id)}">Ver no mapa</button>${routeLinks(r, from)}</div>
      </li>`).join("")}
    </ol>
    <p class="src">Distância em linha reta. Dados do levantamento oficial (IDE-DF/SEL-DF): confirme no local antes de ir.</p>`;
  box.hidden = false;
  status.textContent = "";
  lastAnswerText = `${titulo}. ` + list.slice(0, 5).map((r, i) => `${i + 1}: ${r.n.replace("PEC – Ponto de Encontro Comunitário –", "PEC")}${r.dist != null ? `, a ${r.dist.toFixed(1).replace(".", ",")} quilômetros` : ""}.`).join(" ");

  // Sincroniza mapa e filtros com a resposta
  $$("#f-tipos input").forEach((i) => (i.checked = tipos.has(i.value)));
  $("#f-ra").value = ref ? "" : (p.ras[0] || "");
  $("#f-q").value = piso ? piso.nome : ""; // o mapa mostra os mesmos campos da lista
  $("#f-pcd").checked = p.pcd;
  $("#f-gratis").checked = gratis;
  $("#f-luz").checked = luz;
  $("#f-bom").checked = bom;
  if (ref) { userPos = ref.pos; askSetPos = true; }
  update();
  if (map) {
    if (refLayer) { refLayer.remove(); refLayer = null; }
    if (ref) refLayer = L.marker(ref.pos, { title: "Referência", icon: L.divIcon({ className: "", iconSize: [26, 26], iconAnchor: [13, 13], html: '<span class="mk-ref">★</span>' }) })
      .bindPopup(`Referência: ${esc(ref.label)}`).addTo(map);
    const pts = (totalNoDf ? locaisNoDf : list).map((r) => [r.lat, r.lon]).concat(ref ? [ref.pos] : []);
    map.fitBounds(pts, { padding: [40, 40], maxZoom: 16 });
  }
}

$("#ask-form").addEventListener("submit", (e) => { e.preventDefault(); ask($("#ask-q").value); });
$("#duv-form").addEventListener("submit", (e) => { e.preventDefault(); askDuvida($("#duv-q").value); });
$("#duv-q").addEventListener("input", syncDuvClear);
$("#duv-clear").addEventListener("click", clearDuvida);
$$(".duv-ex").forEach((b) => b.addEventListener("click", () => { $("#duv-q").value = b.textContent; askDuvida(b.textContent); }));
$("#ask-q").addEventListener("input", syncClearSearch);
$$(".ask-ex").forEach((b) => b.addEventListener("click", () => { $("#ask-q").value = b.textContent; ask(b.textContent); }));
$("#ask-answer").addEventListener("click", (e) => {
  const id = e.target.dataset && e.target.dataset.askFocus;
  if (id) return focusPlace(id);
  if (e.target.id === "ask-speak") {
    if (!("speechSynthesis" in window)) { e.target.textContent = "Leitura em voz indisponível"; return; }
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(lastAnswerText);
    u.lang = "pt-BR";
    speechSynthesis.speak(u);
  }
});

// Ditado por voz (Web Speech API). Sem suporte: orienta a digitar.
(function setupMic() {
  const btn = $("#ask-mic"), input = $("#ask-q"), status = $("#ask-status");
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    btn.addEventListener("click", () => { status.textContent = "Seu navegador não tem ditado por voz. Use Chrome, Edge ou Safari, ou digite a pergunta."; });
    return;
  }
  const rec = new SR();
  rec.lang = "pt-BR"; rec.interimResults = true; rec.maxAlternatives = 1; rec.continuous = false;
  let listening = false, finalText = "";
  const setOn = (on) => { listening = on; btn.classList.toggle("on", on); btn.setAttribute("aria-pressed", on); btn.setAttribute("aria-label", on ? "Parar de gravar" : "Falar a pergunta (gravar áudio)"); };
  btn.addEventListener("click", () => {
    if (listening) { rec.stop(); return; }
    finalText = ""; input.value = "";
    try { rec.start(); } catch { /* já iniciado */ }
  });
  rec.onstart = () => { setOn(true); status.textContent = "Ouvindo… fale sua pergunta. Toque no microfone de novo para parar."; };
  rec.onresult = (ev) => {
    let interim = "";
    for (let i = ev.resultIndex; i < ev.results.length; i++) {
      const tr = ev.results[i][0].transcript;
      if (ev.results[i].isFinal) finalText += tr; else interim += tr;
    }
    input.value = (finalText + interim).trim();
  };
  rec.onerror = (ev) => {
    setOn(false);
    status.textContent = ev.error === "not-allowed" || ev.error === "service-not-allowed"
      ? "Permissão do microfone negada. Libere o microfone no navegador ou digite a pergunta."
      : ev.error === "no-speech" ? "Não ouvi nada. Tente de novo, mais perto do microfone." : "Não consegui usar o ditado agora. Digite a pergunta.";
  };
  rec.onend = () => {
    const was = listening; setOn(false);
    if (was && input.value.trim()) { status.textContent = `Você disse: “${input.value.trim()}”`; ask(input.value); }
    else if (was && !status.textContent.startsWith("Não")) status.textContent = "";
  };
})();

// ---------- CTA ----------
$("#cta-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const email = $("#cta-email"), perfil = $("#cta-perfil"), msg = $("#cta-msg");
  if (!perfil.value) { msg.textContent = "Escolha seu perfil."; perfil.focus(); return; }
  if (!email.checkValidity() || !email.value) { msg.textContent = "Informe um e-mail válido."; email.focus(); return; }
  msg.textContent = "Obrigado! (Protótipo: nenhum dado foi enviado.)";
  e.target.reset();
});

// ---------- Moderação e Contribuição Comunitária (Etapa 7) ----------
const SUBMISSIONS_KEY = "pontoativo.contribuicoes.v1";

function getLocalSubmissions() {
  try {
    return JSON.parse(localStorage.getItem(SUBMISSIONS_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveLocalSubmission(sub) {
  const current = getLocalSubmissions();
  current.unshift(sub);
  localStorage.setItem(SUBMISSIONS_KEY, JSON.stringify(current));
  renderSavedContributions();
}

function renderSavedContributions() {
  const listEl = $("#c-saved-list");
  if (!listEl) return;
  const subs = getLocalSubmissions();
  if (!subs.length) {
    listEl.innerHTML = '<p class="meta">Nenhuma contribuição salva localmente ainda.</p>';
    return;
  }
  listEl.innerHTML = subs.map((s, idx) => `
    <div class="saved-item">
      <div>
        <strong>${esc(s.place_name || s.place_id)}</strong> · <small>${new Date(s.submitted_at).toLocaleString("pt-BR")}</small>
        <div><small>${s.kind === "accessibility" ? "Acessibilidade física" : "Informar mudança"}</small></div>
      </div>
      <span class="saved-badge">${s.status === "pending_review" ? "Pendente de revisão" : s.status}</span>
    </div>
  `).join("");
}

function openContributionModal(placeId, placeName) {
  const modal = $("#modal-contribuir");
  if (!modal) return;
  $("#c-place-id").value = placeId || "";
  $("#c-place-name").textContent = placeName ? `Local: ${placeName}` : "";
  $("#form-contribuir").reset();
  $("#c-form-msg").textContent = "";
  modal.hidden = false;
  renderSavedContributions();
  $("#c-notes").focus();
}

function closeContributionModal() {
  const modal = $("#modal-contribuir");
  if (modal) modal.hidden = true;
}

if ($("#btn-close-modal")) $("#btn-close-modal").addEventListener("click", closeContributionModal);
if ($("#btn-cancel-modal")) $("#btn-cancel-modal").addEventListener("click", closeContributionModal);

document.addEventListener("click", (e) => {
  const btn = e.target.closest && e.target.closest("[data-contribute-id]");
  if (btn) {
    openContributionModal(btn.dataset.contributeId, btn.dataset.contributeName);
  }
});

const formContrib = $("#form-contribuir");
if (formContrib) {
  formContrib.addEventListener("submit", (e) => {
    e.preventDefault();
    const consent = $("#c-consent").checked;
    const msg = $("#c-form-msg");
    if (!consent) {
      msg.textContent = "É obrigatório consentir com o envio das informações para moderação.";
      msg.style.color = "#b91c1c";
      return;
    }
    const placeId = $("#c-place-id").value;
    const placeName = $("#c-place-name").textContent.replace("Local: ", "");
    const kind = $("#c-kind").value;
    const notes = $("#c-notes").value.trim();

    const answers = {
      step_free_route: $('input[name="ans_rota"]:checked')?.value || "unknown",
      entry_barrier_free: $('input[name="ans_entrada"]:checked')?.value || "unknown",
      circulation: $('input[name="ans_circulacao"]:checked')?.value || "unknown",
      accessible_toilet: $('input[name="ans_banheiro"]:checked')?.value || "unknown",
      accessible_parking: $('input[name="ans_vaga"]:checked')?.value || "unknown",
      tactile_paving: $('input[name="ans_tatil"]:checked')?.value || "unknown",
    };

    const submission = {
      id: "sub-" + Date.now(),
      place_id: placeId,
      place_name: placeName,
      kind: kind,
      answers: answers,
      notes: notes,
      consent: true,
      status: "pending_review",
      level: "colaborativo",
      submitted_at: new Date().toISOString(),
    };

    saveLocalSubmission(submission);
    msg.textContent = "Contribuição gravada localmente com sucesso! Aguarda revisão do moderador.";
    msg.style.color = "#166534";
    setTimeout(() => {
      closeContributionModal();
    }, 1500);
  });
}

if ($("#btn-export-contributions")) {
  $("#btn-export-contributions").addEventListener("click", () => {
    const subs = getLocalSubmissions();
    if (!subs.length) {
      alert("Nenhuma contribuição salva para exportar.");
      return;
    }
    const blob = new Blob([JSON.stringify(subs, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `pontoativo-contribuicoes-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });
}

// ---------- Revelar ao rolar e botão topo ----------
const io = new IntersectionObserver((entries) => entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } }), { threshold: 0.12 });
$$(".step, .aud-card, .faq details, .trust-list li, .source").forEach((el) => { el.classList.add("reveal"); io.observe(el); });
const toTop = $(".to-top");
addEventListener("scroll", () => toTop.classList.toggle("show", scrollY > 600), { passive: true });

// ---------- Inicialização ----------
window.addEventListener("load", () => { initMap(); update(); });
// Abrir "Ver acessibilidade" dentro de um balão muda o tamanho dele: o balão se reajusta.
document.addEventListener("toggle", (e) => {
  if (!map || !e.target.closest || !e.target.closest(".leaflet-popup")) return;
  map.eachLayer((l) => { if (l.isPopupOpen && l.isPopupOpen()) l.getPopup().update(); });
}, true);
// O mapa pode nascer numa tela escondida: ao abrir a tela do mapa, ele recalcula o tamanho.
document.addEventListener("pa:tela", (e) => { if (e.detail === "mapa" && map) map.invalidateSize(); });

// Destaca o local da agenda mesmo quando a camada de agrupamentos está sendo atualizada.
let meetingFocusMarker = null;
window.PontoAtivoFocus = (id) => {
  const place = LOCAIS.find((r) => r.id === id);
  if (!map || !place || place.lat == null) return;
  if (window.PontoAtivoTelas.atual !== "mapa") window.PontoAtivoTelas.ir("mapa");
  clearTimeout(t);
  $("#filters").reset();
  update();
  if (meetingFocusMarker) { meetingFocusMarker.remove(); meetingFocusMarker = null; }
  map.stop();
  map.setView([place.lat, place.lon], 16, { animate: false });
  // Locais com encontros já têm pino fora dos agrupamentos: basta abrir o balão dele.
  const existing = markerById.get(id);
  if (existing && meetLayer.hasLayer(existing)) existing.openPopup();
  else {
    meetingFocusMarker = L.marker([place.lat, place.lon], { icon: icon(place), title: place.n })
      .addTo(map).bindPopup(popupHtml(place), popupOptions()).openPopup();
  }
  $("#map").scrollIntoView({ block: "center" });
};
