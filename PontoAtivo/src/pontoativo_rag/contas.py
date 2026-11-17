"""Contas adultas autodeclaradas e sessões do piloto."""
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
from uuid import uuid4

from .moderacao import termo_improprio
from .persistencia import ApiError

AGES = ("18-24", "25-34", "35-44", "45-59", "60+")
SESSION_SECONDS = 7 * 24 * 60 * 60
# Mesma lista de esportes dos encontros (encontros.js). Preferências são
# opcionais e só pré-selecionam filtros; nunca escondem resultados.
SPORTS = (
    "Futebol", "Futsal", "Vôlei", "Vôlei de areia", "Basquete", "Tênis",
    "Beach tennis", "Futevôlei", "Caminhada", "Corrida", "Skate",
    "Exercícios no PEC", "Alongamento", "Natação", "Bocha paralímpica",
    "Goalball", "Atletismo", "Tênis em cadeira de rodas", "Basquete em cadeira de rodas",
)
MAX_SPORTS = 5
# Conta do dono do piloto. Só entra pelo botão "Entrar como admin", que o
# servidor libera apenas para quem abre o site no próprio computador.
ADMIN_LOGIN = "admin"
ADMIN_NICKNAME = "Admin"
ADMIN_AGE = "25-34"


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
    return salt + ":" + digest.hex()


def public_user(row, preferences=None):
    return {
        "id": row["id"], "apelido": row["nickname"], "idade": row["age"],
        "preferencias": preferences or {"esportes": [], "regiao": ""},
    }


def _read_preferences(db, user_id):
    row = db.execute("SELECT sports, region FROM preferences WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        return {"esportes": [], "regiao": ""}
    return {"esportes": json.loads(row["sports"]), "regiao": row["region"]}


def _open_session(db, user_id, now):
    token = secrets.token_urlsafe(32)
    db.execute("DELETE FROM sessions WHERE expires < ?", (now,))
    db.execute("INSERT INTO sessions VALUES(?,?,?)",
               (hashlib.sha256(token.encode()).hexdigest(), user_id, now + SESSION_SECONDS))
    return token


class Accounts:
    def __init__(self, db, regions=()):
        self.db = db
        # Regiões válidas para a preferência (as mesmas do mapa); vazio aceita qualquer nome curto.
        self.regions = frozenset(regions)
        self.dummy_password = password_hash("invalid-password-placeholder")

    def clean_preferences(self, data):
        sports = data.get("esportes", [])
        region = data.get("regiao", "")
        if isinstance(sports, str):
            sports = [sports] if sports else []
        if not isinstance(sports, list) or not all(isinstance(s, str) for s in sports):
            raise ApiError(400, "Escolha os esportes da lista.")
        sports = list(dict.fromkeys(sports))  # sem repetição, na ordem escolhida
        if len(sports) > MAX_SPORTS or any(s not in SPORTS for s in sports):
            raise ApiError(400, f"Escolha até {MAX_SPORTS} esportes da lista.")
        if not isinstance(region, str):
            raise ApiError(400, "Escolha uma região da lista.")
        region = region.strip()
        if region and (len(region) > 60 or (self.regions and region not in self.regions)):
            raise ApiError(400, "Escolha uma região da lista.")
        return {"esportes": sports, "regiao": region}

    def _save_preferences(self, db, user_id, preferences):
        db.execute(
            """INSERT INTO preferences VALUES(?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET sports=excluded.sports, region=excluded.region""",
            (user_id, json.dumps(preferences["esportes"], ensure_ascii=False), preferences["regiao"]),
        )

    def update_preferences(self, user_id, data):
        preferences = self.clean_preferences(data)
        with self.db.transaction() as db:
            self._save_preferences(db, user_id, preferences)
        return preferences

    def register(self, data):
        login = str(data.get("login", "")).strip().casefold()
        password = data.get("senha")
        nickname = str(data.get("apelido", "")).strip()
        age = data.get("idade")
        if not re.fullmatch(r"[a-z0-9_.-]{3,50}", login):
            raise ApiError(400, "O usuário deve ter de 3 a 50 letras, números, pontos ou traços.")
        if login == ADMIN_LOGIN:
            raise ApiError(409, "Esse usuário já está cadastrado.")
        if not isinstance(password, str) or not 10 <= len(password) <= 128:
            raise ApiError(400, "Escolha uma senha de 10 a 128 caracteres.")
        if not 2 <= len(nickname) <= 50 or age not in AGES:
            raise ApiError(400, "Informe um apelido e uma faixa etária a partir de 18 anos.")
        # O apelido aparece para todos nos cartões dos encontros.
        termo = termo_improprio(nickname)
        if termo:
            raise ApiError(400, f'O apelido tem um termo impróprio ("{termo}"). Escolha outro.')
        termo = termo_improprio(login)
        if termo:
            raise ApiError(400, f'O usuário tem um termo impróprio ("{termo}"). Escolha outro.')
        preferences = self.clean_preferences(data)
        user_id = uuid4().hex
        hashed = password_hash(password)
        try:
            with self.db.transaction() as db:
                db.execute("INSERT INTO users VALUES(?,?,?,?,?)", (user_id, login, nickname, age, hashed))
                if preferences["esportes"] or preferences["regiao"]:
                    self._save_preferences(db, user_id, preferences)
        except sqlite3.IntegrityError:
            raise ApiError(409, "Esse usuário já está cadastrado.") from None
        return {"id": user_id, "apelido": nickname, "idade": age, "preferencias": preferences}

    def login(self, login, password, address):
        if not isinstance(login, str) or not isinstance(password, str) or len(password) > 128:
            raise ApiError(401, "Usuário ou senha incorretos.")
        login = login.strip().casefold()
        key = hashlib.sha256((address + "|" + login).encode()).hexdigest()
        now = time.time()
        with self.db.transaction() as db:
            db.execute("DELETE FROM login_attempts WHERE expires < ?", (now,))
            attempt = db.execute("SELECT count FROM login_attempts WHERE key=?", (key,)).fetchone()
            if attempt and attempt["count"] >= 5:
                raise ApiError(429, "Muitas tentativas. Aguarde 15 minutos para tentar novamente.")
            row = db.execute("SELECT * FROM users WHERE login=?", (login,)).fetchone()
            stored = row["password"] if row else self.dummy_password
            valid = hmac.compare_digest(password_hash(password, stored.split(":")[0]), stored)
            if row and valid:
                db.execute("DELETE FROM login_attempts WHERE key=?", (key,))
                token = _open_session(db, row["id"], now)
                user = public_user(row, _read_preferences(db, row["id"]))
            else:
                db.execute("""INSERT INTO login_attempts VALUES(?,1,?)
                              ON CONFLICT(key) DO UPDATE SET count=count+1""", (key, now + 900))
                token = None
        if token is None:
            raise ApiError(401, "Usuário ou senha incorretos.")
        return token, user

    def admin_login(self):
        """Abre uma sessão da conta admin, criando-a na primeira vez.

        A senha é aleatória e não é guardada em lugar nenhum: a conta só entra
        por aqui. Quem chama confere antes se o acesso vem do próprio computador.
        """
        with self.db.transaction() as db:
            row = db.execute("SELECT * FROM users WHERE login=?", (ADMIN_LOGIN,)).fetchone()
            if row is None:
                db.execute("INSERT INTO users VALUES(?,?,?,?,?)", (
                    uuid4().hex, ADMIN_LOGIN, ADMIN_NICKNAME, ADMIN_AGE,
                    password_hash(secrets.token_urlsafe(32)),
                ))
                row = db.execute("SELECT * FROM users WHERE login=?", (ADMIN_LOGIN,)).fetchone()
            token = _open_session(db, row["id"], time.time())
            return token, public_user(row, _read_preferences(db, row["id"]))

    def current(self, token):
        if not token:
            return None
        with self.db.transaction() as db:
            row = db.execute("""SELECT users.* FROM users JOIN sessions ON users.id=sessions.user_id
                                WHERE token=? AND expires>?""",
                             (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
            return public_user(row, _read_preferences(db, row["id"])) if row else None

    def logout(self, token):
        with self.db.transaction() as db:
            db.execute("DELETE FROM sessions WHERE token=?", (hashlib.sha256(token.encode()).hexdigest(),))
