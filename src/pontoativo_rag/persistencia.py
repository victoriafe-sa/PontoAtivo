"""Persistência transacional do piloto de encontros."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class Database:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.transaction() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, login TEXT UNIQUE NOT NULL,
                    nickname TEXT NOT NULL, age TEXT NOT NULL, password TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
                    expires REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS login_attempts (
                    key TEXT PRIMARY KEY, count INTEGER NOT NULL, expires REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY, organizer TEXT NOT NULL REFERENCES users(id),
                    place_id TEXT NOT NULL, sport TEXT NOT NULL, start TEXT NOT NULL,
                    level TEXT NOT NULL, age TEXT NOT NULL, format TEXT NOT NULL,
                    capacity INTEGER NOT NULL CHECK(capacity BETWEEN 2 AND 20),
                    cancelled INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS members (
                    event_id TEXT NOT NULL REFERENCES events(id),
                    user_id TEXT NOT NULL REFERENCES users(id),
                    PRIMARY KEY(event_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS event_requests (
                    user_id TEXT NOT NULL REFERENCES users(id),
                    request_id TEXT NOT NULL,
                    event_id TEXT NOT NULL REFERENCES events(id),
                    payload TEXT NOT NULL,
                    PRIMARY KEY(user_id, request_id)
                );
                CREATE TABLE IF NOT EXISTS preferences (
                    user_id TEXT PRIMARY KEY REFERENCES users(id),
                    sports TEXT NOT NULL DEFAULT '[]', region TEXT NOT NULL DEFAULT ''
                );
                -- Amizade entre duas pessoas: user_a < user_b, uma linha por par.
                CREATE TABLE IF NOT EXISTS friendships (
                    user_a TEXT NOT NULL REFERENCES users(id),
                    user_b TEXT NOT NULL REFERENCES users(id),
                    requester TEXT NOT NULL REFERENCES users(id),
                    status TEXT NOT NULL CHECK(status IN ('pendente', 'aceito')),
                    created TEXT NOT NULL,
                    PRIMARY KEY(user_a, user_b), CHECK(user_a < user_b)
                );
                -- Nota anônima de 1 a 5 estrelas: só a média e o total chegam aos outros.
                CREATE TABLE IF NOT EXISTS notas (
                    rater TEXT NOT NULL REFERENCES users(id),
                    rated TEXT NOT NULL REFERENCES users(id),
                    value INTEGER NOT NULL CHECK(value BETWEEN 1 AND 5),
                    updated TEXT NOT NULL,
                    PRIMARY KEY(rater, rated)
                );
                CREATE TABLE IF NOT EXISTS blocks (
                    blocker TEXT NOT NULL REFERENCES users(id),
                    blocked TEXT NOT NULL REFERENCES users(id),
                    created TEXT NOT NULL,
                    PRIMARY KEY(blocker, blocked)
                );
                CREATE INDEX IF NOT EXISTS notas_rated ON notas(rated);
                CREATE INDEX IF NOT EXISTS events_start ON events(start);
                CREATE INDEX IF NOT EXISTS members_user ON members(user_id);
            """)

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()
