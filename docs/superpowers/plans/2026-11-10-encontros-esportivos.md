# Plano de implementação de encontros esportivos

> **Para agentes:** executar tarefa por tarefa com `superpowers:executing-plans` ou `superpowers:subagent-driven-development`, conforme o modo de execução autorizado. Usar as caixas para acompanhar o trabalho.

**Objetivo** — Criar, descobrir e participar de encontros esportivos vinculados aos locais do PontoAtivo.

**Arquitetura** — A interface HTML/JS usa a API do servidor Python já existente. O servidor mantém perfis, sessões, encontros e participações em SQLite. A API atual de perguntas permanece disponível.

**Tecnologias** — Python, SQLite, HTML, CSS e JavaScript.

**Especificação** — [Encontros esportivos no PontoAtivo](../specs/2026-11-10-encontros-esportivos-design.md).

## 1. Persistência, catálogo e vagas

**Arquivos** — Criar `src/pontoativo_rag/encontros.py`, `tests/test_encontros.py` e `PontoAtivo-CURADORIA/ferramentas/exportar-locais-encontros.mjs`. Gerar `PontoAtivo-CURADORIA/data/locais-encontros.json` com ID, nome e região a partir de `data/locais.js`.

- [x] Escrever testes para local inexistente, horário passado, esporte vazio, capacidade inválida e faixa incompatível. Rodar o teste antes de implementar.
- [x] Implementar `criar_encontro(usuario_id, dados)`, `listar_encontros(filtros)`, `entrar(encontro_id, usuario_id)`, `sair(encontro_id, usuario_id)` e `cancelar(encontro_id, usuario_id)`. Guardar em SQLite os encontros, o estado, os perfis e as participações. Usar unicidade em (encontro, usuário) e a mesma transação para checar capacidade e inserir. Criar a participação do organizador na transação de criação.
- [x] Rodar testes para confirmar que dois pedidos simultâneos pela última vaga produzem uma confirmação e uma resposta de lotação. Cobrir clique repetido, liberação de vaga ao sair, cancelamento por terceiro, reentrada e persistência após reabrir o banco.
- [x] Conferir que cada ID exportado aparece uma única vez e que a listagem pode ser filtrada por região, esporte, data, nível, formato e faixa aceita.

## 2. Conta, perfil e API

**Arquivos** — Criar `src/pontoativo_rag/contas.py`, `tests/test_contas.py` e `tests/test_web_encontros.py`. Atualizar `src/pontoativo_rag/web.py` para ligar as rotas ao servidor.

- [x] Testar criação de conta, credenciais incorretas, sessão expirada, logout, tentativa de alterar encontro de outra pessoa e ausência de dados privados na resposta pública.
- [x] Implementar conta com apelido, identificador de login, senha armazenada como hash com salt e faixa etária adulta autodeclarada. Usar sessão com token aleatório em cookie HttpOnly e SameSite, com expiração e invalidação no logout. Usar cookie Secure na implantação HTTPS. Aplicar limite às tentativas de login e proteção contra requisições de outras origens nas operações de escrita.
- [x] Expor `POST /api/conta`, `POST /api/sessao`, `DELETE /api/sessao` e `GET /api/me`. Expor `GET /api/encontros`, `POST /api/encontros`, `GET /api/encontros/meus`, `PUT /api/encontros/{id}/participacao`, `DELETE /api/encontros/{id}/participacao` e `POST /api/encontros/{id}/cancelamento`.
- [x] Derivar o usuário da sessão e retornar erros legíveis para dados inválidos (400), sessão ausente (401), ação proibida (403), encontro inexistente (404) e lotação ou encerramento (409). Retornar vagas restantes e estado atualizado em cada alteração. Manter o banco fora dos arquivos estáticos servidos pelo navegador.
- [x] Rodar os testes da API e verificar também que `/api/perguntar` continua disponível.

## 3. Formulário, descoberta e agenda

**Arquivos** — Criar `PontoAtivo-CURADORIA/encontros.js`. Atualizar `index.html`, `styles.css` e os cartões de locais em `app.js`, todos em `PontoAtivo-CURADORIA/`.

- [x] Adicionar **Encontros** à navegação e **Marcar encontro** aos cartões do local na lista e na busca. Preencher o local ao abrir o formulário pelo cartão e permitir buscá-lo pelo nome ao abrir pelo menu.
- [x] Montar o formulário de esporte, data e hora de Brasília, nível, faixa etária e formato. Exibir o campo de capacidade quando o formato for grupo. Preservar o formulário ao pedir login e enviar apenas após confirmação da pessoa.
- [x] Mostrar cartões com os filtros, vagas restantes e ações **Participar**, **Sair do encontro** ou **Cancelar encontro**, conforme sessão e estado. Mostrar a agenda e distinguir encontros futuros, passados e cancelados.
- [x] Validar uso no celular e por teclado, foco após abrir e fechar formulário, mensagens de erro junto aos campos e anúncio de confirmação. Quando outra pessoa ocupar a última vaga, atualizar o cartão e mostrar **Lotado** sem perder os filtros.

## 4. Verificação do fluxo compartilhado

**Arquivos** — Atualizar `README.md` com instruções para rodar o piloto e testar duas contas.

- [x] Com a conta A, publicar uma dupla de futebol em um local do mapa. Em outro navegador, com a conta B, localizar o encontro com filtros e ocupar a segunda vaga. Verificar que outra conta recebe **Lotado**.
- [x] Sair com B, confirmar que a vaga reaparece e voltar a entrar com B. Cancelar com A e conferir o cancelamento na agenda de B e que novos participantes não conseguem confirmar.
- [x] Reiniciar o servidor e verificar que o estado persiste. Rodar `python -m pytest -q` e confirmar que os fluxos de mapa, busca e voz continuam acessíveis.
- [ ] Para liberar o uso entre pessoas de redes distintas, validar em uma implantação HTTPS com duas contas em dispositivos diferentes. Verificar persistência do banco e sessões nessa implantação antes da abertura do piloto.
