import json
from pathlib import Path

from pontoativo_rag import rotas
from pontoativo_rag.web import ROUTES

ROOT = Path(__file__).resolve().parents[2]


def test_perguntas_de_rotas_cobrem_todas_as_rotas_sem_repetir():
    questions = rotas.load_questions(ROOT / "dados" / "rag" / "perguntas" / "rotas.jsonl")
    ids = [q["id"] for q in questions]
    assert len(ids) == len(set(ids)) == 22
    assert {q["rota"] for q in questions} == set(ROUTES)


class FakeChat:
    def __init__(self, answers):
        self.answers = answers

    def classify(self, question):
        answer = self.answers[question]
        if isinstance(answer, Exception):
            raise answer
        return {"rota": answer}


def test_run_model_conta_acertos_erros_e_tempo():
    questions = [
        {"id": "A", "pergunta": "um", "rota": "mapa"},
        {"id": "B", "pergunta": "dois", "rota": "duvidas"},
        {"id": "C", "pergunta": "tres", "rota": "esclarecer"},
    ]
    chat = FakeChat({"um": "mapa", "dois": "documentos", "tres": ValueError("x")})
    ticks = iter([0.0, 1.0, 1.0, 3.0, 3.0, 6.0])
    run = rotas.run_model(chat, questions, clock=lambda: next(ticks))
    assert run["acertos"] == 1 and run["total"] == 3
    assert run["tempo_medio_s"] == 2.0 and run["tempo_max_s"] == 3.0
    assert run["respostas"][2]["obtida"] == "erro" and run["respostas"][2]["erro"] == "ValueError"

    text = rotas.render_markdown({"modelo-x": run}, "16/11/2026 18:00")
    assert "| `modelo-x` | 1/3 | 2.0 s | 3.0 s |" in text
    assert 'B "dois": esperado `duvidas`, obtido `documentos`' in text
