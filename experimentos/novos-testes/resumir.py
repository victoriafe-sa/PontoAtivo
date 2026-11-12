"""Confere completude e cria planilha CSV para revisão humana, sem dar notas automáticas."""
import argparse
import csv
import json
from pathlib import Path
import statistics

BASE = Path(__file__).resolve().parent

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('rodada', help='Nome da pasta de rodada')
    args = ap.parse_args()
    pasta = BASE/'rodadas'/args.rodada
    ambiente = json.loads((pasta/'ambiente.json').read_text())
    tarefas = [t for t in json.loads((pasta/'tarefas.json').read_text())
               if t['teste'] in ambiente.get('testes', [1,2,3])]
    registros = []
    faltantes = []
    for modelo in ambiente['modelos']:
        for rep in range(1,ambiente['repeticoes']+1):
            for t in tarefas:
                nome = f'{t["id"]}--{t["condicao"]}--r{rep}'
                p = pasta/modelo/(nome+'.json')
                if not p.exists():
                    faltantes.append(f'{modelo}/{nome}')
                    continue
                r = json.loads(p.read_text())
                if r.get('erro') or not r.get('arquivo_resposta'):
                    faltantes.append(f'{modelo}/{nome}: incompleto/falha')
                    continue
                texto = (BASE/r['arquivo_resposta']).read_text()
                registros.append((modelo,r,len(texto.split())))
    linhas = ['# Verificação de execução', '', f'Respostas completas: {len(registros)}.',
              f'Ausentes ou incompletas: {len(faltantes)}.', '',
              '| Modelo | Respostas | >200 palavras | Mediana cliente (s) | Maior entrada (tokens) |',
              '|---|---:|---:|---:|---:|']
    for modelo in ambiente['modelos']:
        rs = [(r,n) for m,r,n in registros if m==modelo]
        if not rs: continue
        tempos = [r['tempo_cliente_segundos'] for r,n in rs]
        entradas = [r['metricas']['tokens_entrada'] for r,n in rs if r['metricas'].get('tokens_entrada') is not None]
        linhas.append(f'| {modelo} | {len(rs)} | {sum(n>200 for r,n in rs)} | {statistics.median(tempos):.2f} | {max(entradas) if entradas else "ausente"} |')
    linhas += ['', 'Contagem de palavras por espaços, incluindo fontes e formato. Latência inclui carga e não é benchmark isolado.',
               'Contagens de tokens não comprovam ausência de truncamento. Qualidade requer avaliação humana.', '']
    if faltantes: linhas += ['## Pendências','']+['- '+v for v in faltantes]
    (pasta/'verificacao.md').write_text('\n'.join(linhas)+'\n')
    revisao = pasta/'avaliacao.csv'
    if not revisao.exists():
        campos = ['modelo','caso','teste','condicao','repeticao','arquivo_resposta','palavras',
                  'fatos_cobertos','fatos_aplicaveis','atribuicao_errada','afirmacao_sem_suporte',
                  'limite_reconhecido','recusa_indevida','citacao_fiel','temporalidade','justificativa','avaliador']
        with revisao.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=campos);w.writeheader()
            for m,r,n in registros:
                w.writerow(dict(modelo=m,caso=r['id'],teste=r['teste'],condicao=r['condicao'],
                                repeticao=r['repeticao'],arquivo_resposta=r['arquivo_resposta'],palavras=n))
    print('\n'.join(linhas))
    if faltantes: raise SystemExit(1)

if __name__=='__main__': main()
