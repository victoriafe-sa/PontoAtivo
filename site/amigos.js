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
    text.append(node("strong", pessoa.apelido));
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

    // Número de pedidos no menu da conta.
    const badge = byId("account-friends-badge");
    if (badge) {
      badge.textContent = data.pedidos.length || "";
      badge.hidden = !data.pedidos.length;
    }
  }

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
    if (Boolean(e.detail) !== logged || window.PontoAtivoTelas.atual === "amigos") load();
  });
  if (window.PontoAtivoTelas && window.PontoAtivoTelas.atual === "amigos") load();
})();
