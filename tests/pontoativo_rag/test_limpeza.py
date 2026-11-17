from collections import Counter
from dataclasses import replace

from pontoativo_rag.limpeza import (
    clean_document,
    drop_duplicate_chunks,
    fix_glued_words,
    keep_df_clubs,
    split_glued_numbering,
    split_glued_word,
)
from pontoativo_rag.modelos import DocumentPage, NormalizedDocument, SourceRecord
from pontoativo_rag.processamento import create_parent_chunks


def _doc(source_id="DOC-900", text="", pages=()):
    source = SourceRecord(
        source_id=source_id, title="Fonte", institution="GDF", location="https://df.gov.br",
        document_type="pdf", subject="esporte", verification_status="aprovada",
    )
    return NormalizedDocument(source=source, text=text, checksum_sha256="x", pages=tuple(pages))


def test_cabecalho_repetido_na_maioria_das_paginas_sai():
    pages = [DocumentPage(i, f"18/08/2022 14:3{i} SEI/GDF - 93377965 - Termo\nItem {i} do termo.\n"
                             f"PARQUE INFANTIL SQN {100 + i} -15.77{i}, -47.88{i}\nOutro item {i}.\nTexto final {i}.")
             for i in range(1, 7)]
    cleaned = clean_document(_doc(pages=pages))
    assert "SEI/GDF" not in cleaned.text
    # linhas do meio da página que só diferem nos números são conteúdo
    assert cleaned.text.count("PARQUE INFANTIL SQN") == 6


def test_linha_que_aparece_em_poucas_paginas_fica():
    pages = [DocumentPage(i, ("Endereço: Secretaria de Esporte\n" if i < 3 else "") + f"Serviço {i} com texto.")
             for i in range(1, 8)]
    assert clean_document(_doc(pages=pages)).text.count("Endereço: Secretaria") == 2


def test_sumario_pontilhado_e_anotacao_vazia_saem():
    text = "1. Introdução ............................ 4\n(Promulgação partes vetadas)\nArt. 1º Esta Lei institui."
    assert clean_document(_doc(text=text)).text == "Art. 1º Esta Lei institui."


def test_lista_do_cpb_fica_so_com_clubes_do_df():
    text = (
        "Procure as Secretarias da sua cidade.\n## Encontre um Clube\n"
        "### Clube de Maringá\nTelefone: (44) 3011-1382\nEndereço: Av. Colombo, CEP 87.020-000\n"
        "### União dos Atletas Cegos do Distrito Federal\nTelefone: (61) 98229-0965\nEndereço: Riacho Fundo II, CEP 71.882-154\n"
        "### Rede Sarah\nTelefone: N/A\nEndereço: Lago Norte, CEP 71.535-005"
    )
    out = keep_df_clubs(text)
    assert "Procure as Secretarias" in out
    assert "Maringá" not in out
    assert "União dos Atletas Cegos" in out and "Rede Sarah" in out


def test_numeracao_colada_no_titulo_e_separada():
    out = split_glued_numbering("1. Dos alunos e usuários acompanhantes1.1 Aluno: são as crianças")
    assert out == "1. Dos alunos e usuários acompanhantes\n1.1 Aluno: são as crianças"
    assert split_glued_numbering("Lei nº 13.146/2015 e versão 2.0") == "Lei nº 13.146/2015 e versão 2.0"


def test_palavra_colada_separa_so_quando_as_partes_existem():
    vocab = Counter({"de": 50, "entrada": 5, "crianças": 6, "criança": 2, "se": 3, "e": 90,
                     "para": 30, "o": 80, "ofertadas": 2, "oferta": 4, "das": 20})
    assert split_glued_word("deentrada", vocab) == "de entrada"
    assert split_glued_word("criançase", vocab) == "crianças e"
    assert split_glued_word("parao", vocab) == "para o"
    assert split_glued_word("ofertadas", vocab) == "ofertadas"  # palavra que existe fica
    assert split_glued_word("xyzwqk", vocab) == "xyzwqk"


def test_correcao_de_palavras_coladas_usa_o_vocabulario_das_outras_fontes():
    outras = _doc("DOC-004", "Guarita de entrada e Prédio Administrativo " * 3)
    colada = _doc("DOC-005", "Guarita deentrada e PrédioAdministrativo")
    fixed = {d.source.source_id: d for d in fix_glued_words([outras, colada])}
    assert fixed["DOC-005"].text == "Guarita de entrada e Prédio Administrativo"
    assert fixed["DOC-004"].text == outras.text


def test_trecho_identico_de_outra_fonte_e_removido():
    a = create_parent_chunks(_doc("DOC-004", "13. INDICADORES\nTexto do modelo de termo de colaboração."))
    b = create_parent_chunks(_doc("DOC-005", "13. INDICADORES\nTexto do modelo de termo de colaboração."))
    kept, dropped = drop_duplicate_chunks(a + b)
    assert dropped == 1 and [c.source_id for c in kept] == ["DOC-004"]


def test_titulos_da_carta_de_servicos_em_maiusculas():
    text = "PROGRAMA CENTROS OLÍMPICOS E\nPARALÍMPICOS\nDescrição do programa.\nCLASSIFICAÇÃO A B C D\nValores."
    chunks = create_parent_chunks(_doc("DOC-001", text))
    assert {c.section for c in chunks} == {"PROGRAMA CENTROS OLÍMPICOS E PARALÍMPICOS"}


def test_titulos_das_leis_levam_o_nome_da_linha_seguinte():
    text = ("TÍTULO I\nDISPOSIÇÕES PRELIMINARES\nCAPÍTULO I\nDISPOSIÇÕES GERAIS\n"
            "Art. 1º Esta Lei institui o Estatuto.\nCAPÍTULO II\nDA IGUALDADE\nArt. 4º Toda pessoa tem direito.")
    sections = [c.section for c in create_parent_chunks(_doc("DOC-014", text))]
    assert sections == [
        "TÍTULO I – DISPOSIÇÕES PRELIMINARES > CAPÍTULO I – DISPOSIÇÕES GERAIS",
        "TÍTULO I – DISPOSIÇÕES PRELIMINARES > CAPÍTULO II – DA IGUALDADE",
    ]


def test_titulos_numerados_do_manual():
    text = "7. Do descumprimento do Termo\n7.1 Falta leve\nAtrasos contínuos;\n7.3 Falta Grave\nAgredir fisicamente."
    sections = [c.section for c in create_parent_chunks(_doc("DOC-003", text))]
    assert "7. Do descumprimento do Termo > 7.3 Falta Grave" in sections


def test_fonte_sem_regra_nao_ganha_titulos_novos():
    text = "PROGRAMA CENTROS OLÍMPICOS E\nPARALÍMPICOS\n1. Introdução\nTexto."
    assert {c.section for c in create_parent_chunks(_doc("DOC-900", text))} == {""}


def test_link_de_impressao_do_sei_sai():
    from pontoativo_rag.limpeza import remove_noise

    text = ("https://sei.df.gov.br/sei/controlador.php?acao=documento_imprimir_web&id=1 1/9\n"
            "Item 1 do termo.\nCompartilhe\n:\nTexto final.")
    assert remove_noise(_doc(text=text)).text == "Item 1 do termo.\nTexto final."


def _html(source_id, text):
    doc = _doc(source_id, text)
    return replace(doc, source=replace(doc.source, document_type="html"))


def test_abertura_das_paginas_html_antes_do_titulo_sai():
    noticia = "02/07/2026 às 09h56 - Atualizado em 26/10/2026 às 09h32\n# Novo PEC\nTexto."
    aba = "Aplicativo fitness — Agência Gov\n\nAgricultura\n# Aplicativo fitness\nTexto."
    assert clean_document(_html("DOC-009", noticia)).text == "# Novo PEC\nTexto."
    assert clean_document(_html("DOC-023", aba)).text == "# Aplicativo fitness\nTexto."


def test_html_sem_titulo_no_inicio_fica_igual():
    text = "Linha 1\nLinha 2\nLinha 3\nLinha 4\nLinha 5\nLinha 6\n# Título tardio\nTexto."
    assert clean_document(_html("DOC-900", text)).text == text


def test_palavras_coladas_em_sequencia_e_por_virgula():
    vocab = Counter({"nos": 9, "jogos": 5, "coletivos": 4, "as": 30, "competições": 3, "antes": 6, "dos": 40})
    assert split_glued_word("nosjogoscoletivos", vocab) == "nos jogos coletivos"
    assert split_glued_word("ascompetiçõesantesdos", vocab) == "as competições antes dos"
    outras = _doc("DOC-004", "evitar nos jogos coletivos as competições antes dos 12 anos " * 3)
    colada = _doc("DOC-005", "devem evitar,nosjogoscoletivos,ascompetições antes")
    fixed = {d.source.source_id: d for d in fix_glued_words([outras, colada])}
    assert fixed["DOC-005"].text == "devem evitar, nos jogos coletivos, as competições antes"


def test_trechos_so_com_titulos_ou_artigos_vetados_saem():
    from pontoativo_rag.limpeza import drop_empty_chunks

    vazios = ["Seção V\nArt. 24.", "Seção III\nArt. 20. (VETADO).\nArt. 21.",
              "CAPÍTULO II – DO SISTEMA NACIONAL DO ESPORTE E\nINDICADORES ESPORTIVOS"]
    cheio = "Seção I\nArt. 1º Esta Lei institui a Lei Geral do Esporte."
    chunks = [c for i, t in enumerate(vazios + [cheio]) for c in create_parent_chunks(_doc(f"DOC-9{i:02d}", t))]
    kept, dropped = drop_empty_chunks(chunks)
    assert dropped == 3 and [c.text for c in kept] == [cheio]


def test_numeros_colados_se_separam_mas_horarios_ficam():
    from pontoativo_rag.limpeza import unglue

    vocab = Counter({"antes": 5, "dos": 9, "anos": 7, "às": 4})
    assert unglue("antes dos12anos, às16h e 7h40 por 50min", vocab) == "antes dos 12 anos, às 16h e 7h40 por 50min"


def test_frase_colada_do_doc005_e_corrigida():
    outras = _doc("DOC-004", "evitar as competições antes dos anos " * 3)
    colada = _doc("DOC-005", "evitar,nosjogosdesportivoscoletivos,ascompetiçõesantesdos12anos,asquaisexigemperfeição dos")
    assert fix_glued_words([outras, colada])[1].text == (
        "evitar, nos jogos desportivos coletivos, as competições antes dos 12 anos, as quais exigem perfeição dos")