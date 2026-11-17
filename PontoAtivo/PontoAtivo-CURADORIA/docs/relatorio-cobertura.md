# Relatório de Cobertura e Curadoria Multifonte — PontoAtivo

**Data de referência:** 10/11/2026  
**Status da curadoria:** Etapas 1 a 7 implementadas e validadas; base candidata gerada com validação zero-error.

**Publicação (12/11/2026):** a candidata foi publicada em `data/locais.js` com
`python3 -B ferramentas/gerar_base.py --publish`. Antes, a base foi regenerada e
conferida byte a byte com `data/locais.candidato.js`. A base de 05/11/2026 segue
preservada em `data/locais.original-20261105.js`, e `data/locais-encontros.json`
foi reexportado (6 locais novos, nenhum removido). Motivo: a base anterior tinha
53 erros de validação e o `pqu-5` triplicado, e o próprio site já descrevia os
parques resolvidos, os clubes e o paradesporto da candidata.

---

## 1. Resumo Quantitativo Antes e Depois

| Métrica | Base Anterior (05/11/2026) | Base Curada / Candidata | Diferença | Observações |
|---|---|---|---|---|
| **Total de Registros** | 1.748 | 1.752 | +4 | A base anterior possuía o registro `pqu-5` duplicado 3 vezes (1.746 locais únicos). Foram adicionados 2 locais de paradesporto e 4 clubes privados, totalizando 1.752 locais únicos. |
| **Público (`public`)** | 1.747 | 1.746 | -1 | Correção de procedência e dedup de `pqu-5`. |
| **Organização Social (`social`)** | 1 | 1 | 0 | CETEFE atualizado institucionalmente. |
| **Privado (`private`)** | 0 | 5 | +5 | 4 clubes novos (`clube`) + Escola N. S. de Fátima (`private`, paradesporto). |
| **Locais sem pino / sem coordenadas** | 15 | 9 | -6 | 12 parques resolvidos com polígonos oficiais Ibram/ONDA. 7 locais sem procedência mantidos sem pino (CETEFE preserva ponto aproximado OSM). |
| **Alertas de Fontes >24 meses** | ~1.641 | 1.643 | +2 | Preservados como alertas transparentes de revisão, sem atualização artificial. |
| **Erros de Validação** | 53 | **0** | -53 | Todos os erros de datas e fontes obrigatórias foram corrigidos. |

---

## 2. Diagnóstico de Cobertura das PECs

- **No mapa:** 403 Pontos de Encontro Comunitário (PECs) georreferenciados no cadastro aberto da IDE-DF.
- **Divulgação oficial recente:** Novacap e Agência Brasília informaram em 04/11/2025 que o DF conta com *"mais de mil PECs"*.
- **Tratamento:** Não foi feita extrapolação fictícia nem inclusão de matérias de jornal sem localização precisa. Candidatos recentes constam em `data/curadoria/pecs_recentes.json`.
- **Minuta LAI:** Documento formal elaborado em `docs/pedido-lai-novacap.md` solicitando inventário aberto e georreferenciado à Novacap.

---

## 3. Parques e Espaços Pendentes

- **12 Parques Resolvidos:** Localizados geometricamente via serviço oficial do Brasília Ambiental (Ibram/ONDA) utilizando cálculo de ponto representativo interno em polígonos (inclusive côncavos). Exibidos na interface com a indicação *"ponto representativo da área do parque"*.
- **2 Parques em Revisão:** `ibram-8` (Parque Distrital Lobo Guará) e `ibram-46` (Parque Lagoinha), cujos polígonos não foram encontrados no serviço ONDA atual.
- **1 Ginásio:** Ginásio de Esportes de Samambaia (`sel-ginasio-samambaia`), mantido separadamente da contagem de parques, aguardando confirmação precisa de endereço da SEL-DF.

---

## 4. Paradesporto e Clubes Privados

- **Paradesporto:** CETEFE (endereço confirmado no site institucional; ponto aproximado OSM mantido; modalidades associadas às fontes), CECAF/DIREF (natação paralímpica via CPB) e Escola N. S. de Fátima (bocha paralímpica). Entidades como UNIACE e Candangos registradas na fila de revisão `data/curadoria/revisao.json`.
- **Privados:** Criada categoria específica `clube` no mapa e filtros. 4 clubes catalogados via site oficial (AABB Brasília, Clube Naval, Minas Brasília, Clube da Aeronáutica). Coordenadas sem comprovação geográfica foram retiradas da publicação (sem pino) e preservadas em `revisao.json`.

---

## 5. Modelo de Evidência e Participação Comunitária

- Cada atributo (endereço, coordenadas, acessibilidade física, modalidades) possui nível de confiança independente: `oficial`, `organizacao`, `colaborativo`, `campo`, `divergente`, `desconhecido`.
- Nenhuma informação declarada ou colaborativa é apresentada como vistoria em campo.
- Formulário comunitário implementado no protótipo com armazenamento local seguro (`localStorage`), consentimento obrigatório e exportação JSON para moderação.
