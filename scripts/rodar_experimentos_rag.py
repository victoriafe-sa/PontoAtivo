"""Executa prompts RAG em lote, em chamadas independentes e com registros."""
import argparse
import csv
from datetime import datetime
import fcntl
import getpass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
import warnings

BASE = Path(__file__).resolve().parents[1] / 'experimentos' / 'experimento-rag'
MODELOS = {'qwen': 'qwen3:8b', 'llama': 'llama3.2:3b',
           'gemini': 'gemini-3.5-flash-lite'}
COLUNAS_METRICAS = [
    'pergunta_id', 'modelo', 'provedor', 'executado_em', 'tokens_entrada',
    'tokens_saida', 'tokens_total', 'tempo_total_s', 'tempo_parede_s',
    'tempo_carga_s', 'tempo_entrada_s', 'tempo_geracao_s', 'tokens_por_s',
    'motivo_fim', 'quantizacao', 'digest', 'status_metricas', 'origem_modelo',
    'arquivo_resposta', 'arquivo_bruto',
]


def extrair_metricas(registro, ambiente):
    """Valores ausentes permanecem vazios; tempos do Ollama vêm em ns."""
    saida = registro.get('saida', {})
    linha = {
        'pergunta_id': registro['pergunta_id'],
        'modelo': saida.get('model') or saida.get('model_version') or registro['modelo'],
        'provedor': registro['provedor'],
        'executado_em': registro['inicio'],
        'tempo_parede_s': registro['tempo_cliente_segundos'],
        'origem_modelo': 'retorno_api' if saida.get('model') or saida.get('model_version') else 'solicitado_na_chamada',
        'arquivo_resposta': registro.get('arquivo_resposta', ''),
        'arquivo_bruto': registro['arquivo_bruto'],
    }
    if registro['provedor'] == 'ollama':
        linha.update(tokens_entrada=saida.get('prompt_eval_count'),
                     tokens_saida=saida.get('eval_count'),
                     motivo_fim=saida.get('done_reason'))
        for coluna, campo in [('tempo_total_s', 'total_duration'),
                              ('tempo_carga_s', 'load_duration'),
                              ('tempo_entrada_s', 'prompt_eval_duration'),
                              ('tempo_geracao_s', 'eval_duration')]:
            valor = saida.get(campo)
            linha[coluna] = valor / 1e9 if valor is not None else None
        if linha['tokens_entrada'] is not None and linha['tokens_saida'] is not None:
            linha['tokens_total'] = linha['tokens_entrada'] + linha['tokens_saida']
        if linha['tempo_geracao_s'] and linha['tokens_saida'] is not None:
            linha['tokens_por_s'] = linha['tokens_saida'] / linha['tempo_geracao_s']
        instalados = ambiente.get('modelos_instalados')
        if isinstance(instalados, dict):
            for modelo in instalados.get('models', []):
                if registro['modelo'] in (modelo.get('name'), modelo.get('model')):
                    linha['digest'] = modelo.get('digest')
                    linha['quantizacao'] = (modelo.get('details') or {}).get('quantization_level')
                    break
    else:
        uso = saida.get('usage_metadata') or {}
        linha.update(tokens_entrada=uso.get('prompt_token_count'),
                     tokens_saida=uso.get('candidates_token_count'),
                     tokens_total=uso.get('total_token_count'))
        candidatos = saida.get('candidates') or []
        linha['motivo_fim'] = candidatos[0].get('finish_reason') if candidatos else None
    linha['status_metricas'] = (
        'falha' if registro.get('erro') else
        'registradas' if linha.get('tokens_entrada') is not None and linha.get('tokens_saida') is not None
        else 'parciais')
    return linha


def salvar_metricas(linha):
    """Acrescenta uma chamada sem substituir o histórico, inclusive em lotes paralelos."""
    with (BASE / 'metricas.csv').open('a+', encoding='utf-8', newline='') as arquivo:
        fcntl.flock(arquivo, fcntl.LOCK_EX)
        arquivo.seek(0)
        cabecalho = next(csv.reader(arquivo), None)
        if cabecalho is not None and cabecalho != COLUNAS_METRICAS:
            raise ValueError('Cabeçalho de metricas.csv incompatível; JSON da chamada foi preservado.')
        arquivo.seek(0, os.SEEK_END)
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS_METRICAS, lineterminator='\n')
        if cabecalho is None:
            escritor.writeheader()
        escritor.writerow(linha)
        arquivo.flush()
        os.fsync(arquivo.fileno())


def obter_chave(area_transferencia=False):
    if area_transferencia:
        chave = subprocess.run(
            ['pbpaste'], capture_output=True, text=True, check=True
        ).stdout.strip()
        if not chave or any(c.isspace() for c in chave):
            raise ValueError('Copie somente a chave, sem espaços ou outras linhas.')
        return chave
    chave = os.environ.get('GEMINI_API_KEY', '').strip()
    if not chave:
        # Não permite o fallback do getpass que exibiria a entrada.
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            chave = getpass.getpass(
                'Cole sua NOVA chave Gemini e pressione Enter (entrada oculta): '
            ).strip()
    if not chave:
        raise ValueError('Chave vazia. Execute novamente e cole a chave quando solicitado.')
    return chave


def chamar_local(entrada):
    req = urllib.request.Request('http://localhost:11434/api/chat',
                                 data=json.dumps(entrada).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=1800) as resposta:
        return json.load(resposta)


def chamar_gemini(cliente, entrada, registro):
    for tentativa in range(1, 4):
        try:
            return cliente.models.generate_content(**entrada)
        except Exception as erro:
            codigo = getattr(erro, 'code', None)
            if not isinstance(codigo, int):
                codigo = None
            registro.setdefault('falhas_api', []).append(
                {'tentativa': tentativa, 'tipo': type(erro).__name__,
                 'codigo_http': codigo})
            if codigo not in (500, 502, 503, 504) or tentativa == 3:
                raise
            espera = 5 * 2 ** (tentativa - 1)
            print(f'Gemini HTTP {codigo}: nova tentativa em {espera}s.', flush=True)
            time.sleep(espera)


def main(sem_rag=False):
    ap = argparse.ArgumentParser(description='Executa prompts sem RAG.' if sem_rag else __doc__)
    ap.add_argument('--modelo', choices=MODELOS, required=True)
    ap.add_argument('--inicio', type=int, default=5)
    ap.add_argument('--fim', type=int, default=20)
    ap.add_argument('--simular', action='store_true', help='valida sem chamar modelos')
    ap.add_argument('--chave-area-transferencia', action='store_true',
                    help='Gemini: lê a chave copiada no Mac, sem colar no terminal')
    args = ap.parse_args()
    if not 1 <= args.inicio <= args.fim <= 20:
        ap.error('Use 1 <= inicio <= fim <= 20.')
    prompts = []
    for i in range(args.inicio, args.fim + 1):
        p = BASE / 'prompts' / f'q{i}.txt'
        texto = p.read_text(encoding='utf-8')
        if sem_rag and 'EVIDÊNCIAS:' in texto:
            ap.error(f'{p.name} contém um bloco de evidências; execução sem RAG cancelada.')
        prompts.append((i, texto))
    if args.simular:
        for i, texto in prompts:
            print(f'Q{i}: {len(texto)} caracteres; modelo {MODELOS[args.modelo]}')
        print('Simulação concluída; nenhuma chamada ou arquivo de resposta criado.')
        return

    cliente = None
    if args.modelo == 'gemini':
        try:
            from google import genai
        except ImportError:
            ap.error('Instale a dependência opcional: python -m pip install google-genai')
        try:
            chave = obter_chave(args.chave_area_transferencia)
        except (EOFError, KeyboardInterrupt, getpass.GetPassWarning, ValueError,
                OSError, subprocess.SubprocessError):
            ap.error('Chave não recebida. Se usar --chave-area-transferencia, copie somente a chave no Mac antes de executar.')
        cliente = genai.Client(api_key=chave)

    rodada = datetime.now().astimezone().strftime('rodada-%Y%m%d-%H%M%S-%f')
    pasta = BASE / f'respostas-{args.modelo}' / rodada
    pasta.mkdir(parents=True, exist_ok=False)
    pasta_brutos = BASE / 'brutos' / args.modelo / rodada
    pasta_brutos.mkdir(parents=True, exist_ok=False)
    ambiente = {'modelo_solicitado': MODELOS[args.modelo],
                'cenario': 'sem_rag' if sem_rag else 'com_rag',
                'contexto': 'Uma mensagem independente por pergunta, sem histórico.',
                'truncamento': 'Não determinado automaticamente.',
                'observacao': 'Configurações desta rodada não comprovam as anteriores.'}
    if not cliente:
        for nome, endpoint in [('versao', 'version'), ('modelos_instalados', 'tags')]:
            try:
                with urllib.request.urlopen(f'http://localhost:11434/api/{endpoint}', timeout=10) as r:
                    ambiente[nome] = json.load(r)
            except Exception:
                ambiente[nome] = 'Não disponível nesta coleta.'
    (pasta_brutos / 'ambiente.json').write_text(
        json.dumps(ambiente, ensure_ascii=False, indent=2), encoding='utf-8')
    falhas = 0
    try:
        for i, prompt in prompts:
            if cliente:
                entrada = {'model': MODELOS[args.modelo], 'contents': prompt,
                           'config': {'temperature': 0, 'max_output_tokens': 4096}}
            else:
                entrada = {'model': MODELOS[args.modelo],
                           'messages': [{'role': 'user', 'content': prompt}],
                           'stream': False,
                           'options': {'num_ctx': 8192, 'temperature': 0,
                                       'seed': 42, 'num_predict': 4096}}
                if args.modelo == 'qwen':
                    entrada['think'] = False
            registro = {'pergunta': f'Q{i}',
                        'pergunta_id': f'q{i}', 'rodada': rodada,
                        'modelo': MODELOS[args.modelo],
                        'provedor': 'gemini' if cliente else 'ollama',
                        'tipo_registro': 'execucao_api',
                        'cenario': 'sem_rag' if sem_rag else 'com_rag',
                        'ambiente_referencia': str((pasta_brutos / 'ambiente.json').relative_to(BASE)),
                        'inicio': datetime.now().astimezone().isoformat(),
                        'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                        'entrada': entrada}
            arquivo = pasta_brutos / f'q{i}.json'
            registro['arquivo_bruto'] = str(arquivo.relative_to(BASE))
            arquivo.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f'Executando Q{i}...', flush=True)
            inicio = time.perf_counter()
            try:
                if cliente:
                    resposta = chamar_gemini(cliente, entrada, registro)
                    registro['saida'] = resposta.model_dump(mode='json')
                    texto = resposta.text or ''
                else:
                    registro['saida'] = chamar_local(entrada)
                    texto = registro['saida'].get('message', {}).get('content', '')
                if not texto.strip():
                    raise ValueError('Resposta sem texto; confira a saída JSON e o motivo de término.')
                (pasta / f'q{i}.txt').write_text(
                    f'modelo: {MODELOS[args.modelo]}\n\n{texto}', encoding='utf-8')
                registro['arquivo_resposta'] = str((pasta / f'q{i}.txt').relative_to(BASE))
                print(f'Q{i}: salva.', flush=True)
            except KeyboardInterrupt:
                registro['erro'] = 'KeyboardInterrupt'
                raise
            except Exception as erro:
                # Evita persistir mensagens de provedores que possam incluir credenciais.
                registro['erro'] = type(erro).__name__
                codigo = getattr(erro, 'code', None)
                if isinstance(codigo, int):
                    registro['codigo_http'] = codigo
                falhas += 1
                detalhe = f', HTTP {codigo}' if isinstance(codigo, int) else ''
                print(f'Q{i}: falha ({type(erro).__name__}{detalhe}); registro salvo.', flush=True)
            finally:
                registro['tempo_cliente_segundos'] = time.perf_counter() - inicio
                registro['fim'] = datetime.now().astimezone().isoformat()
                registro['metricas'] = extrair_metricas(registro, ambiente)
                arquivo.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding='utf-8')
                salvar_metricas(registro['metricas'])
            if registro.get('erro'):
                print('Lote interrompido para evitar repetir uma falha de serviço/configuração.')
                break
    finally:
        if cliente:
            cliente.close()
    print(f'Resultados em: {pasta}')
    print(f'Registros em: {pasta_brutos}; métricas em: {BASE / "metricas.csv"}')
    if falhas:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
