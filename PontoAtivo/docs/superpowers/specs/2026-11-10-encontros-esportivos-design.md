# Encontros esportivos no PontoAtivo

## Objetivo

Permitir que alguém escolha um local do mapa, marque um encontro esportivo e preencha as vagas com outras pessoas. Quem procura companhia pode filtrar encontros futuros e confirmar a participação.

## Experiência proposta

1. No cartão do local, a pessoa escolhe **Marcar encontro**. O formulário abre com o local já selecionado. A pessoa informa esporte, data, horário, nível e formato.
2. Os formatos são **dupla**, **trio** e **grupo**. A capacidade inclui quem criou o encontro. Dupla tem duas pessoas, trio tem três e grupo permite escolher de quatro a vinte. Níveis iniciais: iniciante, intermediário, avançado e todos os níveis.
3. Em **Encontros**, quem procura companhia pode filtrar por região, esporte, data, nível, faixa etária e formato. Cada cartão mostra local, horário e vagas restantes. A lista pode ser consultada sem conta. Criar ou participar exige login.
4. Quem entrou pode sair e liberar a vaga. Quem criou pode cancelar o encontro. Se precisar mudar horário ou local após a publicação, cancela e publica novamente nesta primeira versão.
5. **Minha agenda** reúne os encontros criados e aqueles em que a pessoa confirmou presença, inclusive quando são cancelados.

## Idade e informações públicas

O plano assume um piloto para maiores de 18 anos. A pessoa declara a faixa etária no perfil: 18–24, 25–34, 35–44, 45–59 ou 60+. Ao criar, pode escolher uma faixa aceita ou **Todos os adultos**. A API aplica essa escolha ao entrar e explica o motivo quando a faixa não corresponde. Os cartões mostram a faixa aceita, a contagem de participantes e o apelido de quem organizou. E-mail, telefone e data de nascimento ficam fora dos cartões. A elegibilidade no piloto se baseia em autodeclaração.

## Decisões de implementação

- O encontro referencia o identificador do local do cadastro. O servidor valida esse identificador contra um catálogo gerado a partir da mesma fonte do mapa.
- O horário é informado e exibido em Brasília. A API persiste o instante em UTC e rejeita datas passadas.
- A vaga é confirmada imediatamente em uma transação. A mesma pessoa ocupa uma vaga, inclusive se repetir o clique. Encontros lotados continuam visíveis com o status **Lotado**.
- O horário marca o encontro entre as pessoas. A interface informa que a combinação não reserva o espaço físico.
- O piloto local usa o servidor Python existente, SQLite em disco e sessões autenticadas. Testes com dois navegadores comprovam que as vagas são compartilhadas. O acesso por pessoas em redes diferentes requer uma implantação compartilhada com HTTPS e contas individuais.

## Abordagens consideradas

- Convite por link com horário e local. É simples de distribuir e atende grupos que já se conhecem, mas não oferece descoberta pública nem controle compartilhado de vagas.
- Agenda compartilhada com entrada imediata. Atende quem está procurando companhia e resolve o preenchimento de dupla, trio ou grupo com poucas etapas. É a proposta para o piloto.
- Solicitação de entrada com aprovação. Dá ao organizador controle de quem entra, ao custo de mais estados e espera. Pode ser avaliada depois de testar a agenda.
