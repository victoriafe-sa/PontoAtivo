"""Cria a persona de demonstração Jeferson e a corrida dele no servidor local.

Jeferson é um atleta amador de corrida que estuda na UnB Gama. Ele marca uma
corrida em grupo às 18h no PEC do Setor Leste EQ 4/6 (Gama), a pista pública
mais perto do campus (cerca de 2 km), e procura parceiros para correr.

Uso, com o servidor aberto (`python -m pontoativo_rag.web`):

    python -m pontoativo_rag.persona_demo --porta 8766

O script passa pela mesma API do site, então valida tudo como um usuário real.
A senha é gerada na primeira execução e fica só em `dados/persona_jeferson.txt`,
que o Git ignora. Rodar de novo reaproveita a conta e não duplica a corrida do dia.
"""
import argparse
import json
import secrets
import string
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from http.cookiejar import CookieJar
from pathlib import Path

BRASILIA = timezone(timedelta(hours=-3))
LOGIN = "jeferson.corrida"
PERFIL = {"login": LOGIN, "apelido": "Jeferson", "idade": "25-34", "esportes": ["Corrida"], "regiao": "Gama"}
# PEC – Ponto de Encontro Comunitário – SETOR LESTE EQ 4/6 (data/locais.js).
LOCAL_ID = "ide-603"
HORA = 18
CAPACIDADE = 6
ARQUIVO_SENHA = Path("dados/persona_jeferson.txt")


def proximo_horario(agora):
    """Hoje às 18h em Brasília; se já passou, amanhã às 18h."""
    agora = agora.astimezone(BRASILIA)
    inicio = agora.replace(hour=HORA, minute=0, second=0, microsecond=0)
    return inicio if inicio > agora else inicio + timedelta(days=1)


def dados_da_corrida(inicio):
    return {
        "local_id": LOCAL_ID, "esporte": "Corrida", "inicio": inicio.isoformat(),
        "nivel": "todos", "idade": "todos", "formato": "grupo", "capacidade": CAPACIDADE,
        # Mesmo id no mesmo dia: rodar de novo não cria outra corrida.
        "request_id": f"persona-jeferson-{inicio:%Y%m%d}",
    }


def ler_senha(arquivo):
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        if linha.startswith("Senha: "):
            return linha.removeprefix("Senha: ").strip()
    raise SystemExit(f"{arquivo} não tem a linha 'Senha: ...'.")


class Cliente:
    def __init__(self, base):
        self.base = base
        self.http = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def post(self, caminho, corpo):
        pedido = urllib.request.Request(
            self.base + caminho, data=json.dumps(corpo).encode(), method="POST",
            headers={"Content-Type": "application/json", "Origin": self.base},
        )
        try:
            with self.http.open(pedido, timeout=30) as resposta:
                return resposta.status, json.load(resposta)
        except urllib.error.HTTPError as erro:
            return erro.code, json.load(erro)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--porta", type=int, default=8766)
    args = parser.parse_args(argv)
    cliente = Cliente(f"http://127.0.0.1:{args.porta}")

    try:
        if ARQUIVO_SENHA.exists():
            status, resposta = cliente.post("/api/sessao", {"login": LOGIN, "senha": ler_senha(ARQUIVO_SENHA)})
        else:
            senha = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
            status, resposta = cliente.post("/api/conta", {**PERFIL, "senha": senha})
            if status == 201:
                ARQUIVO_SENHA.parent.mkdir(parents=True, exist_ok=True)
                ARQUIVO_SENHA.write_text(
                    "Conta de teste do PontoAtivo (somente neste computador)\n"
                    f"Usuário: {LOGIN}\nSenha: {senha}\n", encoding="utf-8")
    except urllib.error.URLError:
        raise SystemExit(f"O servidor não respondeu em {cliente.base}. Rode antes: python -m pontoativo_rag.web")
    if status not in (200, 201):
        dica = " Apague a conta no banco local ou recupere o arquivo da senha." if status == 409 else ""
        raise SystemExit(f"Não deu para entrar como {LOGIN}: {resposta.get('erro', resposta)}{dica}")
    print(f"Conta pronta: {LOGIN} (senha em {ARQUIVO_SENHA})")

    status, encontro = cliente.post("/api/encontros", dados_da_corrida(proximo_horario(datetime.now(BRASILIA))))
    if status not in (200, 201):
        raise SystemExit(f"Não deu para marcar a corrida: {encontro.get('erro', encontro)}")
    inicio = datetime.fromisoformat(encontro["inicio"]).astimezone(BRASILIA)
    print(f"Corrida marcada: {encontro['local']['nome']} ({encontro['local']['regiao']}), "
          f"{inicio:%d/%m/%Y às %Hh}, {encontro['vagas']} vagas de {encontro['capacidade']}.")
    print(f"Abra {cliente.base}/#encontros e entre como {LOGIN} para ver a corrida.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
