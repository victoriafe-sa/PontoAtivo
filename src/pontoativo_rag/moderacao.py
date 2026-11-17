"""Detecção de termos impróprios antes de qualquer chamada ao modelo.

O classificador de linguagem pode reescrever a pergunta e descartar justamente
a parte imprópria ("campo de futebol e sexo" vira "campo de futebol"). Esta
checagem é determinística: olha cada palavra escrita, inclusive com acentos
trocados, letras repetidas ou números no lugar de letras, e devolve o termo
encontrado para que a resposta possa apontá-lo.

A lista compara palavras inteiras ou radicais bem delimitados, para não
bloquear palavras comuns como "sexta", "Essex", "computador" ou "disputa".
"""

from __future__ import annotations

import re
import unicodedata

# Palavras inteiras (já sem acento, em minúsculas e sem letras repetidas).
_PALAVRAS = {
    # conteúdo sexual
    "sexo", "sex", "transar", "transa", "transando", "transei", "orgia", "orgias",
    "nude", "nudes", "nudez", "motel", "moteis", "prostituta", "prostitutas",
    "prostituicao", "programa adulto", "puta", "putas", "puteiro", "boquete",
    "punheta", "siririca", "gozada", "tesao", "safadeza", "safado", "safada",
    "pelada nua", "xoxota", "xereca", "buceta", "boceta", "piroca", "pica", "rola grossa",
    "pau duro", "cu", "cuzao", "anal", "fetiche", "suruba", "erotico", "erotica",
    # palavrões
    "porra", "caralho", "foder", "fuder", "foda", "fodase", "fodido", "fodida",
    "merda", "bosta", "cacete", "arrombado", "arrombada", "desgraca", "otario", "otaria",
    "babaca", "imbecil", "idiota",
    # ofensas e preconceito
    "viado", "veado", "bicha", "traveco", "sapatao", "retardado", "retardada",
    "mongoloide", "crioulo", "favelado",
}

# Radicais: a palavra começa assim (cobre plurais e variações).
_RADICAIS = (
    "sexu",      # sexual, sexuais, sexualidade
    "porn",      # pornô, pornografia
    "putari",    # putaria
    "punhet",
    "bucet",
    "bocet",
    "caralh",
    "fodend", "fudend",
    "prostitu",
    "pedofil",
    "estupr",
)

# Expressões de mais de uma palavra.
_EXPRESSOES = (
    "garota de programa", "garoto de programa", "fazer programa", "casa de massagem",
    "filho da puta", "vai se foder", "vai tomar no",
)

# Palavras que começam como um radical, mas são comuns e inofensivas.
_EXCECOES = {"sexta", "sextas", "essex", "estupendo", "estupenda"}

_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})


def _colapsar(texto: str) -> str:
    """Letras repetidas viram uma só, dos dois lados da comparação ("porra" -> "pora")."""
    return re.sub(r"([a-z])\1+", r"\1", texto)


_PALAVRAS = {_colapsar(p) for p in _PALAVRAS}
_RADICAIS = tuple(_colapsar(r) for r in _RADICAIS)
_EXPRESSOES = tuple(_colapsar(e) for e in _EXPRESSOES)
_EXCECOES = {_colapsar(e) for e in _EXCECOES}


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto.casefold())
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    trocado = sem_acento.translate(_LEET)
    # "s.e.x.o", "s-e-x-o" e "s e x o": junta letras soltas separadas por pontuação ou espaço.
    trocado = re.sub(r"\b(?:[a-z][\s.\-_*]){2,}[a-z]\b",
                     lambda m: re.sub(r"[\s.\-_*]", "", m.group()), trocado)
    # "seeexxxo" -> "sexo": letras repetidas viram uma só.
    return re.sub(r"[^a-z\s]", " ", _colapsar(trocado))


def termo_improprio(texto: str) -> str | None:
    """Devolve o primeiro termo impróprio encontrado na pergunta, ou None."""
    if not isinstance(texto, str) or not texto.strip():
        return None
    normalizado = _normalizar(texto)
    palavras = normalizado.split()
    frase = " ".join(palavras)
    for expressao in _EXPRESSOES:
        if re.search(rf"\b{re.escape(expressao)}\b", frase):
            return expressao
    for indice, palavra in enumerate(palavras):
        if palavra in _EXCECOES:
            continue
        if palavra in _PALAVRAS or palavra.startswith(_RADICAIS):
            return _original(texto, indice) or palavra
        if indice + 1 < len(palavras) and f"{palavra} {palavras[indice + 1]}" in _PALAVRAS:
            return f"{palavra} {palavras[indice + 1]}"
    return None


def _original(texto: str, indice: int) -> str | None:
    """Recupera a palavra como a pessoa escreveu, para mostrar na resposta."""
    originais = re.findall(r"[\w@$]+", texto)
    if len(originais) == len(_normalizar(texto).split()):
        return originais[indice]
    return None
