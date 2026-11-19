"""Verifica a moderação da consulta do protótipo."""

import unittest
from unittest.mock import patch

from prototipo.src import main


class TestConsultaPrototipo(unittest.TestCase):
    def test_termo_improprio_interrompe_antes_da_pesquisa(self):
        for pergunta in ("natacao gratuita e sexo", "quadra para esse idiota"):
            with self.subTest(pergunta=pergunta), patch.object(main, "buscar") as busca:
                with self.assertRaisesRegex(ValueError, "impróprio"):
                    main.consultar(pergunta, rascunho=True)
                busca.assert_not_called()
