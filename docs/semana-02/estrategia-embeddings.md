# Estratégia de embeddings

## Modelo escolhido

**`intfloat/multilingual-e5-base`**, usado pela biblioteca `sentence-transformers`.

| Característica | Valor |
|---|---|
| Dimensão dos vetores | 768 |
| Limite de entrada | 512 tokens (o que passar disso é cortado) |
| Idiomas | Multilíngue, com bom desempenho em português |
| Tamanho do modelo | cerca de 1 GB |
| Execução | Local, na CPU, sem chave de API e sem custo |

Código: `src/ingestao/embeddings.py`.

## Por que este modelo

- **Português:** toda a base de conhecimento e as consultas são em PT-BR. Um modelo treinado só em inglês (como o padrão do Chroma, `all-MiniLM-L6-v2`) recuperaria pior.
- **Cabe o chunk inteiro:** com a estratégia de chunking de 800 caracteres e 120 de sobreposição, cada chunk tem cerca de 200 tokens, bem abaixo do limite de 512. Modelos multilíngues populares como o `paraphrase-multilingual-MiniLM-L12-v2` cortam em 128 tokens e perderiam o final dos chunks.
- **Feito para busca:** a família E5 foi treinada para recuperação de informação (pergunta → trecho relevante), que é exatamente o uso no RAG.
- **Local e gratuito:** não depende de serviço externo nem de pagamento, e os textos não saem da máquina, o que está de acordo com o princípio de coleta mínima de dados (LGPD).

## Como usar

O módulo expõe duas funções:

```python
from ingestao.embeddings import gerar_embeddings, embedding_da_consulta

vetores = gerar_embeddings(lista_de_chunks)   # na ingestão: um vetor por chunk
vetor = embedding_da_consulta("pergunta")      # na busca: um vetor para a pergunta
```

Ambas devolvem listas de `float`, prontas para gravar no banco vetorial.

### Prefixos

O modelo E5 espera um prefixo que indica o papel do texto:

- `passage: ` antes de cada chunk indexado;
- `query: ` antes da pergunta do usuário.

As funções já aplicam os prefixos. Quem chama passa o texto puro.

### Métrica de similaridade

Os vetores são **normalizados** (comprimento 1). Assim, a similaridade de cosseno, que mede o ângulo entre os vetores, é igual ao produto escalar. No banco vetorial deve ser usada a **métrica de cosseno**, configurada ao criar a coleção (o Chroma usa distância euclidiana por padrão; a forma exata de configurar depende da versão instalada).

### Recuperação por top-k, não por limiar fixo

Com este modelo, as similaridades ficam concentradas numa faixa alta (por volta de 0,8 a 0,9), mesmo entre textos pouco relacionados. Por isso a busca deve retornar os **k chunks mais próximos** em vez de filtrar por um valor fixo de similaridade.

## Validação

`tests/teste_embeddings.py` testa o modelo sem banco vetorial: 5 trechos de exemplo sobre espaços esportivos do DF e 5 perguntas formuladas com palavras diferentes das usadas nos trechos (por exemplo, "natação" para encontrar "piscina").

Resultado: **5 de 5 perguntas recuperaram o trecho esperado**, com similaridade entre 0,85 e 0,87.

```bash
.venv/bin/python tests/teste_embeddings.py
```

O teste é pequeno e serve para confirmar que o modelo funciona. A avaliação da recuperação com a base completa fica para a demonstração (`docs/semana-02/demonstracao.md`).

## Instalação

```bash
python3 -m venv .venv
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements.txt
```

A primeira execução baixa o modelo (cerca de 1 GB).

## Limitações

- **Primeira execução lenta**, por causa do download do modelo.
- **CPU:** gerar embeddings de milhares de chunks pode levar alguns minutos sem GPU. É uma etapa feita uma vez na ingestão; a consulta é rápida.
- **Trocar de modelo exige refazer a base:** vetores de modelos diferentes não são comparáveis. Se o modelo mudar, todos os chunks precisam ser reprocessados.
- **Embeddings não verificam fatos:** o modelo encontra trechos parecidos com a pergunta, mas não sabe se a informação está correta ou atualizada. A confiabilidade continua dependendo das fontes e das datas de verificação registradas no catálogo.

## Alternativas consideradas

| Modelo | Por que não foi a escolha principal |
|---|---|
| `intfloat/multilingual-e5-small` | Mais leve (384 dimensões, cerca de 470 MB), com a mesma forma de uso. É a opção caso o computador da equipe não aguente o `base`. |
| `paraphrase-multilingual-MiniLM-L12-v2` | Corta a entrada em 128 tokens, menos que o tamanho dos chunks. |
| `all-MiniLM-L6-v2` (padrão do Chroma) | Treinado principalmente em inglês. |
| `BAAI/bge-m3` | Muito bom e aceita textos longos, mas é bem mais pesado (cerca de 2 GB), o que não compensa para chunks curtos. |
| Modelos via API (OpenAI, Voyage) | Exigem conta, chave e pagamento por uso, e enviam os textos para um serviço externo. |
