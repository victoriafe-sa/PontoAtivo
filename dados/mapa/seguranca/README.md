# Segurança por Região Administrativa

`seguranca_ras_2025.json` alimenta o alerta de região dos encontros. Ele é gerado por
`scripts/gerar_seguranca_ras.py`, que baixa as planilhas listadas em `fontes_ssp_2025.tsv`.

## Fontes

- **Crimes:** SSP-DF, Balanço criminal de 2025 por RA, com dados pela data do fato
  e atualizados em 05/01/2026. Disponível em
  <https://www.ssp.df.gov.br/dados-por-regiao-administrativa/>.
- **População:** Codeplan/IPEDF, *Projeções populacionais para as Regiões
  Administrativas do Distrito Federal 2020-2030* (2022), Tabela A.1, ano de 2025.

## Indicador

O indicador soma crimes violentos letais intencionais (C.V.L.I.), roubo a transeunte e
estupro, e divide o total por 100 mil moradores.

Uma RA recebe o alerta quando a taxa dela é 1,5 vez a do DF ou mais. Em 2025, a taxa
do DF foi de 298 por 100 mil, e entraram no alerta Ceilândia (2,1 vezes) e SIA (5,0 vezes).

## Limites

- A taxa é calculada por morador. Regiões com muita gente de fora, como o SIA e o
  Plano Piloto, ficam com a taxa mais alta. O SIA tem cerca de 2,7 mil moradores.
- O número resume o ano inteiro da RA. Ele não diz nada sobre uma quadra, um parque
  ou um horário específico.
- As RAs criadas depois de 2022 (Arapoanga, Água Quente e outras) ainda não têm dados
  separados e ficam sem alerta.
- Para atualizar com um ano novo, troque os links em `fontes_ssp_2025.tsv` e a
  população no script, e rode o script de novo.
