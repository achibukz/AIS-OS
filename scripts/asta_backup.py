#!/usr/bin/env python3
"""Create a verified SQLite backup before pruning older Asta backups."""
from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from asta_store import AstaError, private_directory, safe_path
from gcal import user_home


def backup(source, directory):
    source = safe_path(source)
    if not source.is_file():
        raise AstaError('backup_source_missing')
    directory = private_directory(directory)
    name = 'asta-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '-' + uuid.uuid4().hex[:8]
    partial = directory / (name + '.partial')
    destination = directory / (name + '.sqlite3')
    fd = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    os.close(fd)
    try:
        src = sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=10)
        dst = sqlite3.connect(partial)
        try:
            src.backup(dst)
            if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise AstaError('backup_integrity_failed')
        finally:
            src.close()
            dst.close()
        partial.rename(destination)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    copies = sorted(directory.glob('asta-*.sqlite3'), reverse=True)
    for old in copies[14:]:
        if old.is_file() and not old.is_symlink():
            old.unlink()
    return destination


if __name__ == '__main__':
    home = user_home()
    path = backup(home / '.local/state/achios/asta/asta.sqlite3',
                  home / 'Documents/Files/training/asta/backups')
    print('Asta backup verified: ' + path.name)
