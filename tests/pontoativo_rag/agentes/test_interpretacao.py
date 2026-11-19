import unittest

from pontoativo_rag.agentes.interpretacao import AgenteInterpretacao


class TestInterpretacao(unittest.TestCase):
    def test_intencoes(self):
        casos = (
            ("Quais esportes existem em Brasília?", "pesquisar_esportes"),
            ("Quero conhecer atividades esportivas no DF.", "pesquisar_esportes"),
            ("Como faço meu cadastro?", "consultar_cadastro"),
            ("Quero realizar minha inscrição.", "consultar_cadastro"),
            ("Quero realizar minha INSCRICAO.", "consultar_cadastro"),
            ("Quais atividades são inclusivas?", "pesquisar_inclusao"),
            ("Quero saber sobre acessibilidade.", "pesquisar_inclusao"),
            ("Qual é a previsão do tempo?", "intencao_nao_identificada"),
        )
        agente = AgenteInterpretacao()
        for pergunta, intencao in casos:
            with self.subTest(pergunta=pergunta):
                self.assertEqual(agente.interpretar(pergunta), {
                    "status": "interpretado",
                    "pergunta_original": pergunta,
                    "acao_identificada": intencao,
                })

    def test_preserva_condicoes_ao_preparar_a_pesquisa(self):
        pergunta = "  Como faço inscrição para esportes inclusivos?  "
        self.assertEqual(AgenteInterpretacao().preparar_pesquisa(pergunta), {
            "consulta": pergunta.strip(),
            "pergunta_original": pergunta,
            "tipo": "pesquisar_esportes",
        })
