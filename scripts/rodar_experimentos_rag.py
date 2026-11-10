"""Executa prompts RAG em lote, em chamadas independentes e com registros."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

BASE = Path(__file__).resolve().parents[1] / 'experimentos' / 'experimento-rag'
MODELOS = {'qwen': 'qwen3:8b', 'llama': 'llama3.2:3b',
           'gemini': 'gemini-3.5-flash-lite'}


def chamar_local(entrada):
    req = urllib.request.Request('http://localhost:11434/api/chat',
                                 data=json.dumps(entrada).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=1800) as resposta:
        return json.load(resposta)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--modelo', choices=MODELOS, required=True)
    ap.add_argument('--inicio', type=int, default=5)
    ap.add_argument('--fim', type=int, default=20)
    ap.add_argument('--simular', action='store_true', help='valida sem chamar modelos')
    args = ap.parse_args()
    if not 1 <= args.inicio <= args.fim <= 20:
        ap.error('Use 1 <= inicio <= fim <= 20.')
    prompts = []
    for i in range(args.inicio, args.fim + 1):
        p = BASE / 'prompts' / f'q{i}.txt'
        prompts.append((i, p.read_text(encoding='utf-8')))
    if args.simular:
        for i, texto in prompts:
            print(f'Q{i}: {len(texto)} caracteres; modelo {MODELOS[args.modelo]}')
        print('Simulação concluída; nenhuma chamada ou arquivo de resposta criado.')
        return

    cliente = None
    if args.modelo == 'gemini':
        chave = os.environ.get('GEMINI_API_KEY')
        if not chave:
            ap.error('Defina GEMINI_API_KEY no ambiente. Não escreva a chave no código.')
        try:
            from google import genai
        except ImportError:
            ap.error('Instale a dependência opcional: python -m pip install google-genai')
        cliente = genai.Client(api_key=chave)

    rodada = datetime.now().astimezone().strftime('rodada-%Y%m%d-%H%M%S-%f')
    pasta = BASE / f'respostas-{args.modelo}' / rodada
    pasta.mkdir(parents=True, exist_ok=False)
    ambiente = {'modelo_solicitado': MODELOS[args.modelo],
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
    (pasta / 'ambiente.json').write_text(json.dumps(ambiente, ensure_ascii=False, indent=2))
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
                        'inicio': datetime.now().astimezone().isoformat(),
                        'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                        'entrada': entrada}
            arquivo = pasta / f'q{i}.json'
            arquivo.write_text(json.dumps(registro, ensure_ascii=False, indent=2))
            print(f'Executando Q{i}...', flush=True)
            inicio = time.perf_counter()
            try:
                if cliente:
                    resposta = cliente.models.generate_content(**entrada)
                    registro['saida'] = resposta.model_dump(mode='json')
                    texto = resposta.text or ''
                else:
                    registro['saida'] = chamar_local(entrada)
                    texto = registro['saida'].get('message', {}).get('content', '')
                if not texto.strip():
                    raise ValueError('Resposta sem texto; confira a saída JSON e o motivo de término.')
                (pasta / f'q{i}.txt').write_text(
                    f'modelo: {MODELOS[args.modelo]}\n\n{texto}', encoding='utf-8')
                print(f'Q{i}: salva.', flush=True)
            except Exception as erro:
                # Evita persistir mensagens de provedores que possam incluir credenciais.
                registro['erro'] = type(erro).__name__
                falhas += 1
                print(f'Q{i}: falha ({type(erro).__name__}); registro salvo.', flush=True)
            finally:
                registro['tempo_cliente_segundos'] = time.perf_counter() - inicio
                registro['fim'] = datetime.now().astimezone().isoformat()
                arquivo.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding='utf-8')
            if registro.get('erro'):
                print('Lote interrompido para evitar repetir uma falha de serviço/configuração.')
                break
    finally:
        if cliente:
            cliente.close()
    print(f'Resultados em: {pasta}')
    if falhas:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
