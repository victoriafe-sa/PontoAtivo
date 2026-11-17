# Estratégia de embeddings

O modelo é o `intfloat/multilingual-e5-base` (E5), que representa bem textos em
português e roda em computadores comuns. Até 17/11/2026 o projeto usava o
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (MiniLM); a troca e a
calibração estão descritas abaixo.

## Como os textos são codificados

O E5 foi treinado com prefixos: cada trecho dos documentos é codificado como
`passage: <texto>` e cada pergunta como `query: <pergunta>`. Sem os prefixos, a
qualidade da busca cai. A codificação é normalizada e feita em lotes, o que torna a
comparação por cosseno coerente. O modelo só é carregado na primeira codificação.

O ChromaDB guarda os vetores, o texto do segmento e os metadados do chunk-pai, na
coleção `pontoativo_e5_base_v1`. A coleção usa distância cosseno: valores menores
significam maior proximidade. Essa distância não é uma porcentagem de confiança nem
prova que uma afirmação seja verdadeira. A coleção registra o modelo que a criou, e o
sistema recusa misturar vetores de modelos diferentes.

Os IDs dependem do checksum e da posição. O `upsert` substitui o mesmo registro em vez
de duplicá-lo; uma mudança real no arquivo altera o checksum e os IDs derivados.

## Escala das distâncias e limiar de abstenção

Cada modelo espalha as distâncias numa escala própria. Nas mesmas fontes e perguntas:

| | MiniLM | E5 |
|---|---|---|
| Perguntas com resposta (melhor trecho) | 0,09 a 0,38 | 0,06 a 0,14 |
| Perguntas sem resposta (melhor trecho) | 0,46 a 0,72 | 0,15 a 0,21 |

Por isso o limiar de abstenção (`PONTOATIVO_MAX_DISTANCE`) depende do modelo, e os
valores da busca híbrida e da abstenção, medidos com o MiniLM, são multiplicados pela
escala do modelo (limiar ÷ 0,45):

- bônus da busca híbrida para termos da pergunta (até 0,12), nome da seção (0,10) e
  região administrativa (0,18);
- folgas da abstenção para trechos com muitos termos da pergunta (+0,25) ou da região
  pedida (+0,10).

Com o MiniLM a escala é 1 e nada muda. Com o E5 ela é 0,12 ÷ 0,45 ≈ 0,27. Sem essa
escala, os bônus pesavam mais que a semântica e o E5 acertava menos fontes (0,82 de
recall contra 0,97 do MiniLM), e o limiar de 0,45 fazia o sistema responder todas as
perguntas sem resposta.

## Calibração do E5 (17/11/2026)

Calibrado com 24 perguntas: as 15 com resposta (Q01–Q13, Q19, Q20), as 5 sem resposta
da avaliação (Q14–Q18) e as 4 fora do escopo da barra do mapa (R16–R19).

| Limiar | Recall@4 | Fonte certa | Recusa o que tem resposta | Responde sem base |
|---|---|---|---|---|
| 0,08 | 0,93 | 15/15 | Q12 | — |
| **0,09 a 0,145** | 0,89 a 0,94 | 15/15 | — | — |
| 0,15 | 0,89 | 15/15 | — | Q16 |
| 0,18 | 0,82 | 14/15 | — | 6 perguntas |

O limiar escolhido, **0,12**, fica no meio da faixa sem erros. Com 24 perguntas a
faixa é uma estimativa: qualquer mudança nas fontes, no chunking ou no modelo exige
repetir a calibração e o portão de qualidade (`python -m pontoativo_rag.avaliacao
--verificar-qualidade`).

## Portão de qualidade com o E5

Com o limiar 0,12 e o Gemma 4 12B, o portão completo passou em 17/11/2026
([relatório](../../experimentos/evidencias/referencia_gemma12b_e5.md)): recall@4 de 0,94, fonte certa
em todas as 13 perguntas com resposta, 5 de 5 abstenções corretas, nenhuma falsa
abstenção, nenhuma citação inválida, cobertura de citações e suporte factual de 1,00.

As duas rodadas anteriores falharam por uma afirmação cada, ambas na Q12, e cada falha
levou a uma correção com teste:

- "setor SQNW, como as quadras 108, 109 e 111" estava certa, mas a métrica ignorava
  números soltos; agora números de 3 dígitos ou mais contam como fatos (um número que
  não está na fonte conta contra a frase);
- "a Av. Rabelo" era cortada em duas frases no ponto de "Av."; o separador de frases
  agora reconhece abreviações de endereço e títulos (Av., Qd., Dra. etc.), também na
  resposta mostrada no site.

Comparação com o MiniLM nas mesmas perguntas: o MiniLM tem recall@4 de 0,97 e uma
faixa sem erros mais larga em relação à sua escala; o E5 calibrado tem recall@4 de 0,94
e também acerta a fonte das 15 perguntas. A indexação completa com o E5 leva cerca de
17 minutos num Mac M4, contra poucos minutos com o MiniLM.
