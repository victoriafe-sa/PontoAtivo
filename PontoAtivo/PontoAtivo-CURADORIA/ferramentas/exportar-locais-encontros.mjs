import fs from "node:fs";
import vm from "node:vm";
const base = new URL("../", import.meta.url);
const scope = {window: {}};
vm.runInNewContext(fs.readFileSync(new URL("data/locais.js", base), "utf8"), scope);
const unique = new Map();
for (const {id, n, ra} of scope.window.PA_LOCAIS) {
  const place = {id, nome: n, regiao: ra || ""};
  if (unique.has(id) && JSON.stringify(unique.get(id)) !== JSON.stringify(place)) {
    throw new Error("ID associado a locais diferentes: " + id);
  }
  unique.set(id, place);
}
const places = [...unique.values()];
fs.writeFileSync(new URL("data/locais-encontros.json", base), JSON.stringify(places, null, 2) + "\n");
console.log(places.length + " locais exportados.");
