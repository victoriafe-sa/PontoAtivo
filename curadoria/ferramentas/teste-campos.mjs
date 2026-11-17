const endpoint = process.env.CDP_ENDPOINT || "http://127.0.0.1:9334";

const targets = await (await fetch(`${endpoint}/json`)).json();
const page = targets.find((t) => t.type === "page");
if (!page) throw new Error("Nenhuma página do Chrome disponível para o teste");

const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  ws.onopen = resolve;
  ws.onerror = reject;
});

let seq = 0;
const pending = new Map();
const errors = [];
ws.onmessage = ({ data }) => {
  const msg = JSON.parse(data);
  if (msg.id && pending.has(msg.id)) {
    const { resolve, reject } = pending.get(msg.id);
    pending.delete(msg.id);
    return msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
  }
  if (msg.method === "Runtime.exceptionThrown") errors.push(msg.params.exceptionDetails.text);
  if (msg.method === "Log.entryAdded" && msg.params.entry.level === "error") errors.push(msg.params.entry.text);
};
const send = (method, params = {}) => new Promise((resolve, reject) => {
  const id = ++seq;
  pending.set(id, { resolve, reject });
  ws.send(JSON.stringify({ id, method, params }));
});

await send("Runtime.enable");
await send("Log.enable");
await send("Page.enable");
await send("Page.navigate", { url: "http://localhost:5173/?teste=campos" });

for (let i = 0; i < 50; i++) {
  const state = await send("Runtime.evaluate", { expression: "document.readyState", returnByValue: true });
  if (state.result.value === "complete") break;
  await new Promise((r) => setTimeout(r, 100));
}

const expression = `(async () => {
  const parsed = parseQuestion("campo de futebol em Taguatinga");
  await ask("campo de futebol em Taguatinga");
  return {
    totalCampos: LOCAIS.filter((r) => r.t === "campo").length,
    tipos: [...parsed.tipos],
    regiao: parsed.raNome,
    titulo: document.querySelector("#ask-answer h4")?.textContent,
    resultados: document.querySelectorAll("#ask-answer .ask-list > li").length,
    maps: document.querySelectorAll("#ask-answer .go-gmaps").length,
    waze: document.querySelectorAll("#ask-answer .go-waze").length,
    filtroCampo: document.querySelector('#f-tipos input[value="campo"]')?.checked,
    outrosFiltrosMarcados: [...document.querySelectorAll('#f-tipos input:not([value="campo"])')].filter((x) => x.checked).length,
    contagemMapa: document.querySelector("#results-count")?.textContent,
  };
})()`;
const evaluated = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
const result = evaluated.result.value;

const checks = [
  [result.totalCampos === 141, `esperava 141 campos, recebeu ${result.totalCampos}`],
  [JSON.stringify(result.tipos) === '["campo"]', `tipos interpretados: ${JSON.stringify(result.tipos)}`],
  [result.regiao === "Taguatinga", `região interpretada: ${result.regiao}`],
  [result.resultados > 0, "a busca não retornou resultados"],
  [result.maps === result.resultados, "nem todos os resultados têm Google Maps"],
  [result.waze === result.resultados, "nem todos os resultados têm Waze"],
  [result.filtroCampo === true && result.outrosFiltrosMarcados === 0, "o mapa não ficou filtrado apenas para campos"],
  [errors.length === 0, `erros no navegador: ${errors.join(" | ")}`],
];

console.log(JSON.stringify({ ...result, erros: errors }, null, 2));
const failures = checks.filter(([ok]) => !ok).map(([, message]) => message);
ws.close();
if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log("TESTE_OK: busca de campos, filtro, Google Maps e Waze");
