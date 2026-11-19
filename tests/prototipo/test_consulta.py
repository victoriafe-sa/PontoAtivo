"""Verifica a moderação da consulta do protótipo."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

caminhos_originais = sys.path.copy()
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "prototipo" / "src"))
try:
    from main import consultar
finally:
    sys.path[:] = caminhos_originais


class TestConsultaPrototipo(unittest.TestCase):
    def test_termo_improprio_interrompe_antes_da_pesquisa(self):
        for pergunta in ("natacao gratuita e sexo", "quadra para esse idiota"):
            with self.subTest(pergunta=pergunta), patch("main.buscar") as busca:
                with self.assertRaisesRegex(ValueError, "impróprio"):
                    consultar(pergunta, rascunho=True)
                busca.assert_not_called()
