/* Encontros compartilhados. A sessão permanece em cookie HttpOnly. */
(() => {
  "use strict";
  const byId = (id) => document.getElementById(id);
  const section = byId("encontros");
  const list = byId("meeting-list");
  const filters = byId("meeting-filters");
  const dialog = byId("meeting-dialog");
  const form = byId("meeting-form");
  const authDialog = byId("meeting-auth-dialog");
  const authForm = byId("meeting-auth-form");
  const status = byId("meeting-status");
  const sportNames = [
    "Futebol", "Futsal", "Vôlei", "Vôlei de areia", "Basquete", "Tênis",
    "Beach tennis", "Futevôlei", "Caminhada", "Corrida", "Skate",
    "Exercícios no PEC", "Alongamento", "Natação", "Bocha paralímpica",
    "Goalball", "Atletismo", "Tênis em cadeira de rodas", "Basquete em cadeira de rodas",
  ];
  const labels = {
    iniciante: "Iniciante", intermediario: "Intermediário", avancado: "Avançado",
    todos: "Todos os níveis", dupla: "Dupla", trio: "Trio", grupo: "Grupo",
    aberto: "Aberto", lotado: "Lotado", cancelado: "Cancelado", passado: "Já começou",
  };
  const placeMap = new Map((window.PA_LOCAIS || []).map(p => [p.id, p]));
  const places = [...placeMap.values()];
  const normalize = text => text.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
  const dateFormat = new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo", day: "2-digit", month: "2-digit",
    year: "numeric", hour: "2-digit", minute: "2-digit",
  });
  let user = null;
  let mine = false;
  let register = false;
  let returnToCreate = false;
  let listVersion = 0;
  let creating = false;
  let publication = null;
  let appliedPrefsFor = null; // aplica as preferências uma vez por login, sem sobrepor escolhas feitas depois
  let adminLocal = false; // o servidor só libera o admin para quem abre o site no próprio computador
  const MAX_SPORTS = 5;

  function node(tag, text, className) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (className) element.className = className;
    return element;
  }

  function option(select, value, label) {
    const item = node("option", label);
    item.value = value;
    select.append(item);
  }

  async function api(path, {method = "GET", body} = {}) {
    const response = await fetch(path, {
      method, credentials: "same-origin",
      headers: body === undefined ? {} : {"Content-Type": "application/json"},
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!response.headers.get("content-type")?.includes("application/json")) {
      throw new Error("Abra o PontoAtivo pelo servidor de encontros para usar esta etapa.");
    }
    const result = await response.json();
    if (!response.ok) {
      if (response.status === 401) setUser(null);
      throw new Error(result.erro || "Não foi possível concluir a ação.");
    }
    return result;
  }

  function setUser(value) {
    user = value;
    byId("meeting-account-label").textContent = user
      ? "Sua conta · " + user.apelido
      : "Entre para organizar ou participar.";
    byId("meeting-login").hidden = Boolean(user);
    byId("meeting-account").hidden = Boolean(user);
    byId("account-menu").hidden = !user;
    byId("header-login").hidden = Boolean(user);
    if (user) {
      byId("account-name").textContent = user.apelido;
      byId("account-avatar").textContent = (user.apelido || "?").trim().charAt(0).toUpperCase();
      byId("account-btn").setAttribute("aria-label", "Menu da conta de " + user.apelido);
      byId("account-who-name").textContent = user.apelido;
      const prefs = user.preferencias || {};
      const info = [user.idade ? user.idade + " anos" : "", (prefs.esportes || []).join(", "), prefs.regiao || ""];
      byId("account-who-info").textContent = info.filter(Boolean).join(" · ");
    }
    document.querySelectorAll("[data-admin-login]").forEach(b => { b.hidden = !adminLocal || Boolean(user); });
    byId("meeting-logout").hidden = !user;
    byId("meeting-prefs").hidden = !user;
    if (!user) {
      // Ao sair, os filtros que vieram das preferências não ficam para a próxima pessoa.
      if (appliedPrefsFor) document.dispatchEvent(new CustomEvent("pa:preferencias-limpas"));
      appliedPrefsFor = null;
      byId("meeting-pref-note").hidden = true;
    }
  }

  // ---------- Preferências ----------
  function preferences() {
    return (user && user.preferencias) || {esportes: [], regiao: ""};
  }

  function fillPrefFields(fieldset, prefs) {
    const chosen = new Set(prefs.esportes);
    fieldset.querySelectorAll("[data-pref-sports] input").forEach(input => { input.checked = chosen.has(input.value); });
    fieldset.querySelector("[data-pref-region]").value = prefs.regiao || "";
    limitSports(fieldset);
  }

  function readPrefFields(fieldset) {
    return {
      esportes: [...fieldset.querySelectorAll("[data-pref-sports] input:checked")].map(input => input.value),
      regiao: fieldset.querySelector("[data-pref-region]").value,
    };
  }

  // Até 5 esportes: ao chegar no limite, os demais ficam indisponíveis.
  function limitSports(fieldset) {
    const inputs = [...fieldset.querySelectorAll("[data-pref-sports] input")];
    const full = inputs.filter(input => input.checked).length >= MAX_SPORTS;
    inputs.forEach(input => { input.disabled = full && !input.checked; });
  }

  function describePrefs(prefs) {
    return [prefs.regiao, prefs.esportes.join(", ")].filter(Boolean).join(" · ");
  }

  // Preenche os filtros dos encontros e avisa o mapa. Só pré-seleciona: nada é escondido sem aviso.
  function applyPreferences() {
    const prefs = preferences();
    const note = byId("meeting-pref-note");
    if (!user || appliedPrefsFor === user.id) return;
    appliedPrefsFor = user.id;
    if (!prefs.esportes.length && !prefs.regiao) {
      note.hidden = true;
      document.dispatchEvent(new CustomEvent("pa:preferencias-limpas"));
      return;
    }
    if (prefs.regiao && [...filters.elements.regiao.options].some(o => o.value === prefs.regiao)) {
      filters.elements.regiao.value = prefs.regiao;
    }
    // Um esporte vira filtro; com vários, os encontros desses esportes ganham destaque.
    filters.elements.esporte.value = prefs.esportes.length === 1 ? prefs.esportes[0] : "";
    note.replaceChildren(
      node("span", "Filtros das suas preferências: " + describePrefs(prefs) + ". "),
      Object.assign(node("button", "Ver todos os encontros"), {type: "button", id: "meeting-pref-clear"}),
    );
    note.hidden = false;
    document.dispatchEvent(new CustomEvent("pa:preferencias", {detail: prefs}));
  }

  function showAuth(forCreate = false) {
    returnToCreate = forCreate;
    byId("meeting-auth-status").textContent = "";
    authDialog.showModal();
  }

  function renderPlaces(query = "", chosen = "") {
    const select = byId("meeting-place");
    select.replaceChildren();
    option(select, "", "Selecione um local");
    const terms = normalize(query).split(/\s+/).filter(Boolean);
    const matches = places.filter(p => terms.every(t => normalize(p.n + " " + p.ra).includes(t)));
    const visible = matches.slice(0, 100);
    if (chosen && !visible.some(p => p.id === chosen) && placeMap.has(chosen)) {
      visible.unshift(placeMap.get(chosen));
    }
    for (const place of visible) option(select, place.id, place.n + " · " + (place.ra || "DF"));
    select.value = chosen;
  }

  function create(placeId) {
    if (creating) return;
    byId("meeting-form-status").textContent = "";
    if (placeId) {
      const place = placeMap.get(placeId);
      if (!place) return;
      byId("meeting-place-query").value = "";
      renderPlaces("", placeId);
    }
    if (!user) {
      showAuth(true);
      return;
    }
    dialog.showModal();
  }

  function eventCard(event) {
    const item = node("li", undefined, "meeting-card");
    const header = node("header");
    header.append(node("h3", event.esporte), node("span", labels[event.estado], "meeting-state meeting-state-" + event.estado));
    item.append(header);
    if (preferences().esportes.includes(event.esporte)) {
      item.classList.add("meeting-card-fav");
      item.append(node("p", "Um dos seus esportes", "meeting-fav"));
    }
    item.append(node("p", event.local.nome, "meeting-place-name"));
    item.append(node("p", event.local.regiao, "meta"));
    const time = node("time", dateFormat.format(new Date(event.inicio)) + " · Brasília");
    time.dateTime = event.inicio;
    item.append(time);
    // O aviso de feriado (BrasilAPI) chega depois, sem atrasar a lista.
    if (["aberto", "lotado"].includes(event.estado)) {
      const holiday = node("p", undefined, "meeting-holiday");
      holiday.hidden = true;
      item.append(holiday);
      markHoliday(event, holiday);
    }
    const age = event.idade === "todos" ? "Todos os adultos" : event.idade + " anos";
    item.append(node("p", [labels[event.formato], labels[event.nivel], age].join(" · "), "meta"));
    const bar = node("div", undefined, "meeting-bar meeting-bar-" + event.estado);
    bar.setAttribute("aria-hidden", "true");
    const fill = node("i");
    fill.style.width = Math.min(100, Math.round(100 * event.participantes / event.capacidade)) + "%";
    bar.append(fill);
    item.append(bar);
    item.append(node("p", event.participantes + "/" + event.capacidade + " pessoas · " + event.vagas + (event.vagas === 1 ? " vaga" : " vagas"), "meeting-vacancies"));
    const by = node("p", undefined, "meeting-by");
    by.append(node("span", (event.organizador || "?").trim().charAt(0).toUpperCase(), "meeting-avatar"),
      document.createTextNode("Organizado por " + event.organizador));
    by.firstChild.setAttribute("aria-hidden", "true");
    item.append(by);
    const actions = node("div", undefined, "place-actions");
    const future = ["aberto", "lotado"].includes(event.estado);
    if (event.meu && future) {
      actionButton(actions, "Cancelar encontro", "cancelamento", event.id);
    } else if (event.participando && future) {
      actionButton(actions, "Sair do encontro", "sair", event.id);
    } else if (event.estado === "aberto") {
      actionButton(actions, "Participar", "participacao", event.id);
    }
    if (event.participando) {
      const participation = event.meu ? "Você organizou este encontro."
        : event.estado === "cancelado" ? "O encontro em que você participaria foi cancelado."
        : event.estado === "passado" ? "Este encontro está na sua agenda."
        : "Sua presença está confirmada.";
      item.append(node("p", participation, "meeting-confirmed"));
    }
    const route = node("a", "Ver local no mapa", "meeting-map-link");
    route.href = "#place-" + event.local.id;
    route.dataset.meetingFocus = event.local.id;
    actions.append(route);
    item.append(actions);
    return item;
  }

  // ---------- Feriado do encontro (BrasilAPI, pelo servidor) ----------
  const dayKey = new Intl.DateTimeFormat("en-CA", {timeZone: "America/Sao_Paulo"});
  const holidaysByYear = new Map();

  function holidaysOf(year) {
    if (!holidaysByYear.has(year)) {
      holidaysByYear.set(year, api("/api/feriados?ano=" + year).then(r => r.feriados).catch(() => []));
    }
    return holidaysByYear.get(year);
  }

  async function markHoliday(event, holidayEl) {
    const day = dayKey.format(new Date(event.inicio));
    const holiday = (await holidaysOf(Number(day.slice(0, 4)))).find(h => h.data === day);
    if (!holiday) return;
    holidayEl.textContent = `Feriado: ${holiday.nome}. Confira se o local abre neste dia.`;
    holidayEl.hidden = false;
  }

  function actionButton(parent, text, action, id) {
    const button = node("button", text);
    button.type = "button";
    button.dataset.eventAction = action;
    button.dataset.eventId = id;
    parent.append(button);
  }

  // O mapa recebe todos os encontros futuros, sem os filtros da lista,
  // pelo evento "pa:encontros". Assim app.js não depende deste arquivo.
  let mapVersion = 0;
  async function syncMap() {
    const version = ++mapVersion;
    try {
      const result = await api("/api/encontros");
      if (version !== mapVersion) return;
      document.dispatchEvent(new CustomEvent("pa:encontros", {detail: {encontros: result.encontros}}));
    } catch {
      // Sem o servidor de encontros, o mapa continua funcionando sem os selos.
    }
  }

  async function refresh() {
    const version = ++listVersion;
    syncMap();
    byId("meeting-all").setAttribute("aria-pressed", String(!mine));
    byId("meeting-mine").setAttribute("aria-pressed", String(mine));
    if (mine && !user) {
      list.replaceChildren();
      status.textContent = "Entre para ver os encontros da sua agenda.";
      return;
    }
    list.setAttribute("aria-busy", "true");
    try {
      const query = new URLSearchParams(new FormData(filters));
      const result = await api((mine ? "/api/encontros/meus" : "/api/encontros") + "?" + query);
      if (version !== listVersion) return;
      list.replaceChildren(...result.encontros.map(eventCard));
      status.textContent = result.encontros.length
        ? result.encontros.length + (result.encontros.length === 1 ? " encontro encontrado." : " encontros encontrados.")
        : mine ? "Sua agenda ainda não tem encontros com esses filtros." : "Ainda não há encontros com esses filtros. Você pode marcar o primeiro.";
    } catch (error) {
      if (version === listVersion) status.textContent = error.message;
    } finally {
      if (version === listVersion) list.removeAttribute("aria-busy");
    }
  }

  for (const sport of sportNames) {
    option(byId("meeting-sport"), sport, sport);
    option(filters.elements.esporte, sport, sport);
  }
  const regions = [...new Set(places.map(p => p.ra).filter(Boolean))].sort((a, b) => a.localeCompare(b, "pt-BR"));
  for (const region of regions) option(filters.elements.regiao, region, region);
  document.querySelectorAll("[data-pref-fields]").forEach(fieldset => {
    const box = fieldset.querySelector("[data-pref-sports]");
    for (const sport of sportNames) {
      const label = node("label", undefined, "pref-sport");
      const input = Object.assign(document.createElement("input"), {type: "checkbox", name: "esportes", value: sport});
      label.append(input, document.createTextNode(" " + sport));
      box.append(label);
    }
    for (const region of regions) option(fieldset.querySelector("[data-pref-region]"), region, region);
    box.addEventListener("change", () => limitSports(fieldset));
  });
  const regFields = authForm.querySelector("[data-pref-fields]");
  regFields.disabled = true;
  renderPlaces();
  authForm.elements.apelido.disabled = true;
  authForm.elements.idade.disabled = true;
  byId("meeting-place-query").addEventListener("input", e => renderPlaces(e.target.value));
  byId("meeting-create").addEventListener("click", () => create());
  byId("meeting-login").addEventListener("click", () => showAuth());
  byId("header-login").addEventListener("click", () => showAuth());
  byId("meeting-all").addEventListener("click", () => { mine = false; refresh(); });
  byId("meeting-mine").addEventListener("click", () => {
    if (!user) { showAuth(); return; }
    mine = true;
    refresh();
  });
  byId("meeting-refresh").addEventListener("click", refresh);

  // ---------- Menu da conta no cabeçalho ----------
  const accountBtn = byId("account-btn");
  const accountPop = byId("account-pop");
  function openAccount(open) {
    accountPop.hidden = !open;
    accountBtn.setAttribute("aria-expanded", String(open));
  }
  accountBtn.addEventListener("click", () => openAccount(accountPop.hidden));
  accountPop.addEventListener("click", e => { if (e.target.closest("button")) openAccount(false); });
  document.addEventListener("click", e => { if (!e.target.closest("#account-menu")) openAccount(false); });
  document.addEventListener("keydown", e => {
    if (e.key === "Escape" && !accountPop.hidden) { openAccount(false); accountBtn.focus(); }
  });
  byId("account-agenda").addEventListener("click", () => {
    window.PontoAtivoTelas.ir("encontros");
    mine = true;
    refresh();
  });

  filters.addEventListener("change", () => { byId("meeting-pref-note").hidden = true; refresh(); });
  filters.addEventListener("submit", e => { e.preventDefault(); refresh(); });
  filters.addEventListener("reset", () => setTimeout(refresh, 0));
  form.elements.formato.addEventListener("change", () => {
    const group = form.elements.formato.value === "grupo";
    byId("meeting-capacity-label").hidden = !group;
    form.elements.capacidade.required = group;
    form.elements.capacidade.disabled = !group;
  });
  form.elements.capacidade.disabled = true;

  document.addEventListener("click", e => {
    const close = e.target.closest("[data-close-dialog]");
    if (close) close.closest("dialog").close();
    const button = e.target.closest("[data-meeting-place]");
    if (button) create(button.dataset.meetingPlace);
  });

  authDialog.addEventListener("close", () => {
    authForm.elements.senha.value = "";
    if (returnToCreate && user) { returnToCreate = false; create(); }
  });

  byId("meeting-auth-toggle").addEventListener("click", () => {
    register = !register;
    byId("meeting-registration").hidden = !register;
    authForm.elements.apelido.required = register;
    authForm.elements.idade.required = register;
    authForm.elements.apelido.disabled = !register;
    authForm.elements.idade.disabled = !register;
    regFields.disabled = !register;
    authForm.elements.senha.minLength = register ? 10 : 1;
    authForm.elements.senha.autocomplete = register ? "new-password" : "current-password";
    byId("meeting-auth-title").textContent = register ? "Criar conta" : "Entrar";
    byId("meeting-auth-submit").textContent = register ? "Criar conta" : "Entrar";
    byId("meeting-auth-toggle").textContent = register ? "Já tenho uma conta" : "Criar uma conta";
    byId("meeting-auth-status").textContent = "";
  });

  authForm.addEventListener("submit", async e => {
    e.preventDefault();
    const button = byId("meeting-auth-submit");
    button.disabled = true;
    byId("meeting-auth-status").textContent = "Conectando…";
    try {
      const body = Object.fromEntries(new FormData(authForm));
      if (register) Object.assign(body, readPrefFields(regFields));
      else delete body.esportes;
      const result = await api(register ? "/api/conta" : "/api/sessao", {method: "POST", body});
      setUser(result.usuario);
      authDialog.close();
      applyPreferences();
      await refresh();
    } catch (error) {
      byId("meeting-auth-status").textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });

  document.querySelectorAll("[data-admin-login]").forEach(button => button.addEventListener("click", async () => {
    button.disabled = true;
    try {
      setUser((await api("/api/sessao/admin", {method: "POST", body: {}})).usuario);
      if (authDialog.open) authDialog.close();
      applyPreferences();
      await refresh();
    } catch (error) {
      (authDialog.open ? byId("meeting-auth-status") : status).textContent = error.message;
    } finally {
      button.disabled = false;
    }
  }));

  byId("meeting-logout").addEventListener("click", async () => {
    try {
      await api("/api/sessao", {method: "DELETE"});
      setUser(null);
      mine = false;
      await refresh();
    } catch (error) { status.textContent = error.message; }
  });

  form.addEventListener("submit", async e => {
    e.preventDefault();
    if (creating) return;
    creating = true;
    const button = form.querySelector('[type="submit"]');
    button.disabled = true;
    byId("meeting-form-status").textContent = "Publicando…";
    try {
      const data = Object.fromEntries(new FormData(form));
      data.inicio += ":00-03:00";
      if (data.capacidade) data.capacidade = Number(data.capacidade);
      const payload = JSON.stringify(data);
      if (!publication || publication.payload !== payload) {
        publication = {id: crypto.randomUUID(), payload};
      }
      data.request_id = publication.id;
      await api("/api/encontros", {method: "POST", body: data});
      publication = null;
      dialog.close();
      form.reset();
      form.elements.capacidade.disabled = true;
      byId("meeting-capacity-label").hidden = true;
      byId("meeting-place-query").value = "";
      renderPlaces();
      mine = true;
      filters.reset();
      await refresh();
      status.textContent = "Encontro publicado. Sua presença está confirmada.";
      window.PontoAtivoTelas.ir("encontros");
      byId("meetings-title").focus({preventScroll: true});
    } catch (error) {
      byId("meeting-form-status").textContent = error.message;
      if (!user) { dialog.close(); showAuth(true); }
    } finally {
      creating = false;
      button.disabled = false;
    }
  });

  list.addEventListener("click", async e => {
    const focus = e.target.closest("[data-meeting-focus]");
    if (focus) {
      e.preventDefault();
      const placeId = focus.dataset.meetingFocus;
      const place = placeMap.get(placeId);
      if (place?.lat != null && window.PontoAtivoFocus) window.PontoAtivoFocus(placeId);
      else {
        window.PontoAtivoTelas.ir("encontros");
        status.textContent = "Esse local está com a localização exata pendente. Consulte o endereço no cadastro.";
      }
      return;
    }
    const button = e.target.closest("[data-event-action]");
    if (button) runAction(button);
  });

  // Botões "Participar" dentro dos balões e do painel de encontros do mapa.
  document.addEventListener("click", e => {
    const button = e.target.closest(".pop [data-event-action], .map-meet [data-event-action]");
    if (button) runAction(button, {fromMap: true});
  });

  async function runAction(button, {fromMap = false} = {}) {
    if (!user) { showAuth(); return; }
    button.disabled = true;
    const action = button.dataset.eventAction;
    const operation = action === "sair" ? "participacao" : action;
    const say = message => {
      status.textContent = message;
      // O balão é redesenhado pelo mapa; a mensagem vai pelo estado dele, não pelo DOM.
      if (fromMap) {
        document.dispatchEvent(new CustomEvent("pa:aviso-encontro", {
          detail: {eventId: button.dataset.eventId, text: message},
        }));
      }
    };
    try {
      await api("/api/encontros/" + button.dataset.eventId + "/" + operation, {
        method: action === "sair" ? "DELETE" : action === "participacao" ? "PUT" : "POST",
        body: action === "sair" ? undefined : {},
      });
      await refresh();
      say(action === "sair" ? "Você saiu. A vaga foi liberada."
        : action === "cancelamento" ? "Encontro cancelado." : "Sua presença está confirmada.");
      if (!fromMap) byId("meetings-title").focus({preventScroll: true});
    } catch (error) {
      const message = error.message;
      await refresh();
      say(message);
      button.disabled = false;
    }
  }

  const prefDialog = byId("pref-dialog");
  const prefForm = byId("pref-form");
  const prefFields = prefForm.querySelector("[data-pref-fields]");

  async function savePreferences(prefs) {
    byId("pref-status").textContent = "Salvando…";
    try {
      const result = await api("/api/conta/preferencias", {method: "PUT", body: prefs});
      user = {...user, preferencias: result.preferencias};
      appliedPrefsFor = null;
      filters.reset();
      prefDialog.close();
      applyPreferences();
      await refresh();
    } catch (error) {
      byId("pref-status").textContent = error.message;
    }
  }

  byId("meeting-prefs").addEventListener("click", () => {
    fillPrefFields(prefFields, preferences());
    byId("pref-status").textContent = "";
    prefDialog.showModal();
  });
  prefForm.addEventListener("submit", e => { e.preventDefault(); savePreferences(readPrefFields(prefFields)); });
  byId("pref-clear").addEventListener("click", () => savePreferences({esportes: [], regiao: ""}));
  byId("meeting-pref-note").addEventListener("click", e => {
    if (e.target.id !== "meeting-pref-clear") return;
    byId("meeting-pref-note").hidden = true;
    filters.reset();
    document.dispatchEvent(new CustomEvent("pa:preferencias-limpas"));
  });

  async function initialize() {
    try {
      const me = await api("/api/me");
      adminLocal = Boolean(me.admin_local);
      setUser(me.usuario);
    }
    catch (error) { status.textContent = error.message; return; }
    applyPreferences();
    await refresh();
  }
  initialize();
  setInterval(() => {
    if (!document.hidden && !dialog.open && !authDialog.open && !prefDialog.open) refresh();
  }, 30000);
})();
