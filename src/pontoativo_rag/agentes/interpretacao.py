"""Identifica intenções e prepara ações para a Pesquisa documental."""

import re
import unicodedata
from typing import Literal, TypedDict

from .contratos import AcaoPesquisa


Intencao = Literal[
    "pesquisar_esportes", "consultar_cadastro", "pesquisar_inclusao",
    "intencao_nao_identificada",
]


class Interpretacao(TypedDict):
    pergunta_original: str
    acao_identificada: Intencao
    status: Literal["interpretado"]


_REGRAS: tuple[tuple[Intencao, re.Pattern[str]], ...] = (
    ("pesquisar_esportes", re.compile(r"\b(?:esportes?|modalidades?|esportiv[oa]s?)\b")),
    ("consultar_cadastro", re.compile(r"\b(?:cadastros?|cadastrar|inscricao|inscricoes)\b")),
    ("pesquisar_inclusao", re.compile(r"\b(?:inclusao|inclusiv[oa]s?|acessibilidade)\b")),
)


class AgenteInterpretacao:
    def interpretar(self, pergunta: str) -> Interpretacao:
        if not isinstance(pergunta, str) or not pergunta.strip():
            raise ValueError("Informe uma pergunta para interpretar.")
        normalizada = "".join(
            caractere for caractere in unicodedata.normalize("NFKD", pergunta.casefold())
            if not unicodedata.combining(caractere)
        )
        intencao = next(
            (intencao for intencao, regra in _REGRAS if regra.search(normalizada)),
            "intencao_nao_identificada",
        )
        return {
            "pergunta_original": pergunta,
            "acao_identificada": intencao,
            "status": "interpretado",
        }

    def identificar_duvidas(self, pergunta: str) -> list[str]:
        """Separa as perguntas explícitas ("...?"); o contexto antes delas não é dúvida.

        Sem ponto de interrogação, a pergunta inteira é uma única dúvida.
        """
        if not isinstance(pergunta, str) or not pergunta.strip():
            raise ValueError("Informe uma pergunta para interpretar.")
        duvidas = []
        for parte in re.findall(r"[^?]+\?", pergunta):
            # Remove o contexto que antecede a pergunta na mesma parte ("Uso cadeira. Preciso...?").
            frase = re.split(r"(?<=[.!])\s+", parte.strip())[-1]
            duvidas.append(frase)
        return duvidas or [pergunta.strip()]

    def preparar_pesquisa(self, pergunta: str) -> AcaoPesquisa:
        resultado = self.interpretar(pergunta)
        return {
            "consulta": resultado["pergunta_original"].strip(),
            "pergunta_original": resultado["pergunta_original"],
            "tipo": resultado["acao_identificada"],
        }
