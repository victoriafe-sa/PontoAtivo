# Agente de Interpretação

O fluxo documental da web e do terminal executa Interpretação → Pesquisa →
Análise. Depois da moderação, a Interpretação identifica a intenção por palavras
inteiras, ignorando diferenças de acentuação e caixa.

| Intenção | Exemplos |
|---|---|
| `pesquisar_esportes` | Esportes, modalidades e atividades esportivas |
| `consultar_cadastro` | Cadastro e inscrição |
| `pesquisar_inclusao` | Inclusão e acessibilidade |
| `intencao_nao_identificada` | Perguntas sem palavras das categorias conhecidas |

Se houver termos de mais de uma categoria, vale a ordem da tabela. A Pesquisa
recebe a intenção no campo `tipo` e busca usando a pergunta completa. Perguntas
sem intenção reconhecida seguem para a busca documental. A Análise recebe a
pergunta original e as evidências, incluindo as fontes encontradas.
