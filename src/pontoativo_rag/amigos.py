"""Amigos, notas e bloqueios entre pessoas que já praticaram juntas.

Só quem participou do mesmo encontro, já realizado e não cancelado, pode pedir
amizade ou dar nota à outra pessoa. A nota é anônima: cada pessoa vê apenas
quantas notas positivas e negativas recebeu, nunca quem as deu. Bloquear desfaz
a amizade e impede que as duas pessoas entrem nos encontros uma da outra.
"""
from .encontros import now
from .persistencia import ApiError

NOTAS = (-1, 0, 1)  # 0 apaga a nota dada


def _par(a, b):
    """Chave da amizade: o par em ordem fixa, para não haver duas linhas."""
    return (a, b) if a < b else (b, a)


def bloqueio_entre(db, a, b):
    """True se uma das duas pessoas bloqueou a outra."""
    return db.execute(
        "SELECT 1 FROM blocks WHERE (blocker=? AND blocked=?) OR (blocker=? AND blocked=?)",
        (a, b, b, a),
    ).fetchone() is not None


class Amigos:
    def __init__(self, db):
        self.db = db

    # ---------- consultas ----------
    def _usuario(self, db, user_id):
        row = db.execute("SELECT id, nickname FROM users WHERE id=?", (user_id,)).fetchone()
        if row is None:
            raise ApiError(404, "Pessoa não encontrada.")
        return row

    def _praticaram(self, db, eu):
        """Pessoas com quem ``eu`` participou de encontros já realizados."""
        rows = db.execute(
            """SELECT outro.user_id AS id, users.nickname AS apelido, events.sport AS esporte,
                      events.start AS inicio, events.place_id AS local
               FROM members AS meu
               JOIN members AS outro ON outro.event_id = meu.event_id AND outro.user_id <> meu.user_id
               JOIN events ON events.id = meu.event_id
               JOIN users ON users.id = outro.user_id
               WHERE meu.user_id = ? AND events.cancelled = 0 AND events.start <= ?
               ORDER BY events.start DESC""",
            (eu, now()),
        ).fetchall()
        pessoas = {}
        for row in rows:
            pessoa = pessoas.setdefault(row["id"], {
                "id": row["id"], "apelido": row["apelido"], "encontros": 0,
                "ultimo": {"esporte": row["esporte"], "inicio": row["inicio"], "local_id": row["local"]},
            })
            pessoa["encontros"] += 1
        return pessoas

    def _exigir_pratica(self, db, eu, outro):
        if outro == eu:
            raise ApiError(400, "Escolha outra pessoa.")
        self._usuario(db, outro)
        if outro not in self._praticaram(db, eu):
            raise ApiError(403, "Vocês precisam ter participado juntos de um encontro já realizado.")

    def resumo(self, eu):
        with self.db.transaction() as db:
            praticaram = self._praticaram(db, eu)
            bloqueei = {r["blocked"] for r in db.execute("SELECT blocked FROM blocks WHERE blocker=?", (eu,))}
            me_bloquearam = {r["blocker"] for r in db.execute("SELECT blocker FROM blocks WHERE blocked=?", (eu,))}
            escondidos = bloqueei | me_bloquearam
            amizades = {}
            for row in db.execute(
                "SELECT * FROM friendships WHERE user_a=? OR user_b=?", (eu, eu)
            ):
                outro = row["user_b"] if row["user_a"] == eu else row["user_a"]
                if row["status"] == "aceito":
                    amizades[outro] = "amigos"
                else:
                    amizades[outro] = "pedido_enviado" if row["requester"] == eu else "pedido_recebido"
            notas = {r["rated"]: r["value"] for r in db.execute("SELECT rated, value FROM ratings WHERE rater=?", (eu,))}

            def apelido(user_id):
                row = db.execute("SELECT nickname FROM users WHERE id=?", (user_id,)).fetchone()
                return row["nickname"] if row else "?"

            pessoas = []
            for pessoa in praticaram.values():
                if pessoa["id"] in escondidos:
                    continue
                pessoas.append({**pessoa, "amizade": amizades.get(pessoa["id"], "nenhuma"),
                                "minha_nota": notas.get(pessoa["id"], 0)})
            recebidas = db.execute(
                "SELECT sum(value > 0) AS positivas, sum(value < 0) AS negativas FROM ratings WHERE rated=?",
                (eu,),
            ).fetchone()
            return {
                "pessoas": pessoas,
                "amigos": [{"id": i, "apelido": apelido(i)} for i, s in amizades.items()
                           if s == "amigos" and i not in escondidos],
                "pedidos": [{"id": i, "apelido": apelido(i)} for i, s in amizades.items()
                            if s == "pedido_recebido" and i not in escondidos],
                "bloqueados": [{"id": i, "apelido": apelido(i)} for i in sorted(bloqueei)],
                # Só os totais: quem deu cada nota nunca é revelado.
                "reputacao": {"positivas": recebidas["positivas"] or 0, "negativas": recebidas["negativas"] or 0},
            }

    # ---------- ações ----------
    def pedir(self, eu, outro):
        with self.db.transaction() as db:
            self._exigir_pratica(db, eu, outro)
            if bloqueio_entre(db, eu, outro):
                raise ApiError(403, "Não é possível adicionar essa pessoa.")
            a, b = _par(eu, outro)
            row = db.execute("SELECT * FROM friendships WHERE user_a=? AND user_b=?", (a, b)).fetchone()
            if row is None:
                db.execute("INSERT INTO friendships VALUES(?,?,?,?,?)", (a, b, eu, "pendente", now()))
                return {"amizade": "pedido_enviado"}
            if row["status"] == "pendente" and row["requester"] != eu:
                # Os dois pediram: a amizade é aceita na hora.
                db.execute("UPDATE friendships SET status='aceito' WHERE user_a=? AND user_b=?", (a, b))
                return {"amizade": "amigos"}
            return {"amizade": "amigos" if row["status"] == "aceito" else "pedido_enviado"}

    def aceitar(self, eu, outro):
        with self.db.transaction() as db:
            a, b = _par(eu, outro)
            row = db.execute(
                "SELECT * FROM friendships WHERE user_a=? AND user_b=? AND status='pendente' AND requester=?",
                (a, b, outro),
            ).fetchone()
            if row is None or bloqueio_entre(db, eu, outro):
                raise ApiError(404, "Pedido de amizade não encontrado.")
            db.execute("UPDATE friendships SET status='aceito' WHERE user_a=? AND user_b=?", (a, b))
            return {"amizade": "amigos"}

    def remover(self, eu, outro):
        """Desfaz a amizade, recusa um pedido recebido ou cancela um pedido enviado."""
        with self.db.transaction() as db:
            a, b = _par(eu, outro)
            db.execute("DELETE FROM friendships WHERE user_a=? AND user_b=?", (a, b))
            return {"amizade": "nenhuma"}

    def avaliar(self, eu, outro, nota):
        if nota not in NOTAS or isinstance(nota, bool):
            raise ApiError(400, "A nota deve ser 1 (gostei), -1 (não gostei) ou 0 (sem nota).")
        with self.db.transaction() as db:
            self._exigir_pratica(db, eu, outro)
            if nota == 0:
                db.execute("DELETE FROM ratings WHERE rater=? AND rated=?", (eu, outro))
            else:
                db.execute(
                    """INSERT INTO ratings VALUES(?,?,?,?)
                       ON CONFLICT(rater, rated) DO UPDATE SET value=excluded.value, updated=excluded.updated""",
                    (eu, outro, nota, now()),
                )
            return {"minha_nota": nota}

    def bloquear(self, eu, outro):
        with self.db.transaction() as db:
            if outro == eu:
                raise ApiError(400, "Escolha outra pessoa.")
            self._usuario(db, outro)
            db.execute("INSERT OR IGNORE INTO blocks VALUES(?,?,?)", (eu, outro, now()))
            a, b = _par(eu, outro)
            db.execute("DELETE FROM friendships WHERE user_a=? AND user_b=?", (a, b))
            return {"bloqueado": True}

    def desbloquear(self, eu, outro):
        with self.db.transaction() as db:
            db.execute("DELETE FROM blocks WHERE blocker=? AND blocked=?", (eu, outro))
            return {"bloqueado": False}
