"""Comunicação com o rascunho aprovado do Parque da Cidade (docs/agentes/exemplos/).

Pergunta: cadeirante no Parque da Cidade (F029). O rascunho correto confirma
entrada gratuita e banheiros acessíveis e trata o caminho como lacuna.
"""

import copy
import json
from pathlib import Path

import pytest

from pontoativo_rag.agentes.analise import AnaliseInvalida
from pontoativo_rag.agentes.comunicacao import AgenteComunicacao, ComunicacaoRecusada
from pontoativo_rag.agentes.validacao import AgenteValidacao

EXEMPLOS = Path(__file__).resolve().parents[3] / "docs" / "agentes" / "exemplos"


def _carregar(nome):
    return json.loads((EXEMPLOS / nome).read_text(encoding="utf-8"))


TRECHOS = _carregar("validacao_trechos_f029.json")["trechos"]
CORRETO = _carregar("validacao_rascunho_correto.json")
INVENTADO = _carregar("validacao_rascunho_etapa_inventada.json")
PERGUNTA = CORRETO["pergunta"]
APROVADO = {"agente": "validacao", "aprovado": True, "revisao": "regras", "criterios": {},
            "problemas": [], "consulta_complementar": ""}


def _trecho(id_trecho, id_fonte, texto, instituicao="Órgão de teste"):
    return {"id": id_trecho, "chunk_id": f"{id_fonte}-001", "texto": texto, "distancia": 0.1,
            "fonte": {"id": id_fonte, "titulo": f"Página {id_fonte}", "instituicao": instituicao,
                      "url": f"https://exemplo.gov.br/{id_fonte}", "paginas": "", "secao": "",
                      "regiao": "", "atualidade": ""},
            "entidade": "", "metadado_filtro_ausente": False}


def _item(duvida, estado, conclusao, evidencias):
    return {"duvida": duvida, "estado": estado, "conclusao": conclusao,
            "trechos": [e["id"] for e in evidencias], "evidencias": evidencias}


def test_rascunho_aprovado_vira_resposta_com_lacuna_e_fonte():
    # Fluxo real das duas pontas: a Validação aprova, a Comunicação publica.
    parecer = AgenteValidacao().revisar(PERGUNTA, CORRETO["itens"], TRECHOS)
    final = AgenteComunicacao().comunicar(PERGUNTA, CORRETO["itens"], TRECHOS, parecer)

    assert final["agente"] == "comunicacao"
    assert final["status"] == "parcial"
    assert [r["estado"] for r in final["respostas"]] == ["sustentada", "sustentada", "lacuna"]
    # As conclusões aprovadas não são reescritas.
    assert [r["texto"] for r in final["respostas"]] == [i["conclusao"] for i in CORRETO["itens"]]
    # Três itens citam o mesmo documento: uma só referência.
    fonte, = final["fontes"]
    assert (fonte["ref"], fonte["id"]) == ("F1", "F029")
    assert all(r["fontes"] == ["F1"] for r in final["respostas"])
    assert ("Para o que ficou sem resposta, consulte diretamente Secretaria de Esporte e "
            "Lazer do DF (SEL-DF): https://www.esporte.df.gov.br/parque-da-cidade"
            ) in final["proximos_passos"]

    texto = final["texto"]
    assert texto.index("O que as fontes confirmam") < texto.index("O que as fontes não informam")
    assert "- O caminho até eles também é acessível?" in texto
    assert "Página atualizada em 20/02/2026" in texto
    json.dumps(final, ensure_ascii=False)  # a saída é JSON, como a dos outros agentes


def test_rascunho_reprovado_nao_e_publicado():
    parecer = AgenteValidacao().revisar(PERGUNTA, INVENTADO["itens"], TRECHOS)
    assert parecer["aprovado"] is False
    with pytest.raises(ComunicacaoRecusada):
        AgenteComunicacao().comunicar(PERGUNTA, INVENTADO["itens"], TRECHOS, parecer)
    with pytest.raises(ComunicacaoRecusada):
        AgenteComunicacao().comunicar(PERGUNTA, CORRETO["itens"], TRECHOS, None)


def test_passagem_que_nao_esta_na_fonte_e_barrada():
    itens = copy.deepcopy(CORRETO["itens"])
    itens[0]["evidencias"][0]["passagem"] = "Entrada: 20 reais"
    with pytest.raises(AnaliseInvalida):
        AgenteComunicacao().comunicar(PERGUNTA, itens, TRECHOS, APROVADO)


def test_fontes_numeradas_por_documento_na_ordem_de_citacao():
    trechos = [_trecho("T1", "F010", "Aulas de natação gratuitas."),
               _trecho("T2", "F003", "Piscina com rampa de acesso."),
               _trecho("T3", "F010", "Inscrições pelo site.")]
    itens = [
        _item("Tem rampa?", "sustentada", "A piscina tem rampa de acesso.",
              [{"id": "T2", "passagem": "Piscina com rampa"}]),
        _item("É gratuita?", "sustentada", "As aulas de natação são gratuitas.",
              [{"id": "T1", "passagem": "Aulas de natação gratuitas."},
               {"id": "T3", "passagem": "Inscrições pelo site."}]),
    ]
    final = AgenteComunicacao().comunicar("Natação?", itens, trechos, APROVADO)
    assert [(f["ref"], f["id"]) for f in final["fontes"]] == [("F1", "F003"), ("F2", "F010")]
    # T1 e T3 são do mesmo documento: a referência aparece uma vez.
    assert [r["fontes"] for r in final["respostas"]] == [["F1"], ["F2"]]
    assert final["status"] == "respondida"
    assert "A piscina tem rampa de acesso. [F1]" in final["texto"]


def test_pergunta_ambigua_pede_esclarecimento():
    itens = [_item("É acessível?", "precisa_esclarecimento",
                   "Qual local ou serviço você quer consultar?", [])]
    final = AgenteComunicacao().comunicar("É acessível?", itens, TRECHOS, APROVADO)
    assert final["status"] == "precisa_esclarecimento"
    assert final["fontes"] == []
    assert "Precisamos de um detalhe" in final["texto"]
    assert "Fontes" not in final["texto"]
    assert final["proximos_passos"][0].startswith("Responda à pergunta")


def test_lacuna_sem_documento_orienta_procurar_o_orgao():
    itens = [_item("Tem quadribol?", "lacuna",
                   "Os documentos recuperados não permitem confirmar a oferta de quadribol.", [])]
    final = AgenteComunicacao().comunicar("Tem quadribol?", itens, TRECHOS, APROVADO)
    assert final["status"] == "sem_resposta"
    assert final["proximos_passos"] == [
        "Os documentos consultados não tratam do que ficou sem resposta; "
        "procure o órgão responsável pelo local antes de ir."
    ]


def test_divergencia_mostra_as_duas_fontes_e_pede_confirmacao():
    trechos = [_trecho("T1", "F001", "Funciona de terça a domingo."),
               _trecho("T2", "F002", "Funciona de segunda a sexta.")]
    itens = [_item("Quando funciona?", "divergencia",
                   "Uma fonte diz terça a domingo; outra, segunda a sexta.",
                   [{"id": "T1", "passagem": "terça a domingo"},
                    {"id": "T2", "passagem": "segunda a sexta"}])]
    final = AgenteComunicacao().comunicar("Quando funciona?", itens, trechos, APROVADO)
    assert "Onde as fontes não concordam" in final["texto"]
    assert "segunda a sexta. [F1] [F2]" in final["texto"]
    assert any("qual informação está valendo" in p for p in final["proximos_passos"])
