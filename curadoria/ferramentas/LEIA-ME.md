# Como a base de locais foi montada (05/11/2026)

`site/data/locais.js` (o mapa publicado) veio de `build.py` a partir de:

1. **IDE-DF / SEDUH**: camadas *Mobiliário Esporte e Lazer* (layer 6) e *Parques Urbanos* (layer 7) do serviço
   `https://www.geoservicos.ide.df.gov.br/arcgis/rest/services/Publico/EQUIPAMENTOS_URBANOS/MapServer`.
   Os limites das RAs vêm de `.../Publico/LIMITES/MapServer/1`. Use `outSR=4326`, porque a consulta padrão sai em outra projeção.
2. **SEL-DF**: endereços dos 12 COPs (https://www.esporte.df.gov.br/cops) e espaços esportivos (https://www.esporte.df.gov.br/espacos-esportivos).
3. **Ibram**: tabela de Unidades de Conservação de ago/2026 (`ibram_parks.json`, extraída do PDF oficial).
4. **Paradesporto/UnB**: CETEFE (Agência Gov, Metrópoles) e Centro Olímpico da UnB.
5. **Campos de futebol complementares (opcional)**: arquivo `osm_pitches.json`, obtido da API
   Overpass/OpenStreetMap com `leisure=pitch` e `sport=soccer` dentro do DF. O gerador descarta
   locais privados, pisos de quadra e pontos a menos de 70 m de um campo/quadra já presente na
   IDE-DF. Sem esse arquivo, os 141 campos oficiais da IDE-DF continuam disponíveis normalmente.

As coordenadas dos locais nomeados vêm do OpenStreetMap/Nominatim (`geocode.py`, cache em `geocache.json`).
Cada ponto é conferido com o polígono oficial da RA (tolerância de 3 km na divisa). Quando o ponto cai fora,
o local fica sem pino e aparece como "localização pendente".

Para atualizar: baixe de novo as camadas da IDE-DF (`mob_*.json`, `parques.json`, `ras.json`) e rode
`python build.py <pasta_geo> ibram_parks.json ../data/locais.original-20261105.js`
(dentro de `curadoria/ferramentas`) e depois a curadoria abaixo.

---

# Importadores da IDE-DF (12/11 e 19/11/2026)

Dois importadores leem camadas oficiais da IDE-DF/SEDUH e gravam registros em
`data/curadoria/`, que `gerar_base.py` incorpora à base. Rode-os dentro de `curadoria/`
e depois publique a base (comando 3 abaixo).

| Importador | Camada | Saída | Resultado |
|---|---|---|---|
| `importar_espacos_comunitarios.py` | *Espaços comunitários* (layer 2) | `espacos_comunitarios.json` | 1.348 campos, quadras e praças que não estavam no mobiliário |
| `importar_parquinhos.py` | *Mobiliário Esporte e Lazer* (layer 6), tipo `PARQUE INFANTIL` | `parquinhos.json` | 798 parquinhos (de 812: 1 sem coordenada e 13 repetidos) |

```bash
python3 -B ferramentas/importar_parquinhos.py
python3 -B ferramentas/gerar_base.py --publish
```

Regras dos parquinhos:

- O tipo vem escrito de quatro jeitos (`PARQUE INFANTIL`, `PARQUE_INFANTIL`, com ou sem espaço no fim); todos viram `parquinho`.
- A região vem da poligonal oficial da RA; o endereço é padronizado (`Q2` vira `Q 2`, `QNG 7/ CNG 1` vira `QNG 7/CNG 1`).
- Registros a até 15 m, ou com o mesmo endereço a até 30 m, são o mesmo parquinho.
- O levantamento é de 2015/2017: cada registro traz a data e o aviso de confirmar no local.
- `reviewed_at` é a data da importação. Parquinhos ficam fora da agenda de encontros (maiores de 18 anos).

---

# Curadoria Multifonte (10/11/2026)

A base de dados é mantida e expandida com níveis de evidência por atributo através do pipeline de curadoria em `ferramentas/gerar_base.py`.

### Comandos de Curadoria e Testes:

1. **Executar testes automatizados (Python):**
   ```bash
   python3 -B -m unittest discover -s ferramentas/tests -v
   ```

2. **Gerar base candidata sem alterar a base publicada:**
   ```bash
   python3 -B ferramentas/gerar_base.py --output data/locais.candidato.js
   ```

3. **Publicar nova base com validação estrita e backup automático:**
   ```bash
   python3 -B ferramentas/gerar_base.py --publish
   ```
   *Nota: grava em `../site/data/locais.js` só se passar em 100% dos testes sem nenhum erro de validação. A base de entrada `data/locais.original-20261105.js` não é alterada. Depois, na raiz do projeto, rode `node curadoria/ferramentas/exportar-locais-encontros.mjs`.*

4. **Validar sintaxe JavaScript:**
   ```bash
   /System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc -e "checkSyntax('../site/app.js'); print('OK')"
   ```
