"""Verifica o contrato da Análise sem depender de modelos ou do banco vetorial."""

import json
from pathlib import Path
import sys
from unittest.mock import patch

import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "prototipo" / "src"))

from agentes.analise import analisar, analisar_duvidas
from main import consultar


class TestAnalise(unittest.TestCase):
    def test_termo_improprio_interrompe_antes_da_pesquisa(self):
        for pergunta in ("natacao gratuita e sexo", "quadra para esse idiota"):
            with self.subTest(pergunta=pergunta), patch("main.buscar") as busca:
                with self.assertRaisesRegex(ValueError, "impróprio"):
                    consultar(pergunta, rascunho=True)
                busca.assert_not_called()

    def test_consulta_curta_sem_evidencia(self):
        assert analisar("natacao gratuita", []) == "A Pesquisa não encontrou evidências para analisar."


    def test_rejeita_referencia_inventada(self):
        item = {"duvida": "É gratuito?", "estado": "sustentada",
                "conclusao": "A entrada é gratuita.", "trechos": ["outra-fonte"]}
        with patch("agentes.analise.OllamaClient.complete", return_value=json.dumps([item])):
            with self.assertRaisesRegex(RuntimeError, "referência inválida"):
                analisar_duvidas("Entrada gratuita?", [{"id": "F029-003", "texto": "Entrada: gratuita",
                                                        "metadados": {}}])

    def test_passagem_inventada_e_rejeitada(self):
        item = {"duvida": "É gratuito?", "estado": "sustentada",
                "conclusao": "É gratuito.", "trechos": ["F1"],
                "evidencias": [{"id": "F1", "passagem": "A aula é gratuita."}]}
        with patch("agentes.analise.OllamaClient.complete", return_value=json.dumps([item])):
            with self.assertRaises(RuntimeError):
                analisar_duvidas("A aula é gratuita?", [
                    {"id": "F1", "texto": "Entrada gratuita.", "metadados": {}}])

    def test_esclarecimento_sem_atribuir_local_da_busca(self):
        item = {"duvida": "É acessível?", "estado": "precisa_esclarecimento",
                "conclusao": "Qual local você quer visitar?", "trechos": [],
                "evidencias": []}
        with patch("agentes.analise.OllamaClient.complete", return_value=json.dumps([item])):
            self.assertEqual(analisar_duvidas("É acessível?", [
                {"id": "F1", "texto": "Parque acessível.", "metadados": {}}]), [item])

    def test_passagem_literal_aceita_quebra_de_linha(self):
        item = {"duvida": "Entrada gratuita?", "estado": "sustentada",
                "conclusao": "A entrada é gratuita.", "trechos": ["F1"],
                "evidencias": [{"id": "F1", "passagem": "Entrada gratuita."}]}
        with patch("agentes.analise.OllamaClient.complete", return_value=json.dumps([item])):
            self.assertEqual(analisar_duvidas("Entrada gratuita?", [
                {"id": "F1", "texto": "Entrada\n gratuita.", "metadados": {}}]), [item])

    def test_corrige_saida_invalida_para_modalidade_sem_evidencias(self):
        item = {"duvida": "Quadribol gratuito?", "estado": "lacuna",
                "conclusao": "Os trechos não permitem confirmar quadribol gratuito.",
                "trechos": [], "evidencias": []}
        with patch("agentes.analise.OllamaClient.complete",
                   side_effect=["[]", json.dumps([item])]) as modelo:
            resultado = analisar_duvidas("quadribol gratuito", [
                {"id": "F1", "texto": "Aulas de natação.", "metadados": {}}])
        self.assertEqual(resultado, [item])
        self.assertEqual(modelo.call_count, 2)
