"""Agenda compartilhada com vagas confirmadas atomicamente."""
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import json
import re
import unicodedata

from .contas import AGES
from .persistencia import ApiError

LEVELS = ("iniciante", "intermediario", "avancado", "todos")
FORMATS = ("dupla", "trio", "grupo")
# Quem pode participar. "mulheres" e "homens" conferem o gênero informado na conta.
AUDIENCES = ("misto", "mulheres", "homens")
AUDIENCE_GENDER = {"mulheres": "mulher", "homens": "homem"}
AUDIENCE_LABEL = {"mulheres": "só para mulheres", "homens": "só para homens"}
BRASILIA = timezone(timedelta(hours=-3))


def _chave_regiao(nome):
    """Nome de RA comparável: sem acento, minúsculo, com apelidos unificados."""
    texto = unicodedata.normalize("NFD", str(nome or "")).casefold()
    texto = " ".join("".join(c for c in texto if not unicodedata.combining(c)).split())
    return {"sol nascente": "sol nascente/por do sol", "estrutural": "scia/estrutural"}.get(texto, texto)


def now():
    return datetime.now(timezone.utc).isoformat()


def _matches(key, wanted, value):
    if not wanted:
        return True
    # Quem filtra pela própria faixa também pode entrar em encontros abertos a todos os adultos.
    if key == "idade" and wanted != "todos" and value == "todos":
        return True
    return wanted == value


class Meetings:
    def __init__(self, db, places, seguranca=None):
        self.db = db
        self.places = {place["id"]: place for place in places}
        if len(self.places) != len(places):
            raise ValueError("Identificadores de locais duplicados.")
        # Tabela da SSP-DF por RA (scripts/gerar_seguranca_ras.py). Só as RAs com alerta interessam.
        seguranca = seguranca or {}
        self.seguranca_ano = seguranca.get("ano")
        self.seguranca = {
            _chave_regiao(nome): {"vezes_media_df": dados["vezes_media_df"], "ano": seguranca.get("ano"), "regiao": nome}
            for nome, dados in seguranca.get("regioes", {}).items() if dados.get("alerta")
        }

    def _user(self, db, user_id):
        row = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if row is None:
            raise ApiError(401, "Entre na sua conta para continuar.")
        return row

    def _event(self, db, event_id):
        row = db.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
        if row is None:
            raise ApiError(404, "Encontro não encontrado.")
        return row

    def _available(self, row):
        if row["cancelled"] or row["start"] <= now():
            raise ApiError(409, "Esse encontro já foi cancelado ou já começou.")

    def _alerta_grupo(self, db, row, user_id):
        """Alerta só para mulheres: grupo de 5+ pessoas, mais homens que mulheres
        e ninguém com quem ela já praticou. Só o alerta sai daqui, nunca os gêneros."""
        if not user_id or row["capacity"] < 5:
            return False
        viewer = db.execute("SELECT gender FROM users WHERE id=?", (user_id,)).fetchone()
        if viewer is None or viewer["gender"] != "mulher":
            return False
        outros = db.execute(
            """SELECT users.id, users.gender FROM members JOIN users ON users.id = members.user_id
               WHERE members.event_id = ? AND members.user_id <> ?""",
            (row["id"], user_id),
        ).fetchall()
        homens = sum(o["gender"] == "homem" for o in outros)
        mulheres = sum(o["gender"] == "mulher" for o in outros) + 1  # conta ela também
        if homens <= mulheres:
            return False
        # "Não se conhecem": ela nunca participou de um encontro realizado com ninguém do grupo.
        conhecidos = db.execute(
            """SELECT 1 FROM members AS dela
               JOIN members AS outro ON outro.event_id = dela.event_id
               JOIN events ON events.id = dela.event_id
               WHERE dela.user_id = ? AND events.cancelled = 0 AND events.start <= ?
                 AND outro.user_id IN (SELECT user_id FROM members WHERE event_id = ? AND user_id <> ?)
               LIMIT 1""",
            (user_id, now(), row["id"], user_id),
        ).fetchone()
        return conhecidos is None

    def _view(self, db, row, user_id=None):
        place = self.places.get(row["place_id"], {"id": row["place_id"], "nome": "Local fora do cadastro", "regiao": ""})
        count = db.execute("SELECT count(*) FROM members WHERE event_id=?", (row["id"],)).fetchone()[0]
        joined = db.execute("SELECT 1 FROM members WHERE event_id=? AND user_id=?", (row["id"], user_id)).fetchone() is not None
        nickname = db.execute("SELECT nickname FROM users WHERE id=?", (row["organizer"],)).fetchone()[0]
        state = "cancelado" if row["cancelled"] else "passado" if row["start"] <= now() else "lotado" if count >= row["capacity"] else "aberto"
        return {
            "id": row["id"], "local": place, "esporte": row["sport"], "inicio": row["start"],
            "nivel": row["level"], "idade": row["age"], "formato": row["format"],
            "publico": row["audience"] if "audience" in row.keys() else "misto",
            "alerta_grupo": self._alerta_grupo(db, row, user_id),
            "alerta_regiao": self.seguranca.get(_chave_regiao(place.get("regiao"))),
            "capacidade": row["capacity"], "participantes": count,
            "vagas": row["capacity"] - count, "estado": state, "organizador": nickname,
            "meu": row["organizer"] == user_id, "participando": joined,
        }

    def criar_encontro(self, usuario_id, dados):
        request_id = dados.get("request_id")
        if request_id is not None and (not isinstance(request_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{8,80}", request_id)):
            raise ApiError(400, "A identificação da publicação é inválida.")
        payload = json.dumps({key: value for key, value in dados.items() if key != "request_id"}, sort_keys=True)
        place = dados.get("local_id")
        sport = dados.get("esporte", "")
        level, age, form = dados.get("nivel"), dados.get("idade"), dados.get("formato")
        audience = dados.get("publico", "misto")
        if audience not in AUDIENCES:
            raise ApiError(400, "Escolha se o encontro é misto, só para mulheres ou só para homens.")
        if not isinstance(place, str) or place not in self.places:
            raise ApiError(400, "Selecione um local do mapa.")
        if not isinstance(sport, str) or not 2 <= len(sport.strip()) <= 60:
            raise ApiError(400, "Informe um esporte de 2 a 60 caracteres.")
        if not all(isinstance(value, str) for value in (level, age, form)) or level not in LEVELS or age not in (*AGES, "todos") or form not in FORMATS:
            raise ApiError(400, "Confira o nível, a faixa etária e o formato.")
        capacity = {"dupla": 2, "trio": 3}.get(form, dados.get("capacidade"))
        if type(capacity) is not int or (form == "grupo" and not 4 <= capacity <= 20):
            raise ApiError(400, "Grupos devem ter de 4 a 20 pessoas.")
        try:
            start = datetime.fromisoformat(dados["inicio"])
            if start.tzinfo is None:
                raise ValueError
            start = start.astimezone(timezone.utc).isoformat()
        except (KeyError, TypeError, ValueError):
            raise ApiError(400, "Escolha uma data e hora futuras, no horário de Brasília.") from None
        event_id = uuid4().hex
        with self.db.transaction() as db:
            user = self._user(db, usuario_id)
            if request_id:
                existing = db.execute("SELECT * FROM event_requests WHERE user_id=? AND request_id=?",
                                      (usuario_id, request_id)).fetchone()
                if existing:
                    if existing["payload"] != payload:
                        raise ApiError(409, "Essa publicação já foi usada com outros dados.")
                    return self._view(db, self._event(db, existing["event_id"]), usuario_id)
            if start <= now():
                raise ApiError(400, "Escolha uma data e hora futuras, no horário de Brasília.")
            if age != "todos" and age != user["age"]:
                raise ApiError(400, "Escolha uma faixa etária que inclua você.")
            if audience in AUDIENCE_GENDER and user["gender"] != AUDIENCE_GENDER[audience]:
                raise ApiError(400, f"Para marcar um encontro {AUDIENCE_LABEL[audience]}, informe o gênero "
                                    f"\"{AUDIENCE_GENDER[audience]}\" em Minhas preferências.")
            db.execute("""INSERT INTO events(id, organizer, place_id, sport, start, level, age, format,
                                             capacity, cancelled, audience) VALUES(?,?,?,?,?,?,?,?,?,0,?)""",
                       (event_id, usuario_id, place, sport.strip(), start, level, age, form, capacity, audience))
            db.execute("INSERT INTO members VALUES(?,?)", (event_id, usuario_id))
            if request_id:
                db.execute("INSERT INTO event_requests VALUES(?,?,?,?)", (usuario_id, request_id, event_id, payload))
            return self._view(db, self._event(db, event_id), usuario_id)

    def listar_encontros(self, filtros, usuario_id=None):
        with self.db.transaction() as db:
            if filtros.get("meus"):
                self._user(db, usuario_id)
                rows = db.execute("""SELECT events.* FROM events JOIN members ON events.id=members.event_id
                                     WHERE members.user_id=? ORDER BY start""", (usuario_id,)).fetchall()
            else:
                rows = db.execute("SELECT * FROM events WHERE cancelled=0 AND start>? ORDER BY start", (now(),)).fetchall()
                if usuario_id:
                    # Encontros só para mulheres ou só para homens somem para quem não pode entrar.
                    # Sem conta, todos aparecem: o gênero só é conferido na hora de entrar.
                    gender = self._user(db, usuario_id)["gender"]
                    rows = [row for row in rows
                            if row["audience"] not in AUDIENCE_GENDER or AUDIENCE_GENDER[row["audience"]] == gender]
            result = []
            for row in rows:
                place = self.places.get(row["place_id"], {})
                values = {"regiao": place.get("regiao"), "esporte": row["sport"],
                          "nivel": row["level"], "formato": row["format"], "publico": row["audience"],
                          "idade": row["age"],
                          "data": datetime.fromisoformat(row["start"]).astimezone(BRASILIA).date().isoformat()}
                if all(_matches(key, filtros.get(key), value) for key, value in values.items()):
                    result.append(self._view(db, row, usuario_id))
            return result

    def entrar(self, encontro_id, usuario_id):
        with self.db.transaction() as db:
            user = self._user(db, usuario_id)
            row = self._event(db, encontro_id)
            self._available(row)
            if row["age"] != "todos" and row["age"] != user["age"]:
                raise ApiError(403, "Sua faixa etária não corresponde à deste encontro.")
            if row["audience"] in AUDIENCE_GENDER and user["gender"] != AUDIENCE_GENDER[row["audience"]]:
                raise ApiError(403, f"Este encontro é {AUDIENCE_LABEL[row['audience']]}. Se for o seu caso, "
                                    "informe o gênero em Minhas preferências.")
            current = self._view(db, row, usuario_id)
            if not current["participando"]:
                if current["vagas"] <= 0:
                    raise ApiError(409, "Esse encontro está lotado.")
                db.execute("INSERT INTO members VALUES(?,?)", (encontro_id, usuario_id))
            return self._view(db, row, usuario_id)

    def sair(self, encontro_id, usuario_id):
        with self.db.transaction() as db:
            self._user(db, usuario_id)
            row = self._event(db, encontro_id)
            self._available(row)
            if row["organizer"] == usuario_id:
                raise ApiError(409, "Quem organizou deve cancelar o encontro para sair.")
            db.execute("DELETE FROM members WHERE event_id=? AND user_id=?", (encontro_id, usuario_id))
            return self._view(db, row, usuario_id)

    def cancelar(self, encontro_id, usuario_id):
        with self.db.transaction() as db:
            self._user(db, usuario_id)
            row = self._event(db, encontro_id)
            if row["organizer"] != usuario_id:
                raise ApiError(403, "Somente quem organizou pode cancelar o encontro.")
            db.execute("UPDATE events SET cancelled=1 WHERE id=?", (encontro_id,))
            return self._view(db, self._event(db, encontro_id), usuario_id)
