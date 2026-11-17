import json
from pathlib import Path

import pytest

from pontoativo_rag.moderacao import termo_improprio

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("pergunta", "termo"),
    [
        ("campo de futebol e sexo em brasilia", "sexo"),
        ("como tem quadra de sexo na Ceilândia?", "sexo"),
        ("Campo de futebol e SEXO em Brasília", "SEXO"),
        ("quadra pra fazer putaria no guará", "putaria"),
        ("parque bom pra transar", "transar"),
        ("seeexxxo no parque da cidade", "seeexxxo"),
        ("s3x0 em taguatinga", "s3x0"),
        ("quadra para s.e.x.o", "sexo"),
        ("local com conteúdo sexual", "sexual"),
        ("onde tem pornografia", "pornografia"),
        ("garota de programa perto do PEC", "garota de programa"),
        ("porra, cadê o campo?", "porra"),
        ("quadra pra viado jogar", "viado"),
        ("academia para retardado", "retardado"),
    ],
)
def test_detecta_termos_improprios_e_aponta_a_palavra(pergunta, termo):
    assert termo_improprio(pergunta) == termo


@pytest.mark.parametrize(
    "pergunta",
    [
        "campo de futebol em Brasília",
        "jogar bola na sexta-feira em Taguatinga",
        "aula de natação para idosos na sexta",
        "quadra de vôlei de areia no Guará",
        "COP de Ceilândia tem vaga para pessoa com deficiência?",
        "disputa de futsal no computador do COP",
        "onde fica o parque da cidade",
        "pista de skate perto do Essex",
        "transporte até o centro olímpico",
        "como faço matrícula na escola de esportes?",
        "pelada de futebol no domingo",
        "quero correr no Parque Ecológico",
        "",
        "   ",
    ],
)
def test_nao_bloqueia_perguntas_esportivas_comuns(pergunta):
    assert termo_improprio(pergunta) is None


def test_nenhuma_pergunta_da_avaliacao_e_bloqueada():
    linhas = (ROOT / "dados" / "perguntas_avaliacao.jsonl").read_text(encoding="utf-8").splitlines()
    perguntas = [json.loads(linha)["pergunta"] for linha in linhas if linha.strip()]
    assert perguntas
    assert {p: termo_improprio(p) for p in perguntas if termo_improprio(p)} == {}


def test_nenhum_nome_de_local_do_mapa_e_bloqueado():
    locais = json.loads(
        (ROOT / "PontoAtivo-CURADORIA" / "data" / "locais-encontros.json").read_text(encoding="utf-8")
    )
    assert len(locais) > 1000
    bloqueados = {
        local["nome"]: termo_improprio(local["nome"] + " " + local["regiao"])
        for local in locais
        if termo_improprio(local["nome"] + " " + local["regiao"])
    }
    assert bloqueados == {}
