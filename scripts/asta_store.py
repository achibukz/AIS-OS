"""Private, versioned storage for Asta's health records."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

MANILA = ZoneInfo('Asia/Manila')
SCHEMA = """
CREATE TABLE profiles (id INTEGER PRIMARY KEY, at TEXT NOT NULL, data TEXT NOT NULL);
CREATE TABLE targets (id INTEGER PRIMARY KEY, at TEXT NOT NULL, data TEXT NOT NULL);
CREATE TABLE weights (date TEXT PRIMARY KEY, kg REAL NOT NULL, at TEXT NOT NULL);
CREATE TABLE foods (id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE food_cache (query TEXT PRIMARY KEY, at TEXT NOT NULL, data TEXT NOT NULL);
CREATE TABLE meals (id TEXT PRIMARY KEY, date TEXT NOT NULL, at TEXT NOT NULL,
 original TEXT NOT NULL, current TEXT NOT NULL, tier TEXT NOT NULL);
CREATE INDEX meals_date ON meals(date);
CREATE TABLE corrections (id INTEGER PRIMARY KEY, meal_id TEXT NOT NULL REFERENCES meals(id)
 ON DELETE CASCADE, at TEXT NOT NULL, field TEXT NOT NULL, old TEXT NOT NULL,
 new TEXT NOT NULL, reason TEXT NOT NULL);
CREATE TABLE templates (name TEXT PRIMARY KEY, data TEXT NOT NULL, samples INTEGER NOT NULL);
CREATE TABLE media (hash TEXT PRIMARY KEY, path TEXT NOT NULL, mime TEXT NOT NULL,
 width INTEGER NOT NULL, height INTEGER NOT NULL);
CREATE TABLE adherence (event_id TEXT PRIMARY KEY, state TEXT NOT NULL, source TEXT NOT NULL,
 at TEXT NOT NULL);
PRAGMA user_version=1;
"""


class AstaError(ValueError):
    pass


def now():
    return datetime.now(MANILA).isoformat()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True)


def safe_path(path):
    path = Path(os.path.abspath(path))
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise AstaError('unsafe_symlink')
    return path


def private_directory(path):
    path = safe_path(path)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)
    return path


@contextmanager
def open_store(path):
    path = safe_path(path)
    private_directory(path.parent)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    os.close(fd)
    path.chmod(0o600)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    try:
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('BEGIN IMMEDIATE')
        version = db.execute('PRAGMA user_version').fetchone()[0]
        if version == 0:
            for statement in SCHEMA.split(';'):
                if statement.strip():
                    db.execute(statement)
        elif version != 1:
            raise AstaError('unsupported_schema')
        db.commit()
        yield db
    finally:
        db.close()


def latest(db, table):
    if table not in {'profiles', 'targets'}:
        raise AstaError('invalid_table')
    row = db.execute(f'SELECT * FROM {table} ORDER BY id DESC LIMIT 1').fetchone()
    return {'version': row['id'], 'at': row['at'], **json.loads(row['data'])} if row else None


@contextmanager
def open_reader(path):
    path = safe_path(path)
    if not path.is_file():
        raise AstaError('tracking_not_initialized')
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=10)
    db.row_factory = sqlite3.Row
    try:
        db.execute('PRAGMA query_only=ON')
        if db.execute('PRAGMA user_version').fetchone()[0] != 1:
            raise AstaError('unsupported_schema')
        db.execute('BEGIN')
        yield db
    finally:
        db.close()
