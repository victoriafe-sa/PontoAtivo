"""Verifica persistência de rodadas sem chamadas externas ou arquivos reais."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    'rodar_rag', Path(__file__).resolve().parents[1] / 'scripts/rodar_experimentos_rag.py')
rag = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rag)


class RegistrosRagTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.patch = patch.object(rag, 'BASE', self.base)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        (self.base / 'prompts').mkdir()
        (self.base / 'prompts/q1.txt').write_text('Pergunta de teste')

    def rodar(self, resposta=None, erro=None):
        with patch('sys.argv', ['script', '--modelo', 'llama', '--inicio', '1', '--fim', '1']), \
             patch.object(rag.urllib.request, 'urlopen', side_effect=OSError), \
             patch.object(rag, 'chamar_local', return_value=resposta, side_effect=erro):
            rag.main()

    def test_rodadas_preservam_historico_e_medem_ollama(self):
        rag.salvar_metricas({'pergunta_id': 'q1', 'status_metricas': 'nao_registradas'})
        historico = (self.base / 'metricas.csv').read_bytes()
        resposta = {'model': 'llama3.2:3b', 'message': {'content': 'Resposta'},
                    'prompt_eval_count': 20, 'eval_count': 10,
                    'eval_duration': 2_000_000_000, 'total_duration': 3_000_000_000,
                    'done_reason': 'stop'}
        self.rodar(resposta)
        self.rodar(resposta)
        assert (self.base / 'metricas.csv').read_bytes().startswith(historico)
        with (self.base / 'metricas.csv').open() as f:
            linhas = list(csv.DictReader(f))
        self.assertEqual(len(linhas), 3)
        self.assertNotEqual(linhas[1]['arquivo_bruto'], linhas[2]['arquivo_bruto'])
        for linha in linhas[1:]:
            self.assertEqual(linha['tokens_total'], '30')
            self.assertEqual(float(linha['tokens_por_s']), 5)
            self.assertEqual(float(linha['tempo_total_s']), 3)
            self.assertEqual(linha['tempo_carga_s'], '')
            self.assertTrue(linha['arquivo_bruto'].startswith('brutos/llama/rodada-'))
            d = json.loads((self.base / linha['arquivo_bruto']).read_text())
            self.assertEqual(d['saida'], resposta)
            self.assertTrue((self.base / d['ambiente_referencia']).exists())
            self.assertTrue((self.base / linha['arquivo_resposta']).exists())

    def test_falha_preserva_json_e_csv_sem_resposta_ficticia(self):
        with self.assertRaises(SystemExit):
            self.rodar(erro=TimeoutError())
        with (self.base / 'metricas.csv').open() as f:
            linha = next(csv.DictReader(f))
        self.assertEqual(linha['status_metricas'], 'falha')
        self.assertEqual(linha['tokens_saida'], '')
        self.assertEqual(linha['arquivo_resposta'], '')
        d = json.loads((self.base / linha['arquivo_bruto']).read_text())
        self.assertEqual(d['erro'], 'TimeoutError')

    def test_gemini_preserva_total_api_e_nao_inventa_tempo_geracao(self):
        registro = {'pergunta_id': 'q1', 'modelo': 'gemini-solicitado',
                    'provedor': 'gemini', 'inicio': '2026-11-12T10:00:00-03:00',
                    'tempo_cliente_segundos': 7, 'arquivo_bruto': 'brutos/teste.json',
                    'saida': {'model_version': 'gemini-retornado',
                              'usage_metadata': {'prompt_token_count': 20,
                                                 'candidates_token_count': 10,
                                                 'thoughts_token_count': 5,
                                                 'total_token_count': 35},
                              'candidates': [{'finish_reason': 'STOP'}]}}
        linha = rag.extrair_metricas(registro, {})
        self.assertEqual(linha['tokens_total'], 35)
        self.assertEqual(linha['modelo'], 'gemini-retornado')
        self.assertNotIn('tokens_por_s', linha)
        self.assertNotIn('tempo_geracao_s', linha)
        registro['saida'] = {}
        linha = rag.extrair_metricas(registro, {})
        self.assertEqual(linha['status_metricas'], 'parciais')
        self.assertIsNone(linha['tokens_saida'])


if __name__ == '__main__':
    unittest.main()
