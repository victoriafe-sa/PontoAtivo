"""Teste do banco vetorial e da busca, SEM o modelo de embeddings.

Usa um embedding simples por palavras (hash), só para verificar o encanamento:
carga, contagem, metadados, métrica de cosseno e ordenação da busca. Ele NÃO
mede a qualidade semântica da recuperação; isso é feito com o modelo real na
demonstração.

Rodar a partir da raiz do projeto:
    python tests/teste_banco.py
"""

import hashlib
import math
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from ingestao.banco import obter_cliente, obter_colecao  # noqa: E402
from ingestao.carga import carregar  # noqa: E402
from recuperacao.buscar import buscar  # noqa: E402

DIM = 768


def _vetor(texto):
    sem_acento = unicodedata.normalize("NFKD", texto.lower())
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    v = [0.0] * DIM
    for palavra in re.findall(r"[a-z0-9]{3,}", sem_acento):
        v[int(hashlib.md5(palavra.encode()).hexdigest(), 16) % DIM] += 1.0
    norma = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norma for x in v]


def gerar_falso(textos):
    return [_vetor(t) for t in textos]


def main():
    # Chroma mantém handles nativos do índice abertos no Windows até o processo
    # terminar. Não confundir falha de limpeza temporária com falha de asserção.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        resumo = carregar(caminho_banco=tmp, gerar=gerar_falso)
        colecao = obter_colecao(obter_cliente(tmp))

        assert resumo["fontes"] == 25
        assert colecao.count() == resumo["chunks"]
        print(f"Carga: {resumo['chunks']} chunks de {resumo['fontes']} fontes")

        # A métrica deve ser cosseno.
        configuracao = str(colecao.configuration)
        assert "cosine" in configuracao, f"métrica inesperada: {configuracao}"

        # Os metadados de rastreabilidade chegam ao banco.
        amostra = colecao.get(limit=1, include=["metadatas", "documents"])
        meta = amostra["metadatas"][0]
        for campo in ("id_fonte", "titulo", "orgao", "link", "data_coleta",
                      "validacao", "ressalvas", "comprova_funcionamento"):
            assert meta.get(campo), f"metadado ausente no banco: {campo}"

        # Recuperar um chunk pelo próprio texto indexado deve trazê-lo em 1º,
        # com similaridade ~1. Testa 15 chunks espalhados pela base.
        todos = colecao.get(include=["documents", "metadatas"])
        passo = max(1, len(todos["ids"]) // 15)
        for i in range(0, len(todos["ids"]), passo):
            id_, texto, m = todos["ids"][i], todos["documents"][i], todos["metadatas"][i]
            local = m["regioes"] or m["abrangencia"]
            contexto = m["titulo"] + (f" — {local}" if local else "")
            pergunta = f"{contexto}\n{texto}"  # igual ao texto_indexado
            res = buscar(pergunta, k=3, caminho_banco=tmp,
                         embedding_consulta=_vetor)
            assert res[0]["id"] == id_, f"{id_} não voltou em 1º (veio {res[0]['id']})"
            assert res[0]["similaridade"] > 0.99
            assert res[0]["texto"] == texto
        print("Busca: chunks recuperados em 1º pelo próprio texto (15 amostras)")

        # Filtro por fonte.
        res = buscar("modalidades esportivas", k=5, filtro={"id_fonte": "N03"},
                     caminho_banco=tmp, embedding_consulta=_vetor)
        assert res and all(r["metadados"]["id_fonte"] == "N03" for r in res)

        # Resultados ordenados do mais para o menos similar.
        res = buscar("regras de uso dos centros olímpicos", k=8,
                     caminho_banco=tmp, embedding_consulta=_vetor)
        sims = [r["similaridade"] for r in res]
        assert sims == sorted(sims, reverse=True)
        print("Filtro por fonte e ordenação: OK")
    print("OK")


if __name__ == "__main__":
    main()
