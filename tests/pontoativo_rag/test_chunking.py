from pontoativo_rag.modelos import (
    DocumentPage,
    NormalizedDocument,
    SourceRecord,
)
from pontoativo_rag.processamento import (
    create_embedding_segments,
    create_parent_chunks,
)


def _document(text: str, *, pages=()) -> NormalizedDocument:
    return NormalizedDocument(
        source=SourceRecord(
            source_id="fonte-001",
            title="Fonte oficial",
            institution="GDF",
            location="https://df.gov.br/fonte",
            document_type="html",
            subject="esporte",
            verification_status="verificado",
            administrative_region="Ceilândia",
        ),
        text=text,
        checksum_sha256="abc123",
        pages=tuple(pages),
    )


def test_tabela_georreferenciada_separa_trechos_por_tipo_de_equipamento() -> None:
    linhas = ["RELAÇÃO DE EQUIPAMENTOS PÚBLICOS REGIÃO ADMINISTRATIVA PLANO PILOTO"]
    enderecos = ["SQN 102", "SQS 204", "SHCGN 705", "V. PLANALTO - AV. RABELO"]
    linhas += [f"{n} PARQUE INFANTIL {e} -15.77{n}, -47.88{n}" for n, e in enumerate(enderecos, 1)]
    linhas += [f"{n} QUADRA DE ESPORTE {e} -15.81{n}, -47.89{n}" for n, e in enumerate(enderecos, 5)]
    linhas += [f"{n} PONTO DE ENCONTRO COMUNITÁRIO {e} -15.74{n}, -47.90{n}" for n, e in enumerate(enderecos, 9)]
    document = _document("\n".join(linhas), pages=[DocumentPage(1, "\n".join(linhas))])

    chunks = create_parent_chunks(document, target_tokens=450, overlap_tokens=50)
    by_section = {chunk.section: chunk for chunk in chunks}

    assert set(by_section) == {"", "PARQUE INFANTIL", "QUADRA DE ESPORTE", "PONTO DE ENCONTRO COMUNITÁRIO"}
    pec = by_section["PONTO DE ENCONTRO COMUNITÁRIO"]
    assert "QUADRA" not in pec.text and pec.text.count("PONTO DE ENCONTRO") == 4
    assert pec.entity_key == "ponto-de-encontro-comunitário"
    assert "PONTO DE ENCONTRO COMUNITÁRIO" in create_embedding_segments(pec)[0].embedding_input


def test_secao_sobre_outro_cop_recebe_a_regiao_desse_cop() -> None:
    texto = (
        "1.2 COP SETOR O\nO complexo do Setor O tem piscinas e quadras cobertas.\n"
        "1.3 COP SOBRADINHO\nO complexo de Sobradinho tem pista de atletismo e campo.\n"
        "2. PROPOSTA PEDAGÓGICA\nAs aulas seguem o plano pedagógico do programa."
    )
    chunks = create_parent_chunks(_document(texto), target_tokens=450, overlap_tokens=50)
    region = {chunk.section: chunk.administrative_region for chunk in chunks}

    assert region["1.3 COP SOBRADINHO"] == "Sobradinho"
    assert region["1.2 COP SETOR O"] == "Ceilândia"  # sem RA na seção: região da fonte
    assert region["2. PROPOSTA PEDAGÓGICA"] == "Ceilândia"


def test_fonte_nacional_nao_ganha_regiao_por_nome_de_clube() -> None:
    from dataclasses import replace

    base = _document("# Sociedade Esportiva Vasco da Gama\nClube com modalidades paralímpicas no Rio.")
    document = replace(base, source=replace(base.source, administrative_region=""))

    chunks = create_parent_chunks(document, target_tokens=450, overlap_tokens=50)

    assert [chunk.administrative_region for chunk in chunks] == [""]


def test_linhas_com_coordenadas_isoladas_nao_criam_secao() -> None:
    texto = "Endereço do COP: 1 GINÁSIO CENTRAL -15.8, -48.1\nTexto corrido sobre o local."
    chunks = create_parent_chunks(_document(texto), target_tokens=450, overlap_tokens=50)

    assert [chunk.section for chunk in chunks] == [""]


def test_documento_curto_vira_um_chunk_e_um_segmento() -> None:
    document = _document("Espaço público com atividade esportiva adaptada.")

    chunks = create_parent_chunks(document, target_tokens=450, overlap_tokens=50)
    segments = create_embedding_segments(chunks[0], max_tokens=120)

    assert len(chunks) == 1
    assert chunks[0].text == document.text
    assert chunks[0].source_id == "fonte-001"
    assert len(segments) == 1
    assert segments[0].parent_chunk_id == chunks[0].chunk_id


def test_chunks_longos_tem_sobreposicao_e_ids_estaveis() -> None:
    words = [f"palavra{i}" for i in range(1_050)]
    document = _document(" ".join(words))

    first_run = create_parent_chunks(document, target_tokens=450, overlap_tokens=50)
    second_run = create_parent_chunks(document, target_tokens=450, overlap_tokens=50)

    assert [chunk.chunk_id for chunk in first_run] == [
        chunk.chunk_id for chunk in second_run
    ]
    assert len(first_run) == 3
    assert first_run[0].text.split()[-50:] == first_run[1].text.split()[:50]
    assert all(len(chunk.text.split()) <= 450 for chunk in first_run)


def test_segmentos_respeitam_limite_do_modelo() -> None:
    document = _document(" ".join(f"termo{i}" for i in range(450)))
    chunk = create_parent_chunks(document)[0]

    segments = create_embedding_segments(chunk, max_tokens=120)

    assert len(segments) == 4
    assert all(len(segment.text.split()) <= 120 for segment in segments)
    assert len({segment.segment_id for segment in segments}) == 4


def test_chunk_preserva_pagina_e_metadados() -> None:
    pages = (
        DocumentPage(page_number=1, text="Conteúdo da primeira página."),
        DocumentPage(page_number=2, text="Conteúdo da segunda página."),
    )
    document = _document("\n\n".join(page.text for page in pages), pages=pages)

    chunks = create_parent_chunks(document)

    # Sem títulos, páginas curtas da mesma seção formam um chunk com intervalo.
    assert len(chunks) == 1
    assert (chunks[0].page_number, chunks[0].page_end) == (1, 2)
    assert chunks[0].administrative_region == "Ceilândia"
    assert chunks[0].location == "https://df.gov.br/fonte"


def test_entrada_do_embedding_inclui_titulo_mas_texto_citado_nao() -> None:
    chunk = create_parent_chunks(_document("Piscina semiolímpica coberta."))[0]
    segment = create_embedding_segments(chunk)[0]

    assert segment.embedding_input == "Fonte oficial\nPiscina semiolímpica coberta."
    assert segment.text == "Piscina semiolímpica coberta."


def test_secao_continua_entre_paginas_e_titulo_inicia_novo_chunk() -> None:
    # Reproduz a falha real da DOC-004: a lista do COP Vaquejada continua na
    # página seguinte, antes do título do COP Setor O.
    pages = (
        DocumentPage(1, "1.1 COP PARQUE DA VAQUEJADA\nModalidades:\na) Bocha\nb) Natação"),
        DocumentPage(2, "c) Parabadminton\nd) Atletismo adaptado\n\n"
                        "1.2 COP SETOR “O” (CEILÂNDIA)\n1.2.1 EQUIPAMENTOS\n- Piscina"),
    )
    document = _document("\n\n".join(p.text for p in pages), pages=pages)

    chunks = create_parent_chunks(document)

    vaquejada, setor_o = chunks
    assert vaquejada.section == "1.1 COP PARQUE DA VAQUEJADA"
    assert "a) Bocha" in vaquejada.text and "c) Parabadminton" in vaquejada.text
    assert (vaquejada.page_number, vaquejada.page_end) == (1, 2)
    assert "SETOR" not in vaquejada.text
    assert setor_o.section == "1.2 COP SETOR “O” (CEILÂNDIA) > 1.2.1 EQUIPAMENTOS"
    assert setor_o.text.startswith("1.2 COP SETOR")
    assert "Piscina" in setor_o.text and "Parabadminton" not in setor_o.text


def test_subsecoes_da_mesma_secao_sao_agrupadas_e_irmas_nao() -> None:
    text = (
        "1.2 COP SAMAMBAIA\nComplexo de grande porte.\n\n"
        "1.2.1 EQUIPAMENTOS\n- Piscina\n- Quadra\n\n"
        "1.3 COP SOBRADINHO\nOutro complexo esportivo."
    )
    chunks = create_parent_chunks(_document(text))

    assert [chunk.section for chunk in chunks] == ["1.2 COP SAMAMBAIA", "1.3 COP SOBRADINHO"]
    assert "Piscina" in chunks[0].text and "SAMAMBAIA" in chunks[0].text
    assert "Piscina" not in chunks[1].text


def test_item_de_lista_numerado_nao_e_titulo() -> None:
    from pontoativo_rag.processamento import detect_heading

    assert detect_heading("1. Atividade Física Orientada (AFO)") is None
    assert detect_heading("5.2. O quadro geral de vagas") is None
    assert detect_heading("1.2.2 MODALIDADES OFERECIDAS") == (3, "1.2.2 MODALIDADES OFERECIDAS")
    assert detect_heading("## Como funciona o CPB?") == (2, "Como funciona o CPB?")


def test_chunk_preserva_quebras_de_linha_de_listas() -> None:
    chunk = create_parent_chunks(_document("Modalidades:\n- Natação\n- Bocha"))[0]

    assert chunk.text == "Modalidades:\n- Natação\n- Bocha"
    assert chunk.structure_kind == "lista"
    assert chunk.entity_key == "fonte-oficial"


def test_paragrafos_inteiros_sao_mantidos_quando_cabem() -> None:
    first = " ".join(["alfa"] * 300)
    second = " ".join(["beta"] * 300)
    chunks = create_parent_chunks(_document(f"{first}\n\n{second}"), 450, 50)

    assert len(chunks) == 2
    assert chunks[0].text == first
    # o segundo começa com a sobreposição e contém o parágrafo inteiro
    assert chunks[1].text.endswith(second)
    assert chunks[1].text.split()[:50] == ["alfa"] * 50


def test_falsos_titulos_comuns_em_pdfs_sao_rejeitados() -> None:
    from pontoativo_rag.processamento import detect_heading

    assert detect_heading("10 DIAS") is None
    assert detect_heading("2. CPF;") is None
    assert detect_heading("2. CNPJ") is None
    assert detect_heading("23 PARQUE INFANTIL SQN 115 -15.73933") is None
    assert detect_heading("1 - INTRODUÇÃO") == (1, "1 - INTRODUÇÃO")
