"""Gera docs/dados.json, usado pela página do GitHub Pages (docs/index.html).

Uso (a partir da raiz do repositório, somente biblioteca padrão):
    python3 scripts/gerar_site.py

Lê os chunks, as perguntas de avaliação, as respostas dos experimentos e as
tabelas de avaliação das análises. Rode novamente sempre que esses arquivos
mudarem; nada é inventado: campos ausentes ficam vazios.
"""
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
EXP = RAIZ / 'experimentos'
SAIDA = RAIZ / 'docs' / 'dados.json'
MODELOS = ['gemini', 'qwen', 'llama']
CENARIOS = {'rag': 'experimento-rag', 'sem_rag': 'experimento-sem-rag'}
MARCADOR = '--- CONTEÚDO ORIGINAL PRESERVADO ---'
CABECALHO = re.compile(r'^(modelo|executado_em|tokens|tempo_s)\s*:|^---\s*$')


def ler_chunks():
    chunks, fontes = [], {}
    for linha in (RAIZ / 'dados' / 'chunks.jsonl').read_text(encoding='utf-8').splitlines():
        c = json.loads(linha)
        m = c['metadados']
        chunks.append({'id': c['id'], 'f': m['id_fonte'], 't': c['texto']})
        f = fontes.setdefault(m['id_fonte'], {
            'id': m['id_fonte'], 'titulo': m['titulo'], 'orgao': m['orgao'],
            'link': m['link'], 'tema': m['tema'], 'tipo': m['tipo_evidencia'],
            'publicacao': m['data_publicacao'], 'coleta': m['data_coleta'],
            'validacao': m['validacao'], 'ressalvas': m['ressalvas'], 'chunks': 0})
        f['chunks'] += 1
    return chunks, sorted(fontes.values(), key=lambda f: f['id'])


def ler_resposta(arquivo):
    texto = arquivo.read_text(encoding='utf-8')
    if MARCADOR in texto:
        texto = texto.split(MARCADOR, 1)[1]
    linhas = texto.strip().splitlines()
    modelo = ''
    while linhas and (CABECALHO.match(linhas[0]) or not linhas[0].strip()):
        if linhas[0].startswith('modelo:'):
            modelo = linhas[0].split(':', 1)[1].strip()
        linhas.pop(0)
    return {'modelo': modelo, 'texto': '\n'.join(linhas).strip()}


def ler_avaliacoes(arquivo):
    """Primeira linha de tabela encontrada para cada pergunta: Gemini, Qwen, Llama."""
    avaliacoes = {}
    for linha in arquivo.read_text(encoding='utf-8').splitlines():
        m = re.match(r'^\|\s*Q(\d+)\b[^|]*\|(.+)\|\s*$', linha)
        if m and m.group(1) not in avaliacoes:
            celulas = [c.strip().replace('**', '') for c in m.group(2).split('|')]
            if len(celulas) == 3:
                avaliacoes[m.group(1)] = dict(zip(MODELOS, celulas))
    return avaliacoes


def main():
    chunks, fontes = ler_chunks()
    perguntas = [json.loads(l) for l in
                 (EXP / 'perguntas_avaliacao.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    respostas, avaliacoes = {}, {}
    for cenario, pasta in CENARIOS.items():
        avaliacoes[cenario] = ler_avaliacoes(EXP / pasta / 'analise-respostas.md')
        respostas[cenario] = {}
        for modelo in MODELOS:
            for arquivo in (EXP / pasta / f'respostas-{modelo}').glob('q*.txt'):
                n = re.fullmatch(r'q(\d+)\.txt', arquivo.name)
                if n:
                    respostas[cenario].setdefault(n.group(1), {})[modelo] = ler_resposta(arquivo)
    dados = {'fontes': fontes, 'chunks': chunks, 'perguntas': perguntas,
             'respostas': respostas, 'avaliacoes': avaliacoes}
    SAIDA.write_text(json.dumps(dados, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'{SAIDA.relative_to(RAIZ)}: {len(fontes)} fontes, {len(chunks)} chunks, '
          f'{len(perguntas)} perguntas, avaliações RAG {len(avaliacoes["rag"])} / '
          f'sem RAG {len(avaliacoes["sem_rag"])}')


if __name__ == '__main__':
    main()
