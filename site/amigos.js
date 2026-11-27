/* Tela Amigos: pessoas com quem você já praticou, pedidos de amizade,
 * notas anônimas ("gostei" / "não gostei") e bloqueios. */
(() => {
  "use strict";
  const byId = (id) => document.getElementById(id);
  const status = byId("friends-status");
  const content = byId("friends-content");
  const loginBox = byId("friends-login");
  const dateFormat = new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", day: "2-digit", month: "2-digit", year: "numeric" });
  let logged = false;

  function node(tag, text, className) {
    const el = document.createElement(tag);
    if (text !== undefined) el.textContent = text;
    if (className) el.className = className;
    return el;
  }

  function button(text, action, id, extra = {}) {
    const b = node("button", text, extra.className || "friend-btn");
    b.type = "button";
    b.dataset.friendAction = action;
    b.dataset.friendId = id;
    if (extra.pressed !== undefined) b.setAttribute("aria-pressed", String(extra.pressed));
    if (extra.label) b.setAttribute("aria-label", extra.label);
    return b;
  }

  async function api(path, method = "GET", body) {
    const response = await fetch(path, {
      method, credentials: "same-origin",
      headers: body === undefined ? {} : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(result.erro || "Não foi possível concluir a ação.");
      error.status = response.status;
      throw error;
    }
    return result;
  }

  function avatar(apelido) {
    return node("span", (apelido || "?").trim().charAt(0).toUpperCase(), "friend-avatar");
  }

  function personRow(pessoa, actions, detail) {
    const li = node("li", undefined, "friend-row");
    const who = node("div", undefined, "friend-who");
    who.append(avatar(pessoa.apelido));
    const text = node("div");
    const nome = node("button", pessoa.apelido, "friend-name");
    nome.type = "button";
    nome.dataset.friendProfile = pessoa.id;
    nome.setAttribute("aria-label", `Ver o perfil de ${pessoa.apelido}`);
    text.append(nome);
    if (detail) text.append(node("small", detail));
    who.append(text);
    const box = node("div", undefined, "friend-actions");
    box.append(...actions);
    li.append(who, box);
    return li;
  }

  function fill(list, items, empty) {
    list.replaceChildren(...(items.length ? items : [node("li", empty, "friend-empty")]));
  }

  function render(data) {
    const rep = data.reputacao;
    const faltam = rep.minimo - rep.total;
    byId("friends-rep").replaceChildren(
      node("strong", "Sua nota de quem praticou com você"),
      rep.nota
        ? node("span", `${String(rep.nota.media).replace(".", ",")} ★ · ${rep.nota.total} notas`)
        : node("span", rep.total ? `Faltam ${faltam} ${faltam === 1 ? "nota" : "notas"} para mostrar sua média` : "Você ainda não recebeu notas"),
      node("small", `A média só aparece a partir de ${rep.minimo} notas, para ninguém descobrir quem deu cada uma. Ela aparece também para quem vê seus encontros.`),
    );

    fill(byId("friends-requests"), data.pedidos.map((p) => personRow(p, [
      button("Aceitar", "aceitar", p.id, { className: "friend-btn friend-btn-main" }),
      button("Recusar", "remover", p.id),
    ], "Quer ser seu amigo")), "Nenhum pedido no momento.");

    fill(byId("friends-list"), data.amigos.map((p) => personRow(p, [
      button("Desfazer amizade", "remover", p.id),
    ])), "Você ainda não tem amigos aqui. Depois de praticar junto, adicione a pessoa abaixo.");

    fill(byId("friends-people"), data.pessoas.map((p) => {
      const quando = p.ultimo ? `${p.ultimo.esporte} em ${dateFormat.format(new Date(p.ultimo.inicio))}` : "";
      const vezes = p.encontros > 1 ? ` · ${p.encontros} encontros juntos` : "";
      const amizade = {
        nenhuma: button("Adicionar amigo", "pedir", p.id, { className: "friend-btn friend-btn-main" }),
        pedido_enviado: button("Cancelar pedido", "remover", p.id),
        pedido_recebido: button("Aceitar pedido", "aceitar", p.id, { className: "friend-btn friend-btn-main" }),
        amigos: node("span", "Amigos", "friend-tag"),
      }[p.amizade];
      const estrelas = node("span", undefined, "friend-stars");
      estrelas.setAttribute("role", "group");
      estrelas.setAttribute("aria-label", `Sua nota para ${p.apelido}`);
      for (let n = 1; n <= 5; n += 1) {
        const estrela = button("★", "nota", p.id, {
          pressed: p.minha_nota === n, className: "friend-star" + (n <= p.minha_nota ? " on" : ""),
          label: `${n} ${n === 1 ? "estrela" : "estrelas"} para ${p.apelido}`,
        });
        // Clicar de novo na nota atual tira a nota.
        estrela.dataset.nota = p.minha_nota === n ? "0" : String(n);
        estrelas.append(estrela);
      }
      const bloquear = button("Bloquear", "bloquear", p.id, { className: "friend-btn friend-btn-danger" });
      bloquear.dataset.friendName = p.apelido;
      return personRow(p, [amizade, estrelas, bloquear], `Praticaram: ${quando}${vezes}`);
    }), "Quando você participar de um encontro que já aconteceu, as pessoas que estavam lá aparecem aqui.");

    fill(byId("friends-blocked"), data.bloqueados.map((p) => personRow(p, [
      button("Desbloquear", "desbloquear", p.id),
    ])), "Ninguém bloqueado.");
    byId("friends-blocked-count").textContent = data.bloqueados.length ? ` (${data.bloqueados.length})` : "";

    applySearch();
    notifyRequests(data.pedidos);

    // Número de pedidos no menu da conta.
    const badge = byId("account-friends-badge");
    if (badge) {
      badge.textContent = data.pedidos.length || "";
      badge.hidden = !data.pedidos.length;
    }
  }

  // ---------- Busca pelo apelido ----------
  const search = byId("friends-search");
  const norm = (t) => t.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
  function applySearch() {
    const q = norm(search.value.trim());
    let shown = 0;
    content.querySelectorAll(".friend-row").forEach((row) => {
      const hit = !q || norm(row.querySelector(".friend-name").textContent).includes(q);
      row.hidden = !hit;
      if (hit) shown += 1;
    });
    content.querySelectorAll(".friend-empty").forEach((el) => { if (el.id !== "friends-search-empty") el.hidden = Boolean(q); });
    byId("friends-search-empty").hidden = !q || shown > 0;
  }
  search.addEventListener("input", applySearch);

  // ---------- Perfil ----------
  const profile = byId("friend-profile");
  const AMIZADE = { amigos: "Vocês são amigos", pedido_enviado: "Você pediu amizade", pedido_recebido: "Quer ser seu amigo", nenhuma: "" };
  async function openProfile(id) {
    const body = byId("friend-profile-body");
    byId("friend-profile-title").textContent = "Perfil";
    body.replaceChildren(node("p", "Carregando…", "friend-muted"));
    profile.showModal();
    try {
      const p = await api(`/api/amigos/${id}/perfil`);
      byId("friend-profile-title").textContent = p.apelido;
      const head = node("div", undefined, "friend-profile-head");
      head.append(avatar(p.apelido));
      const info = node("div");
      info.append(node("strong", p.apelido));
      const linha = [p.idade ? `${p.idade} anos` : "", p.regiao].filter(Boolean).join(" · ");
      if (linha) info.append(node("small", linha));
      if (AMIZADE[p.amizade]) info.append(node("span", AMIZADE[p.amizade], "friend-tag"));
      head.append(info);
      const nota = p.nota
        ? node("p", `★ ${String(p.nota.media).replace(".", ",")} · ${p.nota.total} notas de quem praticou`, "meeting-rating")
        : node("p", "Ainda sem média de estrelas (aparece a partir de 3 notas).", "friend-muted");
      const esportes = node("p", p.esportes.length ? "Esportes favoritos: " + p.esportes.join(", ") : "Sem esportes favoritos informados.", "friend-muted");
      const lista = node("ul", undefined, "friend-common");
      for (const e of p.encontros_em_comum) lista.append(node("li", `${e.esporte} · ${dateFormat.format(new Date(e.inicio))}`));
      body.replaceChildren(head, nota, esportes,
        node("h3", p.encontros_em_comum.length ? "Encontros juntos" : "Vocês ainda não praticaram juntos", "friends-h"),
        ...(p.encontros_em_comum.length ? [lista] : []));
    } catch (error) {
      body.replaceChildren(node("p", error.message, "friend-muted"));
    }
  }
  byId("amigos").addEventListener("click", (e) => {
    const b = e.target.closest("[data-friend-profile]");
    if (b) openProfile(b.dataset.friendProfile);
  });

  // ---------- Aviso de pedidos novos ----------
  // Só avisa pedidos de amizade. Notas novas não geram aviso: logo depois de um
  // encontro, o aviso entregaria quem deu a nota.
  let userId = null;
  const toast = byId("friend-toast");
  const seenKey = () => "pa-pedidos-vistos-" + userId;
  function readSeen() {
    try { return new Set(JSON.parse(localStorage.getItem(seenKey()) || "[]")); } catch { return new Set(); }
  }
  function saveSeen(ids) {
    try { localStorage.setItem(seenKey(), JSON.stringify([...ids])); } catch { /* sem armazenamento */ }
  }
  function notifyRequests(pedidos) {
    if (!userId) return;
    if (window.PontoAtivoTelas && window.PontoAtivoTelas.atual === "amigos") {
      saveSeen(pedidos.map((p) => p.id));
      toast.hidden = true;
      return;
    }
    const seen = readSeen();
    const novos = pedidos.filter((p) => !seen.has(p.id));
    if (!novos.length) return;
    byId("friend-toast-text").textContent = novos.length === 1
      ? `${novos[0].apelido} quer ser seu amigo.`
      : `${novos.length} pessoas querem ser suas amigas.`;
    toast.hidden = false;
  }
  byId("friend-toast-go").addEventListener("click", () => { toast.hidden = true; window.PontoAtivoTelas.ir("amigos"); });
  byId("friend-toast-close").addEventListener("click", () => { toast.hidden = true; });

  async function load() {
    try {
      const data = await api("/api/amigos");
      logged = true;
      loginBox.hidden = true;
      content.hidden = false;
      render(data);
    } catch (error) {
      if (error.status === 401) {
        logged = false;
        content.hidden = true;
        loginBox.hidden = false;
      } else {
        status.textContent = error.message;
      }
    }
  }

  const ROUTES = {
    pedir: (id) => api(`/api/amigos/${id}/pedido`, "POST", {}),
    aceitar: (id) => api(`/api/amigos/${id}/aceite`, "POST", {}),
    remover: (id) => api(`/api/amigos/${id}`, "DELETE"),
    nota: (id, b) => api(`/api/amigos/${id}/nota`, "PUT", { nota: Number(b.dataset.nota) }),
    bloquear: (id) => api(`/api/amigos/${id}/bloqueio`, "PUT", {}),
    desbloquear: (id) => api(`/api/amigos/${id}/bloqueio`, "DELETE"),
  };
  const MESSAGES = {
    pedir: "Pedido de amizade enviado.", aceitar: "Agora vocês são amigos.", remover: "Pronto.",
    nota: "Sua nota foi registrada. A pessoa não vê que foi você.", bloquear: "Pessoa bloqueada.", desbloquear: "Pessoa desbloqueada.",
  };

  byId("amigos").addEventListener("click", async (e) => {
    const b = e.target.closest("[data-friend-action]");
    if (!b) return;
    const action = b.dataset.friendAction;
    if (action === "bloquear" && !confirm(`Bloquear ${b.dataset.friendName}? Vocês deixam de ser amigos e não entram mais nos encontros um do outro.`)) return;
    b.disabled = true;
    try {
      await ROUTES[action](b.dataset.friendId, b);
      status.textContent = MESSAGES[action];
      await load();
      // Bloqueios mudam quais encontros aparecem: a agenda e o mapa se atualizam.
      if (action === "bloquear" || action === "desbloquear") document.dispatchEvent(new CustomEvent("pa:bloqueios"));
    } catch (error) {
      status.textContent = error.message;
    } finally {
      b.disabled = false;
    }
  });

  byId("friends-login-btn").addEventListener("click", () => byId("header-login")?.click());
  byId("account-friends").addEventListener("click", () => window.PontoAtivoTelas.ir("amigos"));
  // A tela carrega ao ser aberta e sempre que a pessoa entra ou sai da conta.
  document.addEventListener("pa:tela", (e) => { if (e.detail === "amigos") load(); });
  document.addEventListener("pa:conta", (e) => {
    userId = e.detail ? e.detail.id : null;
    if (!userId) toast.hidden = true;
    if (Boolean(e.detail) !== logged || window.PontoAtivoTelas.atual === "amigos") load();
  });
  if (window.PontoAtivoTelas && window.PontoAtivoTelas.atual === "amigos") load();
})();
