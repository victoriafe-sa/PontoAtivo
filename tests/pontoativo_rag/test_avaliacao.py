from pontoativo_rag.avaliacao import (
    EvaluationQuestion,
    compare_evaluations,
    factual_answer_metrics,
    quality_gate_failures,
    recall_at_k,
    score_question,
    summarize,
)
from pontoativo_rag.geracao import GroundedAnswer
from pontoativo_rag.recuperacao import RetrievedChunk


def _chunk(source_id: str, distance: float, text: str = "texto") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"c-{source_id}-{distance}",
        source_id=source_id,
        title="t",
        institution="i",
        location="https://df.gov.br",
        text=text,
        distance=distance,
        matched_segments=1,
    )


def _question(answerable: bool, sources=()) -> EvaluationQuestion:
    return EvaluationQuestion(
        id="Q", categoria="c", pergunta="?", respondivel=answerable,
        fontes_relevantes=tuple(sources),
    )


def test_recall_por_fonte() -> None:
    assert recall_at_k(("A", "B"), ["B", "C"]) == 0.5
    assert recall_at_k(("A",), ["A", "A"]) == 1.0
    assert recall_at_k((), ["A"]) is None


def test_pontuacao_de_resposta_com_citacao_relevante() -> None:
    chunks = [_chunk("A", 0.2), _chunk("B", 0.3)]
    result = GroundedAnswer("?", "rag", "x [F1]", chunks, cited=[chunks[0]], generation_seconds=1.0)

    row = score_question(_question(True, ["A"]), result, 0.5)

    assert row["recall_at_k"] == 1.0
    assert row["citou_fonte_relevante"] is True
    assert row["melhor_distancia"] == 0.2
    assert row["falsa_abstencao"] is False
    assert row["fontes_irrelevantes_no_topo"] == [
        {"rank": 2, "source_id": "B"}
    ]


def test_avaliacao_factual_mede_citacao_e_suporte() -> None:
    chunk = _chunk("A", 0.2, "O COP oferece natação e atletismo.")
    result = GroundedAnswer(
        "Quais modalidades?",
        "rag",
        "O COP oferece natação [F1].\nTambém oferece atletismo [F1].",
        [chunk],
        cited=[chunk],
    )

    metrics = factual_answer_metrics(result)

    assert metrics["citation_coverage"] == 1.0
    assert metrics["factual_support"] == 1.0
    assert metrics["unsupported_claims"] == 0


def test_avaliacao_factual_detecta_afirmacao_sem_suporte() -> None:
    chunk = _chunk("A", 0.2, "O COP oferece natação.")
    result = GroundedAnswer(
        "Quais modalidades?",
        "rag",
        "O COP oferece natação [F1].\nO local tem estacionamento gratuito [F1].",
        [chunk],
        cited=[chunk],
    )

    metrics = factual_answer_metrics(result)

    assert metrics["citation_coverage"] == 1.0
    assert metrics["factual_support"] == 0.5
    assert metrics["unsupported_claims"] == 1


def test_uma_palavra_generica_em_comum_nao_comprova_afirmacao() -> None:
    chunk = _chunk("A", 0.2, "O COP oferece natação e atletismo.")
    result = GroundedAnswer(
        "Quais modalidades?", "rag", "O COP oferece futebol [F1].", [chunk], cited=[chunk]
    )

    metrics = factual_answer_metrics(result)

    assert metrics["factual_support"] == 0.0
    assert metrics["unsupported_claims"] == 1


def test_avaliacao_factual_associa_citacao_em_linha_separada() -> None:
    chunk = _chunk("A", 0.2, "O COP oferece natação.")
    result = GroundedAnswer(
        "Qual modalidade?",
        "rag",
        "O COP oferece natação.\n[ F1 ]",
        [chunk],
        cited=[chunk],
    )

    metrics = factual_answer_metrics(result)

    assert metrics["citation_coverage"] == 1.0


def test_avaliacao_ignora_metadado_de_citacao_e_cabecalho() -> None:
    chunk = _chunk("A", 0.2, "O COP oferece natação.")
    result = GroundedAnswer(
        "Quais equipamentos?",
        "rag",
        "O COP oferece natação [F1].\nCitei os documentos [F1].\n"
        "Equipamentos disponíveis:",
        [chunk],
        cited=[chunk],
    )

    metrics = factual_answer_metrics(result)

    assert metrics["citation_coverage"] == 1.0
    assert metrics["unsupported_claims"] == 0


def test_resumo_conta_abstencoes_corretas_e_falsas() -> None:
    abstention = GroundedAnswer("?", "abstencao", "Não encontrei", [_chunk("Z", 0.9)])
    rows = [
        score_question(_question(False), abstention, 0.1),
        score_question(_question(True, ["A"]), abstention, 0.1),
    ]

    summary = summarize(rows)

    assert summary["abstencoes_corretas"] == 1
    assert summary["falsas_abstencoes"] == 1
    assert summary["recall_medio_at_k"] == 0.0


def test_portao_de_qualidade_aprova_metricas_minimas() -> None:
    summary = {
        "recall_medio_at_k": 0.97,
        "acerto_ao_menos_uma_fonte": 1.0,
        "falsas_abstencoes": 0,
        "citacoes_invalidas": 0,
        "cobertura_media_citacoes": 1.0,
        "suporte_factual_medio": 1.0,
        "afirmacoes_sem_suporte": 0,
        "geracoes_incompletas": 0,
    }

    assert quality_gate_failures(summary) == []


def test_portao_de_qualidade_identifica_regressao() -> None:
    summary = {
        "recall_medio_at_k": 0.89,
        "acerto_ao_menos_uma_fonte": 0.90,
        "falsas_abstencoes": 1,
        "citacoes_invalidas": 2,
        "geracoes_incompletas": 1,
    }

    failures = quality_gate_failures(summary)

    assert len(failures) == 5
    assert any("Recall@k" in failure for failure in failures)
    assert any("citações inválidas" in failure for failure in failures)
    assert any("gerações incompletas" in failure for failure in failures)


def test_comparacao_identifica_nova_fonte_irrelevante_no_top3() -> None:
    previous = (
        {},
        {"recall_medio_at_k": 0.9, "acerto_ao_menos_uma_fonte": 1.0},
        [{"id": "Q", "recall_at_k": 1.0, "fontes_relevantes": ["A"],
          "fontes_recuperadas": ["A", "B"]}],
    )
    current = (
        {},
        {"recall_medio_at_k": 0.95, "acerto_ao_menos_uma_fonte": 1.0},
        [{"id": "Q", "recall_at_k": 1.0, "fontes_relevantes": ["A"],
          "fontes_recuperadas": ["A", "C", "B"]}],
    )

    comparison = compare_evaluations(previous, current)

    assert comparison["variacao"]["recall_medio_at_k"] == 0.05
    assert comparison["novas_fontes_irrelevantes_no_top3"] == [
        {"id": "Q", "fontes": ["C"]}
    ]


def test_suporte_factual_trata_singular_plural_e_maiusculas_como_mesmo_termo() -> None:
    from pontoativo_rag.avaliacao import _terms

    assert _terms("Alunos idosos") == _terms("aluno idoso") == {"aluno", "idoso"}
    assert _terms("Professores, Inscrições e Atividades anuais") == {
        "professor", "inscricao", "atividade", "anual"
    }

    chunk = _chunk("A", 0.2, "São isentos da taxa: Aluno com deficiência; Aluno idoso.")
    result = GroundedAnswer(
        "Quem é isento?",
        "rag",
        "Alunos com deficiência [F1].\nAlunos idosos [F1].",
        [chunk],
        cited=[chunk],
    )

    metrics = factual_answer_metrics(result)

    assert metrics["unsupported_claims"] == 0
    assert metrics["factual_support"] == 1.0


def test_plural_nao_cria_suporte_com_uma_unica_palavra() -> None:
    chunk = _chunk("A", 0.2, "Os alunos fazem natação pela manhã.")
    result = GroundedAnswer(
        "Q?", "rag", "Alunos pagam mensalidade em dinheiro [F1].", [chunk], cited=[chunk]
    )

    assert factual_answer_metrics(result)["unsupported_claims"] == 1


def test_enderecos_com_numero_contam_como_termos():
    from pontoativo_rag.avaliacao import _terms

    termos = _terms("PECs em SQN 103, EQN 112/113 e SGAN 905")

    assert {"sqn103", "eqn112/113", "sgan905"} <= termos
    assert "sqn104" not in termos  # endereço diferente não coincide


def test_avaliador_nao_quebra_frase_em_abreviacao_de_uma_letra():
    from pontoativo_rag.avaliacao import _answer_sentences

    assert _answer_sentences("Há um PEC na Praça Resistência na V. Telebrasília [F1].") == [
        "Há um PEC na Praça Resistência na V. Telebrasília [F1]."
    ]


def test_numeros_listados_a_parte_do_endereco_contam_como_suporte() -> None:
    # Caso real (Q12 com o E5): as quadras vêm listadas depois do setor.
    fonte = "388 PONTO DE ENCONTRO COMUNITÁRIO SQNW 108\n389 PONTO DE ENCONTRO COMUNITÁRIO SQNW 109\n390 PONTO DE ENCONTRO COMUNITÁRIO SQNW 111"
    chunk = _chunk("A", 0.1, fonte)
    certa = GroundedAnswer("Onde?", "rag", "A lista inclui locais no setor SQNW, como as quadras 108, 109 e 111 [F1].", [chunk], cited=[chunk])
    errada = GroundedAnswer("Onde?", "rag", "A lista inclui locais no setor SQNW, como as quadras 205, 206 e 207 [F1].", [chunk], cited=[chunk])
    assert factual_answer_metrics(certa)["unsupported_claims"] == 0
    assert factual_answer_metrics(errada)["unsupported_claims"] == 1
