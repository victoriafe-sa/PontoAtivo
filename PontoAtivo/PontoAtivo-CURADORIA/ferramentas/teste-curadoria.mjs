const endpoint = process.env.CDP_ENDPOINT || "http://127.0.0.1:9334";

const targets = await (await fetch(`${endpoint}/json`)).json();
const page = targets.find((target) => target.type === "page");
if (!page) throw new Error("Nenhuma página do Chrome disponível para o teste");

const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  ws.onopen = resolve;
  ws.onerror = reject;
});

let sequence = 0;
const pending = new Map();
const errors = [];
ws.onmessage = ({ data }) => {
  const message = JSON.parse(data);
  if (message.id && pending.has(message.id)) {
    const request = pending.get(message.id);
    pending.delete(message.id);
    return message.error
      ? request.reject(new Error(JSON.stringify(message.error)))
      : request.resolve(message.result);
  }
  if (message.method === "Runtime.exceptionThrown") {
    errors.push(message.params.exceptionDetails.text);
  }
  if (message.method === "Log.entryAdded" && message.params.entry.level === "error") {
    errors.push(message.params.entry.text);
  }
};

const send = (method, params = {}) => new Promise((resolve, reject) => {
  const id = ++sequence;
  pending.set(id, { resolve, reject });
  ws.send(JSON.stringify({ id, method, params }));
});

await send("Runtime.enable");
await send("Log.enable");
await send("Page.enable");
await send("Page.navigate", { url: "http://localhost:5173/?teste=curadoria" });

for (let index = 0; index < 50; index += 1) {
  const state = await send("Runtime.evaluate", {
    expression: "document.readyState",
    returnByValue: true,
  });
  if (state.result.value === "complete") break;
  await new Promise((resolve) => setTimeout(resolve, 100));
}

const expression = `(async () => {
  localStorage.removeItem("pontoativo.contribuicoes.v1");
  const places = window.PA_LOCAIS || [];
  const officialUnknown = places.find((place) =>
    place.t === "cop" &&
    place.evidence &&
    place.evidence.accessibility_attributes &&
    Object.values(place.evidence.accessibility_attributes).some((item) => item.level === "desconhecido")
  );
  const privatePlace = places.find((place) => place.ownership === "private");
  const representativePark = places.find((place) =>
    place.t === "parque" && place.aprox === true
  );
  const evidenceFilter = document.querySelector("#f-evidencia");
  const originFilter = document.querySelector("#f-origem input[value='private']");
  const contributionButton = document.querySelector("[data-contribute-id]");

  if (originFilter) {
    originFilter.checked = false;
    originFilter.dispatchEvent(new Event("input", { bubbles: true }));
  }
  if (evidenceFilter) {
    evidenceFilter.value = "campo";
    evidenceFilter.dispatchEvent(new Event("input", { bubbles: true }));
  }

  contributionButton?.click();
  const modal = document.querySelector("#modal-contribuir");
  const consent = document.querySelector("#c-consent");
  if (consent) consent.checked = true;
  document.querySelector("#form-contribuir")?.dispatchEvent(
    new Event("submit", { bubbles: true, cancelable: true })
  );
  await new Promise((resolve) => setTimeout(resolve, 50));
  const saved = JSON.parse(localStorage.getItem("pontoativo.contribuicoes.v1") || "[]");

  return {
    total: places.length,
    officialUnknown: Boolean(officialUnknown),
    privatePlace: Boolean(privatePlace),
    representativePark: Boolean(representativePark),
    originOptions: [...document.querySelectorAll("#f-origem input")].map((input) => input.value),
    evidenceOptions: [...document.querySelectorAll("#f-evidencia option")].map((option) => option.value),
    modalOpened: modal ? !modal.hidden : false,
    contribution: saved[0] || null,
    routes: places.filter((place) => place.lat != null).slice(0, 5).every((place) =>
      typeof place.lat === "number" && typeof place.lon === "number"
    ),
  };
})()`;

const evaluated = await send("Runtime.evaluate", {
  expression,
  awaitPromise: true,
  returnByValue: true,
});
const result = evaluated.result.value;

const checks = [
  [result.total === 1748, `esperava 1748 locais, recebeu ${result.total}`],
  [result.officialUnknown, "não encontrei atributo oficial com acessibilidade desconhecida"],
  [result.privatePlace, "não encontrei local privado na base"],
  [result.representativePark, "não encontrei parque com ponto representativo"],
  [result.originOptions.includes("private"), "filtro privado ausente"],
  [result.evidenceOptions.includes("campo"), "filtro de verificação em campo ausente"],
  [result.modalOpened, "modal de contribuição não abriu"],
  [result.contribution?.status === "pending_review", "contribuição não ficou pendente de revisão"],
  [result.contribution?.level === "colaborativo", "contribuição recebeu nível incorreto"],
  [result.routes, "há locais georreferenciados com coordenadas inválidas"],
  [errors.length === 0, `erros no navegador: ${errors.join(" | ")}`],
];

console.log(JSON.stringify({ ...result, erros: errors }, null, 2));
const failures = checks.filter(([ok]) => !ok).map(([, message]) => message);
ws.close();
if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log("TESTE_OK: curadoria, filtros, evidência, contribuição e coordenadas");
