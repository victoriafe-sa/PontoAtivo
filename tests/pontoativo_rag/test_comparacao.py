from pathlib import Path
from types import SimpleNamespace

from pontoativo_rag.avaliacao import EvaluationQuestion, load_questions
from pontoativo_rag.comparacao import BASELINE_SYSTEMS, compare_question, render_markdown

ROOT = Path(__file__).resolve().parents[2]


class FakeModel:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def complete(self, system, user, **kwargs):
        self.calls.append((system, user, kwargs))
        return self.reply


def _question():
    return EvaluationQuestion(
        id="Q99", categoria="teste", pergunta="Quantas vagas há?", respondivel=True,
        fontes_relevantes=("DOC-002",), referencia="13.672 vagas",
    )


def _rag(answer="São 13.672 vagas [F1].", mode="rag"):
    chunk = SimpleNamespace(source_id="DOC-002", title="Edital 2025")
    return lambda text: SimpleNamespace(mode=mode, answer=answer, cited=[chunk, chunk])


def test_sem_rag_recebe_so_a_pergunta_nos_dois_cenarios():
    model = FakeModel("  Não sei.  ")
    row = compare_question(_question(), model, _rag())

    assert [call[0] for call in model.calls] == list(BASELINE_SYSTEMS.values())
    assert all(call[1] == "Quantas vagas há?" for call in model.calls)
    assert all(call[2]["options"]["temperature"] == 0 for call in model.calls)
    assert {name: r["resposta"] for name, r in row["sem_rag"].items()} == {
        "simples": "Não sei.", "cautelosa": "Não sei."
    }
    assert "não sabe" in BASELINE_SYSTEMS["cautelosa"]
    assert "não sabe" not in BASELINE_SYSTEMS["simples"]


def test_com_rag_registra_modo_resposta_e_fontes_sem_repetir():
    row = compare_question(_question(), FakeModel("x"), _rag())

    assert row["com_rag"]["modo"] == "rag"
    assert row["com_rag"]["resposta"] == "São 13.672 vagas [F1]."
    assert row["com_rag"]["fontes_citadas"] == ["DOC-002"]
    assert row["com_rag"]["titulos_citados"] == ["Edital 2025"]
    assert row["referencia"] == "13.672 vagas"


def test_markdown_mostra_referencia_e_as_duas_respostas():
    row = compare_question(_question(), FakeModel("Linha 1\n\nLinha 2"), _rag())
    meta = {"executado_em": "2026-11-11T21:00:00", "modelo_llm": "m", "arquivos_perguntas": ["a.jsonl"]}

    text = render_markdown(meta, [row])

    assert "## Q99. Quantas vagas há?" in text
    assert "**Referência:** 13.672 vagas" in text
    assert "> Linha 1\n>\n> Linha 2" in text
    assert "fontes: DOC-002" in text
    assert "**Sem RAG, instrução simples**" in text
    assert "**Sem RAG, instrução cautelosa**" in text


def test_perguntas_da_comparacao_somam_20_com_ids_unicos():
    questions = load_questions(ROOT / "dados" / "perguntas_avaliacao.jsonl") + load_questions(
        ROOT / "dados" / "perguntas_comparacao_extras.jsonl"
    )

    assert len(questions) == 20
    assert len({q.id for q in questions}) == 20
    assert all(q.referencia for q in questions)
