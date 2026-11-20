"""Agente de Comunicação: transforma o rascunho aprovado em instruções simples."""

import json
from collections.abc import Sequence
from typing import Literal, TypedDict

from .analise import validar_analise
from .contratos import ItemAnalise, Trecho
from .validacao import Parecer


Status = Literal["respondida", "parcial", "sem_resposta", "precisa_esclarecimento"]


class ComunicacaoRecusada(RuntimeError):
    """O rascunho não foi aprovado pela Validação e não pode ser publicado."""


class Resposta(TypedDict):
    duvida: str
    estado: str
    texto: str
    fontes: list[str]


class FonteCitada(TypedDict):
    ref: str
    id: str
    titulo: str
    instituicao: str
    url: str
    atualidade: str


class Comunicado(TypedDict):
    agente: Literal["comunicacao"]
    pergunta: str
    status: Status
    respostas: list[Resposta]
    fontes: list[FonteCitada]
    proximos_passos: list[str]
    texto: str


# Título de cada seção do texto final, na ordem em que aparecem.
SECOES = (
    ("sustentada", "O que as fontes confirmam"),
    ("divergencia", "Onde as fontes não concordam"),
    ("lacuna", "O que as fontes não informam"),
    ("precisa_esclarecimento", "Precisamos de um detalhe"),
)


def numerar_fontes(
    itens: Sequence[ItemAnalise], trechos: Sequence[Trecho]
) -> tuple[list[FonteCitada], dict[str, str]]:
    """Numera os documentos citados (F1, F2...) na ordem em que aparecem nas respostas.

    Devolve a lista de fontes e o mapa trecho -> referência (``{"T1": "F1"}``).
    """
    por_id = {t["id"]: t for t in trechos}
    fontes: dict[str, FonteCitada] = {}
    ref_do_trecho: dict[str, str] = {}
    for item in itens:
        for id_trecho in item["trechos"]:
            fonte = por_id[id_trecho]["fonte"]
            if fonte["id"] not in fontes:
                fontes[fonte["id"]] = {
                    "ref": f"F{len(fontes) + 1}",
                    **{campo: fonte[campo] for campo in
                       ("id", "titulo", "instituicao", "url", "atualidade")},
                }
            ref_do_trecho[id_trecho] = fontes[fonte["id"]]["ref"]
    return list(fontes.values()), ref_do_trecho


def _status(estados: list[str]) -> Status:
    if "precisa_esclarecimento" in estados:
        return "precisa_esclarecimento"
    if all(estado == "lacuna" for estado in estados):
        return "sem_resposta"
    if "lacuna" in estados:
        return "parcial"
    return "respondida"


def _proximos_passos(respostas: list[Resposta], fontes: list[FonteCitada]) -> list[str]:
    estados = {r["estado"] for r in respostas}
    por_ref = {f["ref"]: f for f in fontes}
    passos = []
    if "precisa_esclarecimento" in estados:
        passos.append("Responda à pergunta da seção \"Precisamos de um detalhe\" "
                      "e faça a consulta de novo.")
    if "lacuna" in estados:
        # Indica onde confirmar: os órgãos das fontes consultadas para as lacunas.
        refs = [ref for r in respostas if r["estado"] == "lacuna" for ref in r["fontes"]]
        orgaos = {por_ref[ref]["instituicao"]: por_ref[ref]["url"] for ref in refs}
        if orgaos:
            passos += [f"Para o que ficou sem resposta, consulte diretamente {orgao}: {url}"
                       for orgao, url in orgaos.items()]
        else:
            passos.append("Os documentos consultados não tratam do que ficou sem resposta; "
                          "procure o órgão responsável pelo local antes de ir.")
    if "divergencia" in estados:
        passos.append("As fontes não concordam: confirme com o órgão responsável "
                      "qual informação está valendo.")
    if estados & {"sustentada", "divergencia"}:
        passos.append("Antes de ir, abra o link da fonte e confira se a informação "
                      "continua valendo (veja a data de atualização).")
    return passos


def formatar_texto(comunicado: Comunicado) -> str:
    blocos = []
    for estado, titulo in SECOES:
        respostas = [r for r in comunicado["respostas"] if r["estado"] == estado]
        if not respostas:
            continue
        linhas = [titulo]
        for r in respostas:
            refs = " ".join(f"[{ref}]" for ref in r["fontes"])
            linhas.append(f"- {r['duvida']}")
            linhas.append(f"  {r['texto']} {refs}".rstrip())
        blocos.append("\n".join(linhas))
    if comunicado["proximos_passos"]:
        blocos.append("\n".join(["O que fazer agora",
                                 *(f"- {p}" for p in comunicado["proximos_passos"])]))
    if comunicado["fontes"]:
        linhas = ["Fontes"]
        for f in comunicado["fontes"]:
            linhas.append(f"[{f['ref']}] {f['titulo']} · {f['instituicao']} · {f['url']}")
            if f["atualidade"]:
                linhas.append(f"     {f['atualidade']}")
        blocos.append("\n".join(linhas))
    return "\n\n".join(blocos)


class AgenteComunicacao:
    nome = "comunicacao"

    def comunicar(
        self, pergunta: str, itens: list[ItemAnalise], trechos: Sequence[Trecho],
        parecer: Parecer | None,
    ) -> Comunicado:
        if parecer is None or parecer.get("aprovado") is not True:
            raise ComunicacaoRecusada(
                "A Comunicação só publica rascunhos aprovados pela Validação."
            )
        # Mesma barreira da Validação: IDs existentes e passagens literais.
        validar_analise(json.dumps(itens, ensure_ascii=False), trechos)
        fontes, ref_do_trecho = numerar_fontes(itens, trechos)
        respostas: list[Resposta] = []
        for item in itens:
            # dict.fromkeys tira repetições (T1 e T2 da mesma página) mantendo a ordem.
            refs = list(dict.fromkeys(ref_do_trecho[t] for t in item["trechos"]))
            respostas.append({"duvida": item["duvida"], "estado": item["estado"],
                              "texto": item["conclusao"], "fontes": refs})
        comunicado: Comunicado = {
            "agente": "comunicacao",
            "pergunta": pergunta,
            "status": _status([r["estado"] for r in respostas]),
            "respostas": respostas,
            "fontes": fontes,
            "proximos_passos": _proximos_passos(respostas, fontes),
            "texto": "",
        }
        comunicado["texto"] = formatar_texto(comunicado)
        return comunicado
