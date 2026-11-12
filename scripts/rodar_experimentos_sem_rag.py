"""Executa Q1–Q20 sem RAG, com parâmetros e registros iguais aos do executor RAG.

Exemplo: python3 scripts/rodar_experimentos_sem_rag.py --modelo llama --inicio 5 --fim 20
"""
from pathlib import Path
import rodar_experimentos_rag as executor


if __name__ == '__main__':
    executor.BASE = Path(__file__).resolve().parents[1] / 'experimentos' / 'experimento-sem-rag'
    executor.main(sem_rag=True)
