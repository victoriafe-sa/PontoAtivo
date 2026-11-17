/* PontoAtivo – navegação por telas.
 * Cada <section data-tela="..."> pertence a uma tela: inicio, mapa, encontros ou duvidas.
 * O endereço decide a tela: #mapa, #encontros e #duvidas abrem a tela de mesmo nome;
 * um link para qualquer elemento (#pergunte, #fontes...) abre a tela que o contém e
 * rola até ele. Elementos fora das telas (#topo, #conteudo) não trocam a tela.
 * Avisa as outras partes com o evento "pa:tela" (detail = nome da tela).
 */
(() => {
  const screens = [...document.querySelectorAll("[data-tela]")];
  const names = new Set(screens.map((s) => s.dataset.tela));
  const navLinks = [...document.querySelectorAll("a[data-nav-tela]")];
  let current = null;

  function show(name) {
    if (name === current) return false;
    current = name;
    screens.forEach((s) => { s.hidden = s.dataset.tela !== name; });
    document.body.dataset.telaAtual = name;
    navLinks.forEach((a) => {
      if (a.dataset.navTela === name) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
    document.dispatchEvent(new CustomEvent("pa:tela", { detail: name }));
    return true;
  }

  // Ao trocar de tela, pula direto para o ponto certo, sem rolagem animada.
  const top = () => scrollTo({ top: 0, behavior: "instant" });
  const reach = (el) => el.scrollIntoView({ block: "start", behavior: "instant" });

  // Abre a tela de um id (sem "#") e rola até ele.
  function go(id) {
    if (!id || id === "inicio") { show("inicio"); top(); return; }
    if (names.has(id)) { show(id); top(); return; }
    const target = document.getElementById(id);
    const screen = target && target.closest("[data-tela]");
    if (screen) {
      const name = screen.dataset.tela;
      show(name);
      // A primeira seção de uma tela começa no topo; as outras (#fontes, #faq...) rolam até elas.
      if (target === screens.find((s) => s.dataset.tela === name)) top();
      else reach(target);
      return;
    }
    if (current === null) show("inicio");
    if (id === "topo") top();
    else if (target) reach(target);
  }

  const fromHash = () => {
    let id = location.hash.slice(1);
    try { id = decodeURIComponent(id); } catch { /* fica como veio */ }
    go(id);
  };

  addEventListener("hashchange", fromHash);
  // Clicar de novo no link da tela atual não muda o endereço: volta ao começo dela.
  document.addEventListener("click", (e) => {
    const link = e.target.closest('a[href^="#"]');
    if (link && link.getAttribute("href") === location.hash) { e.preventDefault(); fromHash(); }
  });

  window.PontoAtivoTelas = {
    // Leva a pessoa a uma tela ou a um elemento dela, registrando no histórico.
    ir(id) {
      if (location.hash !== "#" + id) history.pushState(null, "", "#" + id);
      go(id);
    },
    get atual() { return current; },
  };

  fromHash();
})();
