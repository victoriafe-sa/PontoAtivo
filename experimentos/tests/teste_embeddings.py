"""Teste rápido do módulo de embeddings, sem banco vetorial.

Rodar a partir da raiz do projeto:
    .venv/bin/python tests/teste_embeddings.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ingestao.embeddings import DIMENSAO, embedding_da_consulta, gerar_embeddings

CHUNKS = [
    "Quadra poliesportiva coberta em Taguatinga Norte, aberta ao público, com marcação para vôlei e futsal.",
    "PEC - Ponto de Encontro Comunitário na SQN 104, Asa Norte, com aparelhos de ginástica ao ar livre.",
    "Piscina pública no Centro Olímpico de Ceilândia; a acessibilidade para cadeirantes não foi verificada.",
    "Pista de skate no Parque da Cidade, próxima ao estacionamento 10.",
    "Campo de futebol society de grama sintética no Gama, aluguel por hora.",
]

# Cada pergunta deve recuperar o chunk do índice indicado.
CONSULTAS = [
    ("onde jogar vôlei em Taguatinga?", 0),
    ("academia ao ar livre na Asa Norte", 1),
    ("natação com acesso para cadeira de rodas", 2),
    ("lugar para andar de skate", 3),
    ("alugar campo de futebol", 4),
]


def similaridade(a, b):
    # Os vetores já são normalizados, então o produto escalar é o cosseno.
    return sum(x * y for x, y in zip(a, b))


def main():
    vetores = gerar_embeddings(CHUNKS)
    assert len(vetores) == len(CHUNKS)
    assert all(len(v) == DIMENSAO for v in vetores)
    print(f"{len(vetores)} chunks -> vetores de {DIMENSAO} dimensões\n")

    acertos = 0
    for pergunta, esperado in CONSULTAS:
        consulta = embedding_da_consulta(pergunta)
        notas = [similaridade(consulta, v) for v in vetores]
        melhor = max(range(len(notas)), key=notas.__getitem__)
        ok = melhor == esperado
        acertos += ok
        print(f"[{'OK' if ok else 'ERRO'}] {pergunta}")
        print(f"       -> {CHUNKS[melhor][:70]}... (similaridade {notas[melhor]:.3f})")

    print(f"\n{acertos}/{len(CONSULTAS)} consultas recuperaram o chunk esperado")
    assert acertos == len(CONSULTAS)


if __name__ == "__main__":
    main()
