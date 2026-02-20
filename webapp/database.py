"""SQLite database setup and helpers."""

import sqlite3
from flask import g, current_app

SCHEMA = """
CREATE TABLE IF NOT EXISTS years (
    year INTEGER PRIMARY KEY,
    total_games INTEGER NOT NULL,
    top500_games INTEGER NOT NULL,
    score REAL NOT NULL,
    seed INTEGER NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS games (
    game_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    year_published INTEGER NOT NULL REFERENCES years(year),
    rank INTEGER NOT NULL,
    thumbnail_url TEXT
);

CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY,
    round INTEGER NOT NULL,
    position INTEGER NOT NULL,
    year_a INTEGER REFERENCES years(year),
    year_b INTEGER REFERENCES years(year),
    winner INTEGER REFERENCES years(year),
    next_match_id INTEGER REFERENCES matches(match_id),
    is_active INTEGER NOT NULL DEFAULT 0,
    UNIQUE(round, position)
);

CREATE TABLE IF NOT EXISTS votes (
    vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL REFERENCES matches(match_id),
    voted_for INTEGER NOT NULL REFERENCES years(year),
    voter_id TEXT NOT NULL,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    UNIQUE(match_id, voter_id)
);

CREATE TABLE IF NOT EXISTS tournament_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS voter_finalizations (
    voter_id TEXT PRIMARY KEY,
    finalized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
