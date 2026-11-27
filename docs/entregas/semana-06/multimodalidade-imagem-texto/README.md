# Agente de imagem + análise de texto — PontoAtivo

O usuário fornece a imagem de um cartaz esportivo e uma pergunta em texto.
O agente de imagem transcreve o conteúdo visível; a Análise existente responde
à pergunta usando essa transcrição e a Validação revisa o rascunho antes da
publicação, com uma tentativa de correção a partir do parecer. A referência `[I1]` identifica a transcrição automática do cartaz,
não uma fonte oficial verificada.

## Escopo e integração

- Texto: pergunta em português, até 1.000 caracteres.
- Imagem: um PNG, JPEG ou WebP estático, até 5 MiB e 12 milhões de pixels.
- Extração: texto, legibilidade, atividades, horários, local, datas, contato e alertas.
- Campos ausentes são listas vazias; campos preenchidos são listas de passagens
  literais da transcrição. A transcrição preserva as relações entre atividades.
- Não usa a base vetorial nem associa automaticamente o cartaz a um local do mapa.
- Nesta etapa, execução por terminal e função Python. Upload na interface fica
  com a tarefa de integração; não está implementado nesta entrega técnica.

`AgenteImagem(cliente).extrair(bytes)` retorna a extração estruturada com hash
SHA-256 da imagem original e modelo utilizado. A imagem é decodificada,
orientada conforme EXIF e recodificada sem metadados antes do envio ao Ollama.
Não há persistência automática de uploads.

`responder_imagem(pergunta, bytes, agente=..., cliente_texto=...)` retorna
`modalidades`, `pergunta`, `extracao`, `avisos`, `modo`, `itens` e `resposta`.
Quando há revisão, também retorna `parecer`. Modos: `multimodal`, `abstencao`
e `falha_validacao`. A interface deve mostrar os avisos junto da resposta e
tratar `ImagemInvalida`, `ExtracaoInvalida` e `LLMUnavailable` como erros.
A abstenção por imagem ilegível não chama o agente de texto.

## Execução

Use Python 3.11 a 3.13 e o ambiente instalado conforme o README principal.
Atualize as dependências com `python -m pip install -r requirements.txt`.
Ollama deve estar acessível no endereço configurado, com um modelo de visão
instalado. O modelo textual continua definido por `PONTOATIVO_OLLAMA_MODEL`.

```bash
python scripts/gerar_cartaz_teste.py
python -m pontoativo_rag.agentes.multimodal \
  docs/entregas/semana-06/multimodalidade-imagem-texto/cartaz-teste.png \
  "Quais atividades acontecem pela manhã e onde?" \
  --modelo-imagem gemma4:12b
```

Pode-se definir `PONTOATIVO_OLLAMA_MODEL_IMAGEM` no ambiente ou `.env` em vez
do argumento. Escolha um modelo instalado que declare a capacidade `vision`.
O resultado JSON pode ser redirecionado para um arquivo como evidência, desde
que a imagem e a resposta não contenham dados pessoais reais.

O envio segue a [API de visão do Ollama](https://github.com/ollama/ollama/blob/main/docs/capabilities/vision.mdx):
imagem em base64 no campo `images` da mensagem. O fluxo de texto sem imagens
mantém o payload anterior.

## Limitações e mitigação

| Caso | Comportamento / mitigação |
|---|---|
| Arquivo falso, corrompido, animado ou acima dos limites | Rejeitar antes de chamar o modelo. |
| Texto desfocado ou cortado | Marcar leitura parcial/ilegível, não completar dados; pedir imagem melhor. A classificação depende do modelo. |
| Campo estruturado não aparece na transcrição | Rejeitar a extração. |
| JSON inválido ou truncado | Rejeitar a extração; não transformar saída bruta em resposta. |
| Pergunta sobre preço ou acessibilidade ausente | Análise deve retornar lacuna, sem concluir que é grátis ou inacessível. |
| Comandos escritos no cartaz | Prompt trata a imagem como dados; não há execução de comandos ou abertura de links. Não é garantia absoluta contra injeção. |
| Citação inventada ou conclusão reprovada | Validação bloqueia publicação do rascunho. |
| Ollama indisponível ou modelo sem visão | Erro explícito; não simular análise visual. |
| Cartaz antigo ou informação falsa | Exibir ressalva; leitura não autentica conteúdo nem confirma disponibilidade atual. |
| Erro visual que produz transcrição plausível | Pode passar pela validação textual: ela confere a transcrição, não os pixels. Conferência humana ainda é necessária. |

Não interpreta vídeos, PDFs ou áudio neste fluxo, não reconhece pessoas e não
certifica acessibilidade a partir da imagem. A mesma família de modelo pode
ser usada nos dois papéis; revisão não equivale a verificação independente.

## Verificação e demonstração

```bash
python -m pytest tests/pontoativo_rag/agentes tests/pontoativo_rag/test_geracao.py -q -m "not integration"
```

Os testes simulados verificam transporte da imagem, limites, conteúdo inválido,
contrato de extração, abstenção e passagem de evidência para o agente de texto.
Não medem acurácia visual. O cartaz de teste é sintético e não divulga um evento
real. Perguntas de demonstração:

1. “Quais atividades acontecem pela manhã e onde?” — futsal às 9h na Quadra Exemplo.
2. “Quanto custa participar?” — cartaz não informa o preço.
3. Uma imagem vazia — abstenção e solicitação de outra imagem.

A pessoa responsável pelos testes deve ampliar a avaliação para cartazes reais,
fontes pequenas, desfoque, corte, múltiplos horários e instruções adversariais.
A gravação final deve mostrar imagem, pergunta, transcrição, resposta e avisos.

### Falhas observadas durante a implementação

- O Ollama local rejeitou uma gramática gerada com `maxLength: 12000`.
  O limite de 12.000 caracteres permanece aplicado em Python após a resposta,
  sem esse parâmetro na gramática enviada ao modelo.
- O modelo juntou trechos não contíguos em uma única citação. A validação
  literal bloqueou a resposta; a instrução da Análise agora exige evidências
  separadas para passagens distantes. O teste de regressão preserva essa barreira.
- A fonte padrão do gerador de cartaz não renderizou acentos. O exemplo sintético
  foi corrigido para ASCII e inspecionado visualmente. Isso não representa uma
  avaliação de acurácia do modelo em cartazes com acentos.

A suíte direcionada foi executada com Python 3.13.18 e Pillow 12.3.0:
**119 testes e 8 subtestes aprovados**. O ambiente virtual antigo da máquina
apontava para um interpretador temporário ausente, então a verificação usou
um ambiente temporário separado, sem substituir o ambiente do projeto.

- Na integração inicial, avisos do sistema dentro dos metadados induziram o
  modelo a citá-los como fatos do cartaz, causando reprovação lexical. Os
  avisos agora são retornados separadamente das evidências. O registro
  `resultados/falha-avisos-como-evidencia.json` documenta essa falha intermediária.
