"""Validate attachments and retain meal images by content hash."""
from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from asta_store import AstaError, private_directory, safe_path


def inspect_photo(path, attachments):
    if not isinstance(path, str):
        raise AstaError('photo_path_required')
    source = safe_path(Path(path))
    root = safe_path(attachments)
    if not source.is_relative_to(root) or not source.is_file():
        raise AstaError('invalid_photo_path')
    if source.stat().st_size > 25 * 1024 * 1024:
        raise AstaError('photo_too_large')
    content = source.read_bytes()
    try:
        import io
        with Image.open(io.BytesIO(content)) as image:
            if image.format not in ('JPEG', 'PNG', 'WEBP'):
                raise AstaError('unsupported_image')
            width, height = image.size
            if width * height > 40_000_000:
                raise AstaError('photo_too_large')
            mime = Image.MIME[image.format]
            extension = {'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp'}[image.format]
            image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise AstaError('invalid_image') from None
    return {'hash': hashlib.sha256(content).hexdigest(), 'mime': mime, 'width': width,
            'height': height, 'extension': extension, 'source': source, 'content': content}


def retain(db, photo, meals_root, on):
    row = db.execute('SELECT * FROM media WHERE hash=?', (photo['hash'],)).fetchone()
    if row:
        destination = safe_path(Path(row['path']))
        if not destination.is_relative_to(safe_path(meals_root)):
            raise AstaError('invalid_media_path')
    else:
        at = datetime.fromisoformat(on)
        directory = private_directory(meals_root / f'{at.year:04d}' / f'{at.month:02d}')
        destination = directory / (photo['hash'] + photo['extension'])
    safe_path(destination)
    if destination.exists():
        if hashlib.sha256(destination.read_bytes()).hexdigest() != photo['hash']:
            raise AstaError('media_hash_mismatch')
    else:
        temporary = destination.with_name('.' + uuid.uuid4().hex + '.partial')
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(fd, 'wb') as output:
                output.write(photo['content'])
                output.flush()
                os.fsync(output.fileno())
            temporary.replace(destination)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    db.execute('INSERT OR IGNORE INTO media VALUES(?,?,?,?,?)',
               (photo['hash'], str(destination), photo['mime'], photo['width'], photo['height']))
    return {'hash': photo['hash'], 'path': str(destination), 'mime': photo['mime'],
            'width': photo['width'], 'height': photo['height']}


def finish(photo):
    source = photo['source']
    if source.exists() and hashlib.sha256(source.read_bytes()).hexdigest() == photo['hash']:
        source.unlink()
