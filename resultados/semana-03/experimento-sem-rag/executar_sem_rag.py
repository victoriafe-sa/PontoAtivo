"""Executa as perguntas do experimento SEM RAG e registra resposta, configuração,
tempo e consumo de tokens.

Uso (a partir da raiz do repositório):
    python3 resultados/semana-03/experimento-sem-rag/executar_sem_rag.py qwen llama
    GEMINI_API_KEY=... python3 resultados/semana-03/experimento-sem-rag/executar_sem_rag.py gemini

Requer apenas a biblioteca padrão do Python. Os modelos locais rodam pelo
Ollama (http://localhost:11434). O Gemini só é executado se GEMINI_API_KEY
estiver definida; a chave nunca é gravada nos registros.
"""
import datetime as dt
import json
import os
import platform
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PASTA = Path(__file__).resolve().parent
PERGUNTAS = ["q1", "q2", "q3", "q4"]
OLLAMA = "http://localhost:11434"
SEED = 42  # fixa a amostragem para permitir repetição; demais parâmetros ficam no padrão do modelo

MODELOS = {
    "qwen": {"provedor": "ollama", "modelo": "qwen3:8b", "pasta": "respostas-qwen"},
    "llama": {"provedor": "ollama", "modelo": "llama3.2:3b", "pasta": "respostas-llama"},
    "gemini": {"provedor": "gemini", "modelo": "gemini-3.5-flash-lite", "pasta": "respostas-gemini"},
}


try:  # o Python do python.org no macOS não traz certificados raiz; usa os do certifi se houver
    import certifi
    import ssl
    CONTEXTO_SSL = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CONTEXTO_SSL = None


def carregar_env():
    """Lê GEMINI_API_KEY de um .env na raiz do repositório (ignorado pelo Git)."""
    env = PASTA.parents[2] / ".env"
    if env.exists() and not os.environ.get("GEMINI_API_KEY"):
        for linha in env.read_text(encoding="utf-8").splitlines():
            chave, _, valor = linha.partition("=")
            if chave.strip() == "GEMINI_API_KEY":
                os.environ["GEMINI_API_KEY"] = valor.strip().strip('"\'')


def post(url, corpo, headers=None):
    req = urllib.request.Request(url, data=json.dumps(corpo).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **(headers or {})})
    for tentativa in range(1, 6):
        try:
            with urllib.request.urlopen(req, timeout=900, context=CONTEXTO_SSL) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as erro:  # mostra a mensagem da API (ex.: chave inválida)
            if erro.code in (429, 503) and tentativa < 5:  # sobrecarga temporária: espera e repete
                print(f"  HTTP {erro.code}, nova tentativa em {10 * tentativa} s...")
                time.sleep(10 * tentativa)
                continue
            sys.exit(f"Erro HTTP {erro.code}: {erro.read().decode(errors='replace')[:500]}")


def info_ollama(modelo):
    """Versão do Ollama, digest e parâmetros padrão do modelo (para o registro)."""
    with urllib.request.urlopen(f"{OLLAMA}/api/version") as r:
        versao = json.loads(r.read())["version"]
    show = post(f"{OLLAMA}/api/show", {"model": modelo})
    with urllib.request.urlopen(f"{OLLAMA}/api/tags") as r:
        tags = {m["name"]: m for m in json.loads(r.read())["models"]}
    det = show.get("details", {})
    return {
        "ollama_versao": versao,
        "digest": tags.get(modelo, {}).get("digest"),
        "familia": det.get("family"),
        "parametros_modelo": det.get("parameter_size"),
        "quantizacao": det.get("quantization_level"),
        "parametros_padrao_modelfile": show.get("parameters", "").strip(),
    }


def rodar_ollama(modelo, prompt):
    # Pré-carrega o modelo (prompt vazio não gera texto) para que o tempo medido
    # seja o da resposta, não o do carregamento do disco.
    post(f"{OLLAMA}/api/generate", {"model": modelo, "prompt": "", "keep_alive": "10m"})
    opcoes = {"seed": SEED}
    t0 = time.perf_counter()
    r = post(f"{OLLAMA}/api/generate", {"model": modelo, "prompt": prompt, "stream": False,
                                         "options": opcoes, "keep_alive": "10m"})
    parede = time.perf_counter() - t0
    ns = 1e9
    gen_s = r.get("eval_duration", 0) / ns
    return {
        "resposta": r.get("response", "").strip(),
        "raciocinio": (r.get("thinking") or "").strip(),
        "configuracao": {"options": opcoes, "stream": False, "think": "padrão do Ollama (não definido)",
                         "endpoint": "/api/generate"},
        "tokens_entrada": r.get("prompt_eval_count"),
        "tokens_saida": r.get("eval_count"),
        "tempo_total_s": round(r.get("total_duration", 0) / ns, 3),
        "tempo_carga_s": round(r.get("load_duration", 0) / ns, 3),
        "tempo_entrada_s": round(r.get("prompt_eval_duration", 0) / ns, 3),
        "tempo_geracao_s": round(gen_s, 3),
        "tokens_por_s": round(r["eval_count"] / gen_s, 2) if gen_s else None,
        "tempo_parede_s": round(parede, 3),
        "motivo_fim": r.get("done_reason"),
    }


def rodar_gemini(modelo, prompt):
    chave = os.environ["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
    t0 = time.perf_counter()
    r = post(url, {"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
             headers={"x-goog-api-key": chave})
    parede = time.perf_counter() - t0
    cand = r["candidates"][0]
    partes = cand.get("content", {}).get("parts", [])
    uso = r.get("usageMetadata", {})
    return {
        "resposta": "".join(p.get("text", "") for p in partes if not p.get("thought")).strip(),
        "raciocinio": "",
        "configuracao": {"generationConfig": "padrão da API", "ferramentas": "nenhuma (sem busca)",
                         "versao_modelo_api": r.get("modelVersion")},
        "tokens_entrada": uso.get("promptTokenCount"),
        "tokens_saida": uso.get("candidatesTokenCount"),
        "tokens_raciocinio": uso.get("thoughtsTokenCount"),
        "tokens_total": uso.get("totalTokenCount"),
        "tempo_parede_s": round(parede, 3),
        "motivo_fim": cand.get("finishReason"),
    }


def main():
    carregar_env()
    escolhidos = sys.argv[1:] or ["qwen", "llama"]
    agora = dt.datetime.now().astimezone()
    amanha = (agora + dt.timedelta(days=1)).date().isoformat()
    for nome in escolhidos:
        cfg = MODELOS[nome]
        if cfg["provedor"] == "gemini" and not os.environ.get("GEMINI_API_KEY"):
            print("gemini: GEMINI_API_KEY não definida — pulando.")
            continue
        extra = info_ollama(cfg["modelo"]) if cfg["provedor"] == "ollama" else {}
        # SO_PERGUNTAS=q4 roda só as perguntas indicadas, sem sobrescrever as demais
        for q in os.environ.get("SO_PERGUNTAS", ",".join(PERGUNTAS)).split(","):
            prompt = (PASTA / "prompts" / f"{q}.txt").read_text(encoding="utf-8")
            inicio = dt.datetime.now().astimezone().isoformat(timespec="seconds")
            res = (rodar_ollama if cfg["provedor"] == "ollama" else rodar_gemini)(cfg["modelo"], prompt)
            registro = {"pergunta_id": q, "modelo": cfg["modelo"], "provedor": cfg["provedor"],
                        "executado_em": inicio, "maquina": f"{platform.system()} {platform.machine()}",
                        **({"amanha_refere_se_a": amanha} if q == "q4" else {}), **extra, **res}
            (PASTA / "brutos" / f"{nome}-{q}.json").write_text(
                json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
            cab = [f"modelo: {cfg['modelo']}", f"executado_em: {inicio}",
                   f"tokens: entrada={res.get('tokens_entrada')} saida={res.get('tokens_saida')}"
                   + (f" raciocinio={res['tokens_raciocinio']}" if res.get("tokens_raciocinio") else ""),
                   f"tempo_s: {res.get('tempo_total_s', res['tempo_parede_s'])}"]
            if q == "q4":
                cab.append(f"amanha_refere_se_a: {amanha}")
            (PASTA / cfg["pasta"] / f"{q}.txt").write_text(
                "\n".join(cab) + "\n---\n" + res["resposta"] + "\n", encoding="utf-8")
            print(f"{nome} {q}: {res.get('tokens_entrada')}→{res.get('tokens_saida')} tokens, "
                  f"{res.get('tempo_total_s', res['tempo_parede_s'])} s")


if __name__ == "__main__":
    main()
