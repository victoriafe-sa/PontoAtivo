"""Chunking do PontoAtivo.

Parte da proposta de chunking da equipe (800 caracteres, sobreposição de 120,
preferência por fim de frase) com quatro correções, feitas depois de testar a
função original nos 25 documentos reais:

1. IDs globais e únicos (``F028-003``), em vez de 1, 2, 3 por documento.
2. Todo chunk começa em início de palavra (a sobreposição não corta palavras).
3. Pontos de abreviação (``Art.``, ``Inc.``, ``Dr.``) e de numeração
   (``1. Dos alunos``, ``Art. 97.``) não são tratados como fim de frase.
4. Cadastros oficiais (R01 a R04), que são listas de registros, são divididos
   por linha (registro), sem cortar um registro ao meio, e cada chunk repete
   o cabeçalho de colunas.

Cada chunk guarda dois textos:
- ``texto``: o trecho exatamente como está na fonte (usado para citar);
- ``texto_indexado``: o mesmo trecho precedido do título (e da região, nos
  cadastros), usado só para gerar o embedding.

Uso (a partir da raiz do projeto):
    python src/ingestao/chunking.py
    python src/ingestao/chunking.py --saida dados/chunks.jsonl
"""

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

TAMANHO_CHUNK = 800
SOBREPOSICAO = 120
TAMANHO_CHUNK_REGISTROS = 1000  # inclui o cabeçalho de colunas repetido

# Palavras que terminam em ponto sem encerrar a frase.
ABREVIACOES = {
    "art", "arts", "inc", "par", "cap", "sec", "dr", "dra", "sr", "sra",
    "av", "cf", "ex", "exmo", "obs", "tel", "ltda", "min", "gen",
    "n", "p", "pp", "fl",
}

CAMPOS_CABECALHO = {
    "TÍTULO": "titulo",
    "ÓRGÃO": "orgao",
    "LINK": "link",
    "TEMA": "tema",
    "ABRANGÊNCIA": "abrangencia",
    "TIPO DE EVIDÊNCIA": "tipo_evidencia",
    "COMPROVA FUNCIONAMENTO ATUAL?": "comprova_funcionamento",
    "DATA DE PUBLICAÇÃO": "data_publicacao",
    "DATA DE COLETA": "data_coleta",
    "ID": "id_fonte",
    "ESTADO DE VALIDAÇÃO": "validacao",
    "RESSALVAS": "ressalvas",
    "RECORTE": "recorte",
}

PADRAO_FONTE = re.compile(r"^[FNR]\d{2,3}_.*\.txt$")


# ---------------------------------------------------------------- leitura

def ler_fonte(caminho):
    """Lê um .txt de fonte e devolve (metadados, corpo)."""
    linhas = Path(caminho).read_text(encoding="utf-8").splitlines()
    sep = next(i for i, l in enumerate(linhas) if re.fullmatch(r"=+\s*", l))
    metadados = {nome: "" for nome in CAMPOS_CABECALHO.values()}
    ultimo = None
    for linha in linhas[:sep]:
        m = re.match(r"^([A-ZÀ-Ú][A-ZÀ-Ú ?]*?):\s*(.*)$", linha)
        if m and m.group(1) in CAMPOS_CABECALHO:
            ultimo = CAMPOS_CABECALHO[m.group(1)]
            metadados[ultimo] = m.group(2).strip()
        elif ultimo and linha.strip():
            metadados[ultimo] += " " + linha.strip()
    # O estado de validação traz uma explicação longa entre parênteses.
    metadados["validacao"] = metadados["validacao"].split(" (")[0].strip()
    corpo = "\n".join(linhas[sep + 1:]).strip("\n")
    return metadados, corpo


# ------------------------------------------------------- divisão em frases

def _dividir_frases(texto):
    """Divide em frases sem cortar em abreviações nem em numeração."""
    cortes = []
    inicio = 0
    for m in re.finditer(r"[.!?;]\s+", texto):
        if m.group()[0] == ".":
            antes = texto[:m.start()]
            segmento = texto[inicio:m.start()].strip()
            achou = re.search(r"([\wÀ-ÿ]+)$", antes)
            palavra = achou.group(1).lower() if achou else ""
            if palavra in ABREVIACOES or antes.endswith(("Art", "Arts")):
                continue
            if len(palavra) == 1 and palavra.isalpha():
                continue
            if re.search(r"(?i)arts?\.?\s*\d+[\wº°-]*$", antes):
                continue  # "Art. 97." não termina a frase
            if re.fullmatch(r"\d{1,3}(\.\d+)*", segmento):
                continue  # numeração "1." ou "1.1." no início do segmento
        cortes.append(m.end())
        inicio = m.end()
    frases, ini = [], 0
    for c in cortes:
        frases.append(texto[ini:c].strip())
        ini = c
    if texto[ini:].strip():
        frases.append(texto[ini:].strip())
    return [f for f in frases if f]


def _termina_em_abreviacao(texto):
    achou = re.search(r"([\wÀ-ÿ]+)\.?$", texto)
    palavra = achou.group(1).lower() if achou else ""
    if texto.endswith(".") and (palavra in ABREVIACOES
                                or texto[:-1].endswith(("Art", "Arts"))):
        return True
    return bool(re.search(r"(?i)arts?\.?\s*\d+[\wº°-]*$", texto))


def _quebrar_longo(frase, limite):
    """Quebra uma frase maior que o limite, sempre em espaço."""
    partes = []
    while len(frase) > limite:
        corte = frase.rfind(" ", 0, limite)
        # Não separa "Art." / "Art. 12" / abreviações do que vem depois.
        while corte > limite // 2 and _termina_em_abreviacao(frase[:corte]):
            corte = frase.rfind(" ", 0, corte)
        if corte <= 0:
            corte = limite
        partes.append(frase[:corte].strip())
        frase = frase[corte:].strip()
    if frase:
        partes.append(frase)
    return partes


def _cauda_sobreposicao(texto, n):
    """Últimos ~n caracteres do chunk, começando em palavra (ou frase)."""
    if n <= 0 or len(texto) <= n:
        return ""
    cauda = texto[-n:]
    for m in re.finditer(r"(?<=[.!?;]\s)\S", cauda):
        # Ignora "início de frase" logo depois de "Art." e de outras abreviações.
        if not _termina_em_abreviacao(cauda[:m.start()].rstrip()):
            return cauda[m.start():]
    if not texto[-n - 1].isspace():
        espaco = re.search(r"\s", cauda)
        return cauda[espaco.end():] if espaco else ""
    return cauda.lstrip()


def _empacotar(unidades, tamanho, sobreposicao):
    """Junta frases em chunks de até `tamanho` caracteres, com sobreposição."""
    chunks, atual = [], ""
    for texto, novo_paragrafo in unidades:
        sep = "" if not atual else ("\n" if novo_paragrafo else " ")
        if atual and len(atual) + len(sep) + len(texto) > tamanho:
            chunks.append(atual)
            cauda = _cauda_sobreposicao(atual, sobreposicao)
            if cauda and len(cauda) + 1 + len(texto) <= tamanho:
                atual = cauda + ("\n" if novo_paragrafo else " ") + texto
            else:
                atual = texto
        else:
            atual += sep + texto
    if atual:
        chunks.append(atual)
    return chunks


def _chunks_de_texto(corpo, tamanho, sobreposicao):
    unidades = []
    for linha in corpo.splitlines():
        linha = " ".join(linha.split())
        if not linha:
            continue
        primeira = True
        for frase in _dividir_frases(linha):
            for parte in _quebrar_longo(frase, tamanho):
                unidades.append((parte, primeira))
                primeira = False
    return _empacotar(unidades, tamanho, sobreposicao)


# ------------------------------------------------- cadastros (registros)

_PLACEHOLDER = re.compile(r"^(—|cód\. None|<Null>|\d{2}/\d{2}/\d{4})?$")


def _linha_informativa(linha):
    """False se todas as células são vazias, '—', 'cód. None' ou só data."""
    return any(not _PLACEHOLDER.match(c.strip()) for c in linha.split("|"))


def _chunks_de_registros(linhas_corpo, tamanho):
    """Agrupa registros (linhas) sem cortá-los; repete o cabeçalho de colunas.

    Devolve (prosa, chunks, descartados), onde chunks é uma lista de
    (texto, regioes). Se o corpo não tem tabela, devolve (corpo, [], 0).
    """
    idx = next((i for i, l in enumerate(linhas_corpo)
                if l.startswith("Colunas:")), None)
    if idx is None:
        return "\n".join(linhas_corpo), [], 0
    idx_titulo = max(i for i in range(idx) if linhas_corpo[i].strip())
    prosa = "\n".join(linhas_corpo[:idx_titulo])
    cabecalho = linhas_corpo[idx_titulo].strip() + "\n" + linhas_corpo[idx].strip()

    colunas = [c.strip().lower()
               for c in linhas_corpo[idx].split(":", 1)[1].split("|")]
    col_regiao = next((i for i, c in enumerate(colunas)
                       if c.startswith("região")), None)

    registros = [l.strip() for l in linhas_corpo[idx + 1:] if l.strip()]
    uteis = [r for r in registros if _linha_informativa(r)]
    descartados = len(registros) - len(uteis)

    chunks, atual, regioes = [], [], set()

    def fechar():
        if atual:
            chunks.append((cabecalho + "\n" + "\n".join(atual),
                           ", ".join(sorted(regioes))))

    for reg in uteis:
        if atual and len(cabecalho) + 1 + len("\n".join(atual + [reg])) > tamanho:
            fechar()
            atual, regioes = [], set()
        atual.append(reg)
        if col_regiao is not None:
            celulas = [c.strip() for c in reg.split(" | ")]
            if len(celulas) > col_regiao and not celulas[col_regiao].startswith("cód."):
                regioes.add(celulas[col_regiao])
    fechar()
    return prosa, chunks, descartados


# --------------------------------------------------------------- API pública

def _texto_indexado(meta, texto, regioes=""):
    contexto = meta["titulo"]
    local = regioes or meta["abrangencia"]
    if local:
        contexto += " — " + local
    return contexto + "\n" + texto


def dividir_documento(corpo, metadados, tamanho_chunk=TAMANHO_CHUNK,
                      sobreposicao=SOBREPOSICAO,
                      tamanho_registros=TAMANHO_CHUNK_REGISTROS):
    """Divide o corpo de uma fonte em chunks com metadados.

    Devolve (lista_de_chunks, registros_descartados). Cada chunk é um dict com
    id global, texto, texto_indexado e metadados.
    """
    if tamanho_chunk <= 0:
        raise ValueError("O tamanho do chunk deve ser maior que zero.")
    if sobreposicao < 0 or sobreposicao >= tamanho_chunk:
        raise ValueError("A sobreposição deve ser não negativa e menor que o chunk.")

    prosa, registros, descartados = _chunks_de_registros(
        corpo.splitlines(), tamanho_registros)
    brutos = [(t, "texto", "") for t in
              _chunks_de_texto(prosa, tamanho_chunk, sobreposicao)]
    brutos += [(t, "registros", r) for t, r in registros]

    chunks = []
    for n, (texto, tipo, regioes) in enumerate(brutos, start=1):
        meta = dict(metadados)
        meta.update({"indice_chunk": n, "total_chunks": len(brutos),
                     "tipo_chunk": tipo, "regioes": regioes})
        chunks.append({
            "id": f"{metadados['id_fonte']}-{n:03d}",
            "texto": texto,
            "texto_indexado": _texto_indexado(metadados, texto, regioes),
            "metadados": meta,
        })
    return chunks, descartados


def listar_fontes(pasta):
    return sorted(p for p in Path(pasta).glob("*.txt") if PADRAO_FONTE.match(p.name))


def chunkar_pasta(pasta):
    """Chunka todas as fontes da pasta. Devolve (chunks, descartados_por_id)."""
    todos, descartados = [], {}
    for caminho in listar_fontes(pasta):
        metadados, corpo = ler_fonte(caminho)
        chunks, desc = dividir_documento(corpo, metadados)
        todos += chunks
        if desc:
            descartados[metadados["id_fonte"]] = desc
    return todos, descartados


def main():
    raiz = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description="Chunking das fontes do PontoAtivo")
    ap.add_argument("--pasta", default=str(raiz / "dados" / "fontes" / "texto"))
    ap.add_argument("--saida", help="grava os chunks em JSONL")
    args = ap.parse_args()

    chunks, descartados = chunkar_pasta(args.pasta)
    por_fonte = {}
    for c in chunks:
        por_fonte.setdefault(c["metadados"]["id_fonte"], []).append(c)

    print(f"{'fonte':6} {'chunks':>6}  título")
    for id_fonte, lista in por_fonte.items():
        print(f"{id_fonte:6} {len(lista):6}  {lista[0]['metadados']['titulo'][:60]}")
    tam = [len(c["texto"]) for c in chunks]
    print(f"\nFontes: {len(por_fonte)} | chunks: {len(chunks)} | "
          f"tamanho médio: {round(statistics.mean(tam))} | "
          f"mín/máx: {min(tam)}/{max(tam)}")
    print("Registros de cadastro descartados por não terem informação:",
          descartados or "nenhum")
    if args.saida:
        with open(args.saida, "w", encoding="utf-8") as f:
            for c in chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        print("Chunks gravados em", args.saida)


if __name__ == "__main__":
    sys.exit(main())
