"""Testes do chunking, com os documentos reais de dados/fontes/texto/.

Rodar a partir da raiz do projeto:
    python tests/teste_chunking.py
"""

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from ingestao.chunking import (  # noqa: E402
    SOBREPOSICAO, TAMANHO_CHUNK, TAMANHO_CHUNK_REGISTROS,
    chunkar_pasta, ler_fonte, listar_fontes,
)

PASTA = RAIZ / "dados" / "fontes" / "texto"
CAMPOS_OBRIGATORIOS = ["id_fonte", "titulo", "orgao", "link", "data_coleta",
                       "validacao", "ressalvas", "comprova_funcionamento"]


def normalizar(t):
    return " ".join(t.split())


def main():
    chunks, _ = chunkar_pasta(PASTA)
    fontes = listar_fontes(PASTA)

    assert len(fontes) == 25, f"esperava 25 fontes, achei {len(fontes)}"

    ids = [c["id"] for c in chunks]
    assert len(ids) == len(set(ids)), "há ids repetidos"

    for c in chunks:
        meta = c["metadados"]
        limite = TAMANHO_CHUNK_REGISTROS if meta["tipo_chunk"] == "registros" else TAMANHO_CHUNK
        assert len(c["texto"]) <= limite, f"{c['id']} passa do limite ({len(c['texto'])})"
        for campo in CAMPOS_OBRIGATORIOS:
            assert meta[campo], f"{c['id']} sem {campo}"
        assert not re.search(r"\b(Arts?|Inc|Dr|Dra)\.$", c["texto"]), \
            f"{c['id']} termina em abreviação: ...{c['texto'][-30:]}"
        assert c["texto_indexado"].endswith(c["texto"])

    # Todo chunk de texto começa em início de palavra e é um trecho contíguo
    # (a menos de espaços) do corpo original.
    corpos = {}
    for caminho in fontes:
        meta, corpo = ler_fonte(caminho)
        corpos[meta["id_fonte"]] = normalizar(corpo)
    for c in chunks:
        if c["metadados"]["tipo_chunk"] != "texto":
            continue
        corpo = corpos[c["metadados"]["id_fonte"]]
        t = normalizar(c["texto"])
        pos = corpo.find(t)
        assert pos >= 0, f"{c['id']} não é trecho contíguo da fonte"
        assert pos == 0 or corpo[pos - 1] == " ", f"{c['id']} começa no meio de palavra"

    # Registros de cadastro: cabeçalho de colunas repetido, nenhum registro cortado.
    for c in chunks:
        if c["metadados"]["tipo_chunk"] == "registros":
            assert "Colunas:" in c["texto"], f"{c['id']} sem cabeçalho de colunas"
            for linha in c["texto"].splitlines()[2:]:
                assert linha.count(" | ") >= 3, f"{c['id']} registro cortado: {linha[:60]}"

    por_fonte = {}
    for c in chunks:
        por_fonte.setdefault(c["metadados"]["id_fonte"], 0)
        por_fonte[c["metadados"]["id_fonte"]] += 1
    assert all(n == c["metadados"]["total_chunks"] for c in chunks
               for n in [por_fonte[c["metadados"]["id_fonte"]]])

    print(f"OK: {len(fontes)} fontes, {len(chunks)} chunks, "
          f"limite {TAMANHO_CHUNK}/{TAMANHO_CHUNK_REGISTROS} caracteres, "
          f"sobreposição {SOBREPOSICAO}.")


if __name__ == "__main__":
    main()
