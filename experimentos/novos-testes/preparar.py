"""Prepara controles documentais; não chama modelos nem altera rodadas existentes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent


def preparar():
    banco = {}
    for p in sorted((ROOT / 'experimentos/experimento-rag/evidencias').glob('*.json')):
        for e in json.loads(p.read_text())['resultados']:
            registro = {k: e[k] for k in ('id', 'texto', 'metadados')}
            if e['id'] in banco and banco[e['id']] != registro:
                raise ValueError(f'Evidência divergente: {e["id"]}')
            banco[e['id']] = registro
    casos = []
    def caso(id, pergunta, ids, fatos, limites, par=None):
        casos.append(dict(id=id, teste=int(id[1]), pergunta=pergunta, evidencia_ids=ids,
                          fatos_esperados=fatos, limites_esperados=limites, par=par))
    for sufixo, entidade in [('a', 'Programa Centros Olímpicos e Paralímpicos'), ('b', 'projeto Semear')]:
        caso('t1-01'+sufixo, f'Qual é a idade mínima para participar do {entidade}?', ['F028-001'],
             ['A partir de 4 anos, conforme página atualizada em 26/06/2026.'] if sufixo == 'a' else [],
             ['Não comprova turma ou vaga atual.'] if sufixo == 'a' else ['O trecho é sobre COPs; não comprova idade mínima do Semear.'], 'idade')
    for sufixo, entidade in [('a', 'Centros Olímpicos e Paralímpicos'), ('b', 'Escola Paralímpica de Esportes')]:
        caso('t1-02'+sufixo, f'Quais modalidades são oferecidas nos {entidade}?' if sufixo == 'a' else f'Quais modalidades são oferecidas na {entidade}?', ['N03-003'],
             ['Atletismo, basquete, futsal, futebol society, ginástica localizada, pilates, vôlei, jiu-jitsu, judô, taekwondo, karatê e capoterapia.'] if sufixo == 'a' else [],
             ['Lista exemplificativa; oferta varia por unidade; não comprova oferta atual.'] if sufixo == 'a' else ['Não transferir modalidades dos COPs para a Escola Paralímpica.'], 'modalidades')
    for sufixo, entidade in [('a', 'academia pública do Parque da Cidade'), ('b', 'academia particular do Lago Sul')]:
        caso('t1-03'+sufixo, f'Como utilizar a {entidade} e é gratuito?', ['N04-008'],
             ['Musculação e aulas gratuitas; baixar Mude – Yoga e Fitness, cadastrar-se e agendar; presença de profissional de educação física.'] if sufixo == 'a' else [],
             ['Informação documental, sem confirmação operacional atual.'] if sufixo == 'a' else ['Não transferir gratuidade ou procedimento da academia pública para academia privada não identificada.'], 'gratuidade')
    caso('t2-01', 'Qual é o endereço do Bezerrão, qual a capacidade estimada e há disponibilidade para reserva em 13/11/2026 às 19h?', ['F059-001'],
         ['St. Central – Gama, Brasília – DF, 72405-610.', 'Capacidade estimada de 20.310 espectadores; página atualizada em 20/02/2026.'],
         ['Não há agenda de reservas; não confirmar nem negar vaga.'])
    caso('t2-02', 'A academia pública do Parque da Cidade é gratuita, como faço o agendamento e há horário livre em 13/11/2026 às 19h?', ['N04-008'],
         ['Musculação e aulas gratuitas.', 'Baixar Mude – Yoga e Fitness, cadastrar-se e agendar; funcionamento condicionado a profissional de educação física.'],
         ['Não há disponibilidade de agenda para a data solicitada.'])
    caso('t2-03', 'A partir de qual idade posso participar dos COPs, pessoas com deficiência estão incluídas e há vaga para uma criança de 5 anos no COP do Gama em 13/11/2026?', ['F028-001'],
         ['A partir de 4 anos.', 'Público inclui pessoas com deficiência; página atualizada em 26/06/2026.'],
         ['Elegibilidade geral não comprova vaga nem turma específica no Gama.'])
    for n, pergunta, ids, fatos, limites in [
        (1, 'Qual é o endereço do Estádio Bezerrão no Gama?', ['F059-001'], ['St. Central – Gama, Brasília – DF, 72405-610.'], ['Endereço documental; atualização de 20/02/2026 não comprova funcionamento atual.']),
        (2, 'Como utilizar a academia pública do Parque da Cidade e é gratuito?', ['N04-008'], ['Gratuito; baixar Mude – Yoga e Fitness, cadastrar-se e agendar; presença de profissional de educação física.'], ['Não confirmar disponibilidade ou funcionamento atual.']),
        (3, 'Qual é a idade mínima para participar do Programa Centros Olímpicos e Paralímpicos?', ['F028-001'], ['A partir de 4 anos; página atualizada em 26/06/2026.'], ['Não comprova turma ou vaga atual.'])]:
        caso(f't3-0{n}', pergunta, ids, fatos, limites)
    BASE.mkdir(parents=True, exist_ok=True)
    tarefas = []
    for c in casos:
        alvo = c['evidencia_ids']
        variantes = {'sem_rag': [], 'rag_curto': alvo}
        if c['teste'] == 3:
            ruido = ['F060-001', 'F062-001', 'N01-049', 'N03-003']
            variantes.update(rag_ruido_inicio=alvo+ruido,
                             rag_ruido_meio=ruido[:2]+alvo+ruido[2:],
                             rag_ruido_fim=ruido+alvo)
        for condicao, ids in variantes.items():
            tarefa = {k: c[k] for k in ('id', 'teste', 'pergunta')}
            tarefa.update(condicao=condicao, evidencia_ids=ids)
            tarefas.append(tarefa)
    usados = {id for t in tarefas for id in t['evidencia_ids']}
    for nome, dados in [('gabarito.json', casos), ('tarefas.json', tarefas),
                        ('evidencias.json', {id:banco[id] for id in sorted(usados)})]:
        (BASE / nome).write_text(json.dumps(dados, ensure_ascii=False, indent=2)+'\n')
    print(f'{len(casos)} perguntas; {len(tarefas)} chamadas por modelo/repetição.')


if __name__ == '__main__':
    preparar()
