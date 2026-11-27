"""Gera a tabela de segurança por Região Administrativa usada nos alertas dos encontros.

Fontes oficiais:
- SSP-DF, "Balanço criminal" de 2025 por RA (planilhas XLSX, dados pela data do
  fato, atualizados em 05/01/2026): https://www.ssp.df.gov.br/dados-por-regiao-administrativa/
- Codeplan/IPEDF, "Projeções populacionais para as Regiões Administrativas do
  Distrito Federal 2020-2030" (2022), Tabela A.1, população de 2025.

Indicador: crimes violentos contra a pessoa na rua = homicídios e outros crimes
violentos letais (C.V.L.I.) + roubo a transeunte + estupro, por 100 mil moradores.
Uma RA recebe alerta quando a taxa fica 50% ou mais acima da taxa do DF.

Uso (baixa as planilhas da SSP-DF, só biblioteca padrão):
    python scripts/gerar_seguranca_ras.py
"""
from __future__ import annotations

import io
import json
import re
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "dados" / "mapa" / "seguranca"
SAIDA = PASTA / "seguranca_ras_2025.json"
LIMIAR = 1.5  # taxa da RA / taxa do DF

# Codeplan/IPEDF, Tabela A.1, população projetada para 2025.
POPULACAO_2025 = {
    "Águas Claras": 130342, "Arniqueira": 47932, "Brazlândia": 66729, "Candangolândia": 16094,
    "Ceilândia": 356548, "Cruzeiro": 30441, "Fercal": 9508, "Gama": 146705, "Guará": 146001,
    "Itapoã": 97667, "Jardim Botânico": 63186, "Lago Norte": 39095, "Lago Sul": 30652,
    "Núcleo Bandeirante": 24654, "Paranoá": 76666, "Park Way": 24294, "Planaltina": 218569,
    "Plano Piloto": 248568, "Recanto das Emas": 148474, "Riacho Fundo": 46398,
    "Riacho Fundo II": 76384, "Samambaia": 264403, "Santa Maria": 132256, "São Sebastião": 128066,
    "SCIA/Estrutural": 39890, "SIA": 2692, "Sobradinho": 75710, "Sobradinho II": 84744,
    "Sol Nascente/Pôr do Sol": 99984, "Sudoeste/Octogonal": 58141, "Taguatinga": 217565,
    "Varjão": 9283, "Vicente Pires": 82034,
}
# Nome da RA na página da SSP-DF -> nome usado no mapa.
NOMES_SSP = {
    "BRASILIA (PLANO PILOTO)": "Plano Piloto", "ESTRUTURAL / SETOR COMPLEMENTAR DE INDUSTRIA E ABASTECIMENTO (SCIA)": "SCIA/Estrutural",
    "SOBRADINHO I": "Sobradinho", "RIACHO FUNDO I": "Riacho Fundo", "SOL NASCENTE": "Sol Nascente/Pôr do Sol",
    "SUDOESTE/OCTOGONAL": "Sudoeste/Octogonal",
}
INDICADORES = {"1.TOTAL C.V.L.I.": "cvli", "ROUBO A TRANSEUNTE": "roubo_transeunte", "ESTUPRO": "estupro"}


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", str(texto).upper())
    return " ".join("".join(c for c in texto if not unicodedata.combining(c)).split())


def nome_do_mapa(nome_ssp: str) -> str | None:
    chave = normalizar(nome_ssp.split("🗓️")[0])
    if chave in NOMES_SSP:
        return NOMES_SSP[chave]
    for nome in POPULACAO_2025:
        if normalizar(nome) == chave:
            return nome
    return None


def ler_xlsx(conteudo: bytes) -> list[list]:
    """Primeira planilha de um .xlsx como lista de linhas (sem dependências)."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    z = zipfile.ZipFile(io.BytesIO(conteudo))
    textos = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns):
            textos.append("".join(t.text or "" for t in si.iter(f"{{{ns['m']}}}t")))
    planilha = sorted(n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n))[0]
    linhas = []
    for row in ET.fromstring(z.read(planilha)).iter(f"{{{ns['m']}}}row"):
        valores = []
        for c in row.findall("m:c", ns):
            v = c.find("m:v", ns)
            if v is not None:
                valores.append(textos[int(v.text)] if c.get("t") == "s" else v.text)
        linhas.append([x for x in valores if x not in (None, "")])
    return linhas


def indicadores(linhas: list[list]) -> dict:
    achados = {}
    for linha in linhas:
        for i, celula in enumerate(linha):
            chave = INDICADORES.get(normalizar(celula))
            if chave and i + 1 < len(linha):
                achados[chave] = int(float(linha[i + 1]))
    return achados


def main() -> None:
    fontes = [l.split("\t") for l in (PASTA / "fontes_ssp_2025.tsv").read_text(encoding="utf-8").splitlines() if l.strip()]
    regioes = {}
    for nome_ssp, url in fontes:
        nome = nome_do_mapa(nome_ssp)
        if nome is None:
            raise SystemExit(f"RA sem correspondência no mapa: {nome_ssp!r}")
        pedido = urllib.request.Request(url.strip(), headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(pedido, timeout=60) as resposta:
            dados = indicadores(ler_xlsx(resposta.read()))
        if set(dados) != set(INDICADORES.values()):
            raise SystemExit(f"Indicadores faltando em {nome}: {dados}")
        regioes[nome] = {"fonte_ssp": url.strip(), **dados}

    total_crimes = sum(sum(r[k] for k in INDICADORES.values()) for r in regioes.values())
    total_pop = sum(POPULACAO_2025[n] for n in regioes)
    taxa_df = round(100000 * total_crimes / total_pop, 1)
    for nome, r in regioes.items():
        crimes = sum(r[k] for k in INDICADORES.values())
        r["populacao_2025"] = POPULACAO_2025[nome]
        r["crimes"] = crimes
        r["taxa_100mil"] = round(100000 * crimes / POPULACAO_2025[nome], 1)
        r["vezes_media_df"] = round(r["taxa_100mil"] / taxa_df, 2)
        r["alerta"] = r["taxa_100mil"] >= LIMIAR * taxa_df

    resultado = {
        "ano": 2025,
        "indicador": "C.V.L.I. + roubo a transeunte + estupro, por 100 mil moradores",
        "taxa_df_100mil": taxa_df,
        "limiar": f"alerta quando a taxa da RA é {LIMIAR}x a do DF ou mais",
        "fontes": {
            "crimes": "SSP-DF, Balanço criminal 2025 por RA (dados pela data do fato, atualizados em 05/01/2026) - https://www.ssp.df.gov.br/dados-por-regiao-administrativa/",
            "populacao": "Codeplan/IPEDF, Projeções populacionais para as RAs do DF 2020-2030 (2022), Tabela A.1, 2025",
        },
        "observacao": "Taxa por morador. Regiões com muita gente de fora (Plano Piloto, SIA) ficam com taxa mais alta. "
                      "O alerta resume o ano inteiro da RA: não diz nada sobre uma quadra ou um horário.",
        "regioes": dict(sorted(regioes.items())),
    }
    SAIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(regioes)} RAs · taxa do DF {taxa_df}/100 mil · com alerta: "
          + ", ".join(n for n, r in regioes.items() if r["alerta"]))


if __name__ == "__main__":
    main()
