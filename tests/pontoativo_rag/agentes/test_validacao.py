"""Validação com os dois rascunhos preparados à mão (docs/agentes/exemplos/).

Pergunta: cadeirante no Parque da Cidade (F029). O rascunho correto confirma
entrada gratuita e banheiros acessíveis e trata o caminho como lacuna; o outro
inventa a etapa "o trajeto até os banheiros é acessível".
"""

import copy
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from pontoativo_rag.agentes.coordenador import FluxoDocumental
from pontoativo_rag.agentes.interpretacao import AgenteInterpretacao
from pontoativo_rag.agentes.pesquisa import AgentePesquisa
from pontoativo_rag.agentes.validacao import (
    AgenteValidacao, ParecerInvalido, conferir_apoio, feedback_para_analise, ler_parecer,
)
from pontoativo_rag.recuperacao import RetrievedChunk

EXEMPLOS = Path(__file__).resolve().parents[3] / "docs" / "agentes" / "exemplos"


def _carregar(nome):
    return json.loads((EXEMPLOS / nome).read_text(encoding="utf-8"))


TRECHOS = _carregar("validacao_trechos_f029.json")["trechos"]
CORRETO = _carregar("validacao_rascunho_correto.json")
INVENTADO = _carregar("validacao_rascunho_etapa_inventada.json")
PERGUNTA = CORRETO["pergunta"]
TODOS_OK = {"sustentacao": True, "condicoes": True, "completude": True,
            "temporalidade": True, "lacunas_conflitos": True}


def _aprovacao():
    return json.dumps({"aprovado": True, "criterios": TODOS_OK, "problemas": [],
                       "consulta_complementar": ""})


def test_rascunho_correto_e_aprovado_pelas_regras():
    parecer = AgenteValidacao().revisar(PERGUNTA, CORRETO["itens"], TRECHOS)
    assert parecer["aprovado"] is True
    assert parecer["revisao"] == "regras"
    assert parecer["problemas"] == []


def test_etapa_inventada_e_reprovada_com_o_trecho_a_corrigir():
    parecer = AgenteValidacao().revisar(PERGUNTA, INVENTADO["itens"], TRECHOS)
    assert parecer["aprovado"] is False
    assert parecer["criterios"]["sustentacao"] is False
    problema, = parecer["problemas"]
    assert problema["item"] == 3
    assert problema["trecho_rascunho"] in INVENTADO["itens"][2]["conclusao"]
    assert "trajeto" in problema["correcao"]
    # Os itens apoiados pela F029 não são apontados.
    assert {p["item"] for p in parecer["problemas"]} == {3}


def test_regra_ignora_lacunas_e_aceita_variacao_de_genero_e_numero():
    itens = [{"duvida": "Gratuito?", "estado": "sustentada",
              "conclusao": "O acesso ao parque é gratuito e há banheiro acessível.",
              "trechos": ["T1"], "evidencias": [{"id": "T1", "passagem": "Entrada: gratuita"}]},
             {"duvida": "Rampas?", "estado": "lacuna",
              "conclusao": "A fonte não fala de rampas.", "trechos": [], "evidencias": []}]
    assert conferir_apoio(itens, TRECHOS) == []


def test_numero_ausente_da_fonte_e_apontado():
    itens = [{"duvida": "Preço?", "estado": "sustentada",
              "conclusao": "A entrada custa 20 reais.", "trechos": ["T1"],
              "evidencias": [{"id": "T1", "passagem": "Entrada: gratuita"}]}]
    problema, = conferir_apoio(itens, TRECHOS)
    assert "20" in problema["correcao"] and "reais" in problema["correcao"]


def test_modelo_nao_aprova_etapa_que_a_regra_reprovou():
    cliente = Mock(model="teste")
    cliente.complete.return_value = _aprovacao()
    parecer = AgenteValidacao(cliente).revisar(PERGUNTA, INVENTADO["itens"], TRECHOS)
    assert parecer["aprovado"] is False
    assert parecer["revisao"] == "regras_e_modelo"
    dados = json.loads(cliente.complete.call_args.args[1])
    assert dados["alertas_automaticos"][0]["item"] == 3


def test_modelo_aprova_rascunho_correto():
    cliente = Mock(model="teste")
    cliente.complete.return_value = _aprovacao()
    parecer = AgenteValidacao(cliente).revisar(PERGUNTA, CORRETO["itens"], TRECHOS)
    assert parecer["aprovado"] is True
    assert parecer["revisao"] == "regras_e_modelo"


def test_modelo_pode_reprovar_o_que_a_regra_nao_ve():
    itens = copy.deepcopy(CORRETO["itens"])
    cliente = Mock(model="teste")
    cliente.complete.return_value = json.dumps({
        "aprovado": False, "criterios": {**TODOS_OK, "completude": False},
        "problemas": [{"item": 1, "trecho_rascunho": "a entrada no Parque da Cidade",
                       "criterio": "completude", "correcao": "Teste."}],
        "consulta_complementar": "",
    })
    parecer = AgenteValidacao(cliente).revisar(PERGUNTA, itens, TRECHOS)
    assert parecer["aprovado"] is False
    assert parecer["problemas"][0]["criterio"] == "completude"


@pytest.mark.parametrize("problema", [
    {"item": 3, "trecho_rascunho": "texto que não está no rascunho",
     "criterio": "sustentacao", "correcao": "x"},
    {"item": 9, "trecho_rascunho": "Sim", "criterio": "sustentacao", "correcao": "x"},
    {"item": 3, "trecho_rascunho": "Sim", "criterio": "inventado", "correcao": "x"},
])
def test_parecer_do_modelo_e_conferido(problema):
    bruto = json.dumps({"aprovado": False, "criterios": {**TODOS_OK, "sustentacao": False},
                        "problemas": [problema], "consulta_complementar": ""})
    with pytest.raises(ParecerInvalido):
        ler_parecer(bruto, INVENTADO["itens"])


def test_revisor_tem_segunda_chance_e_depois_falha():
    invalido = json.dumps({"aprovado": False, "criterios": TODOS_OK, "problemas": [
        {"item": 1, "trecho_rascunho": "texto de outro item", "criterio": "completude",
         "correcao": "x"}], "consulta_complementar": ""})
    cliente = Mock(model="teste")
    cliente.complete.side_effect = [invalido, _aprovacao()]
    assert AgenteValidacao(cliente).revisar(PERGUNTA, CORRETO["itens"], TRECHOS)["aprovado"]
    segunda = json.loads(cliente.complete.call_args.args[1])
    assert "não é literal" in segunda["erro_parecer"]
    assert segunda["rascunho"][0]["item"] == 1

    cliente.complete.side_effect = [invalido, invalido]
    with pytest.raises(ParecerInvalido):
        AgenteValidacao(cliente).revisar(PERGUNTA, CORRETO["itens"], TRECHOS)


def test_pedido_de_busca_apos_o_limite_e_descartado():
    cliente = Mock(model="teste")
    cliente.complete.return_value = json.dumps({
        "aprovado": False, "criterios": {**TODOS_OK, "completude": False},
        "problemas": [{"item": 3, "trecho_rascunho": "A página não descreve o caminho",
                       "criterio": "completude", "correcao": "Buscar."}],
        "consulta_complementar": "outra busca",
    })
    parecer = AgenteValidacao(cliente).revisar(PERGUNTA, CORRETO["itens"], TRECHOS, pode_pesquisar=False)
    assert parecer["aprovado"] is False
    assert parecer["consulta_complementar"] == ""


def test_reprovacao_sem_motivo_e_aprovacao_contraditoria_sao_rejeitadas():
    for bruto in (
        {"aprovado": False, "criterios": TODOS_OK, "problemas": [], "consulta_complementar": ""},
        {"aprovado": True, "criterios": {**TODOS_OK, "completude": False}, "problemas": [],
         "consulta_complementar": ""},
    ):
        with pytest.raises(ParecerInvalido):
            ler_parecer(json.dumps(bruto), CORRETO["itens"])


def test_feedback_devolve_o_trecho_para_a_analise():
    parecer = AgenteValidacao().revisar(PERGUNTA, INVENTADO["itens"], TRECHOS)
    mensagem, = feedback_para_analise(parecer, INVENTADO["itens"])
    assert mensagem.startswith('Item 3 ("O caminho até eles também é acessível?")')
    assert parecer["problemas"][0]["trecho_rascunho"] in mensagem


def test_interpretacao_identifica_as_tres_duvidas():
    assert AgenteInterpretacao().identificar_duvidas(PERGUNTA) == [
        "Preciso pagar para entrar?", "Há banheiros acessíveis?",
        "O caminho até eles também é acessível?",
    ]


# --- Integração: Pesquisa -> Análise -> Validação -> Análise corrigida ---

def _chunk_f029():
    t = TRECHOS[0]
    return RetrievedChunk(
        t["chunk_id"], "F029", t["fonte"]["titulo"], t["fonte"]["instituicao"],
        t["fonte"]["url"], t["texto"], 0.05, 1,
    )


def _fluxo(cliente, *, validacao=None, max_correcoes=1, buscas=None):
    chunk = _chunk_f029()
    busca = Mock(side_effect=buscas) if buscas else Mock(return_value=[chunk])
    eventos = []
    fluxo = FluxoDocumental(
        AgentePesquisa(Mock(search=busca), max_distance=0.12), cliente,
        validacao=validacao or AgenteValidacao(), max_correcoes=max_correcoes,
        registrar=eventos.append,
    )
    return fluxo, eventos, busca


def test_coordenador_devolve_trecho_sem_apoio_e_publica_a_correcao():
    cliente = Mock(model="teste")
    cliente.complete.side_effect = [json.dumps(INVENTADO["itens"]), json.dumps(CORRETO["itens"])]
    fluxo, eventos, _ = _fluxo(cliente)

    resposta, _ = fluxo.responder(PERGUNTA)

    assert resposta.mode == "rag"
    assert "não dá para confirmar" in resposta.answer
    assert "O trajeto até os banheiros também é acessível" not in resposta.answer
    segunda_analise = json.loads(cliente.complete.call_args_list[1].args[1])
    assert "O trajeto até os banheiros" in segunda_analise["feedback_validacao"][0]
    assert segunda_analise["rascunho_anterior"] == INVENTADO["itens"]
    etapas = [e["etapa"] for e in eventos]
    assert etapas == [
        "interpretacao_para_pesquisa", "pesquisa_para_analise", "analise_para_validacao",
        "validacao", "validacao_para_analise", "analise_para_validacao", "validacao",
    ]
    assert [e["parecer"]["aprovado"] for e in eventos if e["etapa"] == "validacao"] == [False, True]


def test_coordenador_nao_publica_se_a_correcao_continua_sem_apoio():
    cliente = Mock(model="teste")
    cliente.complete.return_value = json.dumps(INVENTADO["itens"])
    fluxo, _, _ = _fluxo(cliente)
    resposta, _ = fluxo.responder(PERGUNTA)
    assert resposta.mode == "recuperacao_sem_geracao"
    assert "não passou na validação das fontes" in resposta.answer
    assert cliente.complete.call_count == 2


def test_parecer_invalido_nao_autoriza_publicar():
    cliente = Mock(model="teste")
    cliente.complete.side_effect = [json.dumps(CORRETO["itens"]), "não é JSON", "não é JSON"]
    fluxo, _, _ = _fluxo(cliente, validacao=AgenteValidacao(cliente))
    resposta, _ = fluxo.responder(PERGUNTA)
    assert resposta.mode == "recuperacao_sem_geracao"
    assert "validação não conseguiu revisar" in resposta.answer


@pytest.mark.parametrize("repetir_chunk", [True, False])
def test_validacao_pede_consulta_complementar_a_pesquisa(repetir_chunk, monkeypatch, tmp_path):
    rotas = RetrievedChunk("rotas", "F030", "Rotas", "SEL-DF", "", "Rotas acessíveis até os banheiros.",
                           0.05, 1)
    lacuna = copy.deepcopy(CORRETO["itens"])
    final = copy.deepcopy(CORRETO["itens"])
    final[2] = {"duvida": lacuna[2]["duvida"], "estado": "sustentada",
                "conclusao": "Há rotas acessíveis até os banheiros.", "trechos": ["T2"],
                "evidencias": [{"id": "T2", "passagem": rotas.text}]}
    pede_busca = json.dumps({
        "aprovado": False, "criterios": {**TODOS_OK, "completude": False},
        "problemas": [{"item": 3, "trecho_rascunho": "A página não descreve o caminho",
                       "criterio": "completude", "correcao": "Buscar o trajeto."}],
        "consulta_complementar": "rota acessível até os banheiros do Parque da Cidade",
    })
    cliente = Mock(model="teste")
    cliente.complete.side_effect = [json.dumps(lacuna), pede_busca, json.dumps(final), _aprovacao()]
    fluxo, eventos, busca = _fluxo(
        cliente, validacao=AgenteValidacao(cliente), buscas=[[_chunk_f029()], [_chunk_f029(), rotas] if repetir_chunk else [rotas]],
    )

    resposta, _ = fluxo.responder(PERGUNTA)

    assert resposta.mode == "rag"
    assert busca.call_args_list[1].args[0] == "rota acessível até os banheiros do Parque da Cidade"
    assert "Há rotas acessíveis até os banheiros. [F2]" in resposta.answer
    assert [c.chunk_id for c in resposta.retrieved] == ["F029-003", "rotas"]
    assert "validacao_para_pesquisa" in [e["etapa"] for e in eventos]
    # Depois da busca complementar, o revisor não pode pedir outra.
    assert json.loads(cliente.complete.call_args_list[3].args[1])[
        "pesquisa_complementar_disponivel"] is False

    # A demonstração precisa usar os mesmos IDs que a última revisão recebeu.
    import runpy
    demo = runpy.run_path(str(EXEMPLOS.parents[2] / "scripts" / "demonstrar_validacao.py"))
    revisoes = [e for e in eventos if e["etapa"] == "validacao"]
    assert [t["id"] for t in revisoes[0]["trechos"]] == ["T1"]
    assert [(t["id"], t["fonte"]["id"]) for t in revisoes[-1]["trechos"]] == [
        ("T1", "F029"), ("T2", "F030"),
    ]
    texto = demo["comunicar"](final, revisoes[-1]["trechos"])
    assert "Fonte F029" in texto and "Fonte F030" in texto
    # Executa o caminho de gravação do script com a consulta já exercitada acima.
    def criar_fluxo_demo(*args, **kwargs):
        for evento in eventos:
            kwargs["registrar"](evento)
        return Mock(responder=Mock(return_value=(resposta, 0.01)))
    monkeypatch.setitem(demo["main"].__globals__, "FluxoDocumental", criar_fluxo_demo)
    saida = tmp_path / "demo.json"
    monkeypatch.setattr("sys.argv", ["demonstrar_validacao.py", "--saida", str(saida)])
    assert demo["main"]() == 0
    registro = json.loads(saida.read_text())
    assert registro["resposta_comunicacao"] == texto


@pytest.mark.parametrize("ultima_saida,modo", [
    (_aprovacao(), "rag"), ("não é JSON", "recuperacao_sem_geracao"),
])
def test_conta_cada_chamada_do_revisor(ultima_saida, modo):
    cliente = Mock(model="teste")
    cliente.complete.side_effect = [json.dumps(CORRETO["itens"]), "não é JSON", ultima_saida]
    fluxo, _, _ = _fluxo(cliente, validacao=AgenteValidacao(cliente))
    resposta, _ = fluxo.responder(PERGUNTA)
    assert resposta.mode == modo
    assert resposta.generation_attempts == cliente.complete.call_count == 3


def test_demo_salva_abstencao_sem_eventos_de_validacao(monkeypatch, tmp_path):
    import runpy
    from pontoativo_rag.geracao import GroundedAnswer

    demo = runpy.run_path(str(EXEMPLOS.parents[2] / "scripts" / "demonstrar_validacao.py"))
    resposta = GroundedAnswer(PERGUNTA, "abstencao", "Sem evidências.", [])
    monkeypatch.setitem(demo["main"].__globals__, "FluxoDocumental",
                        Mock(return_value=Mock(responder=Mock(return_value=(resposta, 0.01)))))
    saida = tmp_path / "sem-evidencias.json"
    monkeypatch.setattr("sys.argv", ["demonstrar_validacao.py", "--saida", str(saida)])
    assert demo["main"]() == 1
    assert json.loads(saida.read_text())["resposta_comunicacao"] == "Sem evidências."
