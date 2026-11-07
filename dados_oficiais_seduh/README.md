# Dados oficiais de localização — SEDUH / IDE-DF

Coleta feita em 2026-11-07 nas camadas públicas do Geoportal/IDE-DF (www.geoservicos.ide.df.gov.br):
- EQUIPAMENTOS_URBANOS/FeatureServer/2 (Espaços comunitários): 3 PECs (ec_tipo=3) e 1.997 registros de esporte (ec_tipo 2, 5, 7, 9, 10)
- EQUIPAMENTOS_URBANOS/FeatureServer/6 (Mobiliário esportivo/lazer): 2.458 registros, dos quais 403 do tipo PEC
- CADASTRO_TERRITORIAL/FeatureServer/1 (Campos e Quadras Poliesportivas): NÃO coletada, o servidor retornou erro 500

## Arquivos
- `pontoativo_bruto_seduh.json`: respostas originais da API, para auditoria
- `pontoativo_cadastro_seduh.csv` / `.jsonl`: 4.458 registros normalizados (separador `;`)
- `pontoativo_base_filtrada.csv`: 4.453 registros, com tipos unificados na coluna `grupo` e `coordenada_valida`

## Limites
- Coordenadas são o centro aproximado do polígono, não a entrada do local.
- Implantação e acessibilidade NÃO verificadas em nenhum registro.
- Os 3 PECs da camada Espaços comunitários estão previstos em projeto (ec_prev_projeto=1).
- ec_sit_fisica e ec_operacional são códigos sem legenda oficial; não interpretar.
- Camada única de uma instituição: não conta como documentos-fonte originais distintos.
