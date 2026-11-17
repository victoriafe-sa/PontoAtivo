# Estratégia de embeddings

O modelo inicial é
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Ele foi
escolhido porque representa semanticamente textos em português, tem tamanho
viável para computadores comuns e integra-se diretamente ao Python.

Tanto os segmentos dos documentos quanto as perguntas passam pelo mesmo
modelo. A codificação é normalizada e executada em lotes; isso torna a
comparação por cosseno coerente e reduz o custo de chamadas repetidas. O modelo
é carregado apenas quando a primeira codificação acontece.

O ChromaDB persiste localmente os vetores, o texto do segmento e os metadados
do chunk-pai. A coleção usa distância cosseno: valores menores significam maior
proximidade vetorial. Essa distância não é uma porcentagem de confiança nem
prova que uma afirmação seja verdadeira.

Os IDs dependem do checksum e da posição. O `upsert` substitui o mesmo registro
em vez de duplicá-lo, evitando recalcular ou acumular cópias quando uma fonte
não mudou. Uma mudança real no arquivo altera o checksum e, consequentemente,
os identificadores derivados.
