import base64
import io
import json
from unittest.mock import Mock

import httpx
import pytest
from PIL import Image

from pontoativo_rag.agentes.imagem import (
    AgenteImagem, CAMPOS, ExtracaoInvalida, ImagemInvalida, preparar_imagem, validar_extracao,
)
from pontoativo_rag.agentes.multimodal import responder_imagem
from pontoativo_rag.geracao import OllamaClient


def png():
    buffer = io.BytesIO()
    Image.new("RGB", (100, 100), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def extracao(texto="Futsal às 9h", legibilidade="legivel"):
    return {"legibilidade": legibilidade, "texto": texto,
            "campos": {k: [] for k in CAMPOS}, "alertas": []}


def agente(dados=None):
    cliente = Mock(model="visao-teste")
    cliente.complete.return_value = json.dumps(dados or extracao())
    return AgenteImagem(cliente)


def test_valida_conteudo_e_envia_pixels():
    visual = agente()
    resultado = visual.extrair(png())
    enviado = visual.cliente.complete.call_args.kwargs["images"][0]
    assert Image.open(io.BytesIO(base64.b64decode(enviado))).size == (100, 100)
    assert resultado["fonte"] == "I1"
    assert len(resultado["sha256"]) == 64


@pytest.mark.parametrize("conteudo", [b"", b"arquivo falso.png", b"x" * (5 * 1024 * 1024 + 1)])
def test_rejeita_arquivo_antes_do_modelo(conteudo):
    visual = agente()
    with pytest.raises(ImagemInvalida):
        visual.extrair(conteudo)
    visual.cliente.complete.assert_not_called()


def test_limite_pixels():
    buffer = io.BytesIO()
    Image.new("RGB", (4000, 3001)).save(buffer, format="PNG")
    with pytest.raises(ImagemInvalida, match="pixels"):
        preparar_imagem(buffer.getvalue())


def test_campo_sem_evidencia_rejeitado():
    dados = extracao()
    dados["campos"]["local"] = ["Brasília"]
    with pytest.raises(ExtracaoInvalida):
        validar_extracao(json.dumps(dados))


@pytest.mark.parametrize("dados", [[], {}, extracao("", "legivel"), extracao("Futsal", "ilegivel")])
def test_saida_incoerente_rejeitada(dados):
    with pytest.raises(ExtracaoInvalida):
        validar_extracao(json.dumps(dados))


def test_ilegivel_nao_chama_texto():
    texto = Mock()
    resultado = responder_imagem("Qual horário?", png(),
        agente=agente(extracao("", "ilegivel")), cliente_texto=texto)
    assert resultado["modo"] == "abstencao"
    texto.complete.assert_not_called()


def test_integracao_texto_com_citacao():
    texto = Mock(model="texto-teste")
    itens = [{"duvida": "Qual horário?", "estado": "sustentada", "conclusao": "Futsal às 9h",
              "trechos": ["I1"], "evidencias": [{"id": "I1", "passagem": "Futsal às 9h"}]}]
    parecer = {"aprovado": True, "criterios": {k: True for k in (
        "sustentacao", "condicoes", "completude", "temporalidade", "lacunas_conflitos")},
        "problemas": [], "consulta_complementar": ""}
    texto.complete.side_effect = [json.dumps(itens), json.dumps(parecer)]
    resultado = responder_imagem("Qual horário?", png(), agente=agente(), cliente_texto=texto)
    assert resultado["modo"] == "multimodal"
    assert "[I1]" in resultado["resposta"]
    assert "Futsal às 9h" in texto.complete.call_args_list[0].args[1]


def test_texto_nao_publica_evidencia_inventada():
    texto = Mock(model="texto-teste")
    texto.complete.return_value = json.dumps([{
        "duvida": "É grátis?", "estado": "sustentada", "conclusao": "Grátis",
        "trechos": ["I1"], "evidencias": [{"id": "I1", "passagem": "Grátis"}]}])
    resultado = responder_imagem("É grátis?", png(), agente=agente(), cliente_texto=texto)
    assert resultado["modo"] == "falha_validacao"
    assert resultado["itens"] == []


def test_ollama_transporta_imagem_sem_alterar_texto(monkeypatch):
    post = Mock(return_value=httpx.Response(200, json={"message": {"content": "ok"}},
                                           request=httpx.Request("POST", "http://localhost")))
    monkeypatch.setattr(httpx, "post", post)
    cliente = OllamaClient("http://localhost", "visual", 10)
    cliente.complete("sistema", "pergunta", images=["base64"])
    assert post.call_args.kwargs["json"]["messages"][1]["images"] == ["base64"]
    cliente.complete("sistema", "pergunta")
    assert "images" not in post.call_args.kwargs["json"]["messages"][1]


def test_passagens_distantes_exigem_evidencias_separadas():
    from pontoativo_rag.agentes.analise import AnaliseInvalida, validar_analise
    trechos = [{"id": "I1", "texto": "Futsal: 9h\nVolei: 15h\nLocal: Quadra Exemplo",
                "metadados": {"id": "I1"}}]
    item = {"duvida": "Manhã e local?", "estado": "sustentada",
            "conclusao": "Futsal: 9h, Quadra Exemplo", "trechos": ["I1"],
            "evidencias": [{"id": "I1", "passagem": "Futsal: 9h\nLocal: Quadra Exemplo"}]}
    with pytest.raises(AnaliseInvalida):
        validar_analise(json.dumps([item]), trechos)
    item["evidencias"] = [{"id": "I1", "passagem": p} for p in
                           ["Futsal: 9h", "Local: Quadra Exemplo"]]
    assert validar_analise(json.dumps([item]), trechos) == [item]


def test_lacuna_sem_inventar_preco():
    texto = Mock(model="texto-teste")
    item = {"duvida": "Quanto custa?", "estado": "lacuna", "conclusao": "O cartaz não informa preço.",
            "trechos": [], "evidencias": []}
    parecer = {"aprovado": True, "criterios": {k: True for k in (
        "sustentacao", "condicoes", "completude", "temporalidade", "lacunas_conflitos")},
        "problemas": [], "consulta_complementar": ""}
    texto.complete.side_effect = [json.dumps([item]), json.dumps(parecer)]
    resultado = responder_imagem("Quanto custa?", png(), agente=agente(), cliente_texto=texto)
    assert resultado["itens"][0]["estado"] == "lacuna"
    assert resultado["itens"][0]["trechos"] == []


def test_reprovacao_nao_publica_rascunho_apos_correcao(monkeypatch):
    from pontoativo_rag.agentes import multimodal
    item = {"duvida": "Horário?", "estado": "sustentada", "conclusao": "Futsal às 9h",
            "trechos": ["I1"], "evidencias": [{"id": "I1", "passagem": "Futsal às 9h"}]}
    texto = Mock(model="texto-teste")
    texto.complete.return_value = json.dumps([item])
    revisor = Mock()
    revisor.revisar.return_value = {"aprovado": False, "problemas": [{"item": 1,
        "trecho_rascunho": "Futsal às 9h", "criterio": "temporalidade",
        "correcao": "Preserve a data do cartaz."}]}
    monkeypatch.setattr(multimodal, "AgenteValidacao", lambda _: revisor)
    resultado = responder_imagem("Horário?", png(), agente=agente(), cliente_texto=texto)
    assert resultado["modo"] == "falha_validacao"
    assert resultado["itens"] == []
    assert revisor.revisar.call_count == 2


def test_avisos_do_sistema_nao_sao_evidencias_do_cartaz():
    texto = Mock(model="texto-teste")
    texto.complete.return_value = "[]"
    resultado = responder_imagem("Horário?", png(), agente=agente(), cliente_texto=texto)
    entrada = json.loads(texto.complete.call_args_list[0].args[1])
    assert "ressalvas" not in entrada["documentos"][0]["fonte"]
    assert entrada["documentos"][0]["texto"] == "Futsal às 9h"
    assert "transcrição automática" in resultado["avisos"][0]
