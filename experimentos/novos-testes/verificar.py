"""Valida controles experimentais sem chamar modelos."""
import importlib.util
from pathlib import Path
import json

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('executar', BASE/'executar.py')
executor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(executor)
tarefas, evidencias = executor.carregar()
gabarito = json.loads((BASE/'gabarito.json').read_text())
assert len(tarefas) == 33 and len(gabarito) == 12
for c in gabarito:
    ts = {t['condicao']:t for t in tarefas if t['id']==c['id']}
    assert len({t['pergunta'] for t in ts.values()}) == 1
    assert len(ts) == (5 if c['teste']==3 else 2)
    sem = executor.prompt(ts['sem_rag'],evidencias)
    assert 'EVIDÊNCIAS:' not in sem
    for e in evidencias.values():
        assert e['texto'] not in sem
    for t in ts.values():
        # Inserir uma sentinela nos campos de avaliação não deve alterar o prompt.
        antes = executor.prompt(t,evidencias)
        depois = executor.prompt(dict(t,fatos_esperados=['SEGREDO_GABARITO']),evidencias)
        assert antes == depois
    if c['teste']==3:
        alvo = c['evidencia_ids'][0]
        listas = [ts['rag_ruido_'+p]['evidencia_ids'] for p in ['inicio','meio','fim']]
        assert [ids.index(alvo) for ids in listas] == [0,2,4]
        assert len({tuple(sorted(ids)) for ids in listas}) == 1
        assert len({tuple(i for i in ids if i != alvo) for ids in listas}) == 1
        assert len({len(executor.prompt(ts['rag_ruido_'+p],evidencias)) for p in ['inicio','meio','fim']}) == 1
for par in ['idade','modalidades','gratuidade']:
    cs = [c for c in gabarito if c['par']==par]
    assert len(cs)==2 and cs[0]['evidencia_ids']==cs[1]['evidencia_ids']
print('OK: 33 condições, perguntas pareadas, sem vazamento de evidências/gabarito, ruído e posições controlados.')
