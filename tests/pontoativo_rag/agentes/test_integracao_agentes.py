import json
from unittest.mock import Mock, patch

from pontoativo_rag.agentes.analise import analisar_duvidas
from pontoativo_rag.agentes.pesquisa import AgentePesquisa
from pontoativo_rag.recuperacao import RetrievedChunk


def test_analise_aceita_trechos_da_pesquisa_sem_converter_a_fonte():
    chunk = RetrievedChunk(
        "c1", "DOC-003", "Manual", "SEL-DF", "", "Entrada gratuita.", 0.05, 1,
        entity_key="cop", filter_metadata_missing=True,
    )
    agente = AgentePesquisa(Mock(search=Mock(return_value=[chunk])), max_distance=0.12)
    pergunta = "Qual é a regra do COP?"
    resultado = agente.executar({"consulta": pergunta})
    item = {
        "duvida": pergunta,
        "estado": "sustentada",
        "conclusao": chunk.text,
        "trechos": ["T1"],
        "evidencias": [{"id": "T1", "passagem": chunk.text}],
    }
    with patch("pontoativo_rag.agentes.analise.OllamaClient.complete",
               return_value=json.dumps([item])) as modelo:
        assert analisar_duvidas(pergunta, resultado["trechos"]) == [item]

    assert resultado["trechos"][0]["chunk_id"] == "c1"
    documento, = json.loads(modelo.call_args.args[1])["documentos"]
    assert documento["fonte"]["id"] == chunk.source_id
    assert documento["entidade"] == "cop"
    assert documento["metadado_filtro_ausente"] is True


def test_coordenador_publica_apenas_referencias_validadas():
    from pontoativo_rag.agentes.coordenador import FluxoDocumental

    chunk = RetrievedChunk("c1", "DOC-003", "Manual", "", "", "Entrada gratuita.", 0.05, 1)
    busca = Mock(return_value=[chunk])
    pesquisa = AgentePesquisa(Mock(search=busca), max_distance=0.12)
    item = {
        "duvida": "A entrada é gratuita?",
        "estado": "sustentada",
        "conclusao": chunk.text,
        "trechos": ["T1"],
        "evidencias": [{"id": "T1", "passagem": chunk.text}],
    }
    cliente = Mock(model="teste")
    cliente.complete.side_effect = ["[]", json.dumps([item])]
    fluxo = FluxoDocumental(pesquisa, cliente)

    resposta, _ = fluxo.responder(item["duvida"], top_k=2, filters={"source_id": "DOC-003"})

    busca.assert_called_once_with(item["duvida"], top_k=2, filters={"source_id": "DOC-003"})
    assert resposta.answer == "Entrada gratuita. [F1]"
    assert resposta.cited == [chunk]
    assert resposta.generation_attempts == 2


def test_coordenador_abstem_sem_chamar_o_modelo():
    from pontoativo_rag.agentes.coordenador import FluxoDocumental

    pesquisa = AgentePesquisa(Mock(search=Mock(return_value=[])), max_distance=0.12)
    cliente = Mock()
    resposta, _ = FluxoDocumental(pesquisa, cliente).responder("Qual é o horário?")
    assert resposta.mode == "abstencao"
    cliente.complete.assert_not_called()


def test_coordenador_mostra_trecho_se_modelo_estiver_indisponivel():
    from pontoativo_rag.agentes.coordenador import FluxoDocumental
    from pontoativo_rag.geracao import LLMUnavailable

    chunk = RetrievedChunk("c1", "DOC-003", "Manual", "", "", "Entrada gratuita.", 0.05, 1)
    pesquisa = AgentePesquisa(Mock(search=Mock(return_value=[chunk])), max_distance=0.12)
    cliente = Mock()
    cliente.complete.side_effect = LLMUnavailable("offline")
    resposta, _ = FluxoDocumental(pesquisa, cliente).responder("A entrada é gratuita?")
    assert resposta.mode == "recuperacao_sem_geracao"
    assert resposta.retrieved == [chunk]
    assert resposta.cited == []
    assert resposta.generation_attempts == 1


def test_coordenador_preserva_resposta_parcial_e_nao_cita_outro_local():
    from pontoativo_rag.agentes.coordenador import FluxoDocumental

    cop_gama = RetrievedChunk(
        "gama", "DOC-001", "Manual", "", "", "Há natação no COP do Gama.", 0.04, 1,
        entity_key="cop-gama",
    )
    cop_ceilandia = RetrievedChunk(
        "ceilandia", "DOC-002", "Manual", "", "", "A natação é gratuita neste COP.", 0.05, 1,
        entity_key="cop-ceilandia",
    )
    pergunta = "O COP do Gama oferece natação gratuita como modalidade?"
    pesquisa = AgentePesquisa(
        Mock(search=Mock(return_value=[cop_gama, cop_ceilandia])), max_distance=0.12,
    )
    cliente = Mock(model="teste")
    cliente.complete.return_value = json.dumps([
        {
            "duvida": "Tem natação?",
            "estado": "sustentada",
            "conclusao": cop_gama.text,
            "trechos": ["T1"],
            "evidencias": [{"id": "T1", "passagem": cop_gama.text}],
        },
        {
            "duvida": "É gratuita?",
            "estado": "lacuna",
            "conclusao": "Os documentos não confirmam a gratuidade no Gama.",
            "trechos": [],
            "evidencias": [],
        },
    ])

    with patch.object(pesquisa, "pesquisar", wraps=pesquisa.pesquisar) as pesquisar:
        resposta, _ = FluxoDocumental(pesquisa, cliente).responder(pergunta)

    assert pesquisar.call_args.args[0] == {
        "consulta": pergunta,
        "pergunta_original": pergunta,
        "tipo": "pesquisar_esportes",
    }
    dados = json.loads(cliente.complete.call_args.args[1])
    assert dados["pergunta"] == pergunta
    assert [doc["entidade"] for doc in dados["documentos"]] == ["cop-gama", "cop-ceilandia"]
    assert resposta.answer.splitlines() == [
        "Há natação no COP do Gama. [F1]",
        "Os documentos não confirmam a gratuidade no Gama.",
    ]
    assert resposta.cited == [cop_gama]
    assert resposta.model_abstained is False


def test_orcamento_esgotado_nao_inicia_geracao():
    from pontoativo_rag.agentes.coordenador import FluxoDocumental

    chunk = RetrievedChunk("c1", "DOC-003", "Manual", "", "", "Entrada gratuita.", 0.05, 1)
    pesquisa = AgentePesquisa(Mock(search=Mock(return_value=[chunk])), max_distance=0.12)
    cliente = Mock(model="teste")
    with patch("pontoativo_rag.agentes.coordenador.perf_counter", side_effect=[0, 2, 2, 2, 2]):
        resposta, _ = FluxoDocumental(pesquisa, cliente, orcamento_segundos=1).responder("Entrada gratuita?")
    assert resposta.mode == "recuperacao_sem_geracao"
    assert resposta.generation_attempts == 0
    cliente.complete.assert_not_called()


def test_cliente_compartilha_prazo_sem_mutar_timeout_original():
    from pontoativo_rag.agentes.coordenador import _ClienteComPrazo
    from pontoativo_rag.geracao import LLMUnavailable
    import pytest

    cliente = Mock(model="teste", timeout_seconds=180)
    com_prazo = _ClienteComPrazo(cliente, 10)
    with patch("pontoativo_rag.agentes.coordenador.perf_counter", side_effect=[3, 8, 11]):
        com_prazo.complete("s", "u")
        com_prazo.complete("s", "u")
        with pytest.raises(LLMUnavailable):
            com_prazo.complete("s", "u")
    assert [c.kwargs["timeout_seconds"] for c in cliente.complete.call_args_list] == [7, 2]
    assert cliente.timeout_seconds == 180


def test_analise_rejeita_campos_extras_e_referencias_duplicadas():
    from pontoativo_rag.agentes.analise import AnaliseInvalida, validar_analise
    import pytest

    trecho = {"id": "T1", "texto": "Entrada gratuita.", "metadados": {}}
    item = {"duvida": "Entrada?", "estado": "sustentada", "conclusao": "Entrada gratuita.",
            "trechos": ["T1"], "evidencias": [{"id": "T1", "passagem": trecho["texto"]}]}
    for invalido in ({**item, "extra": True}, {**item, "trechos": ["T1", "T1"]}):
        with pytest.raises(AnaliseInvalida):
            validar_analise(json.dumps([invalido]), [trecho])
