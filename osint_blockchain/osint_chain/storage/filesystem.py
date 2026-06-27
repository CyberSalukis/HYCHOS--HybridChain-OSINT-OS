"""Write-once immutable filesystem evidence store.

Design
------
* Content-addressed: files are stored under ``<evidence_dir>/<ab>/<hash>``
  where ``ab`` is the first two hex chars of the SHA-256 (sharding to avoid
  huge directories).
* Write-once: once written, the file's permissions are set to read-only
  (0o444) and any attempt to store different content under the same hash is
  impossible (identical content => identical hash => idempotent no-op). An
  attempt to overwrite an existing object with different bytes can never
  happen because the path is derived from the content hash.
* A sidecar ``<hash>.meta.json`` records the original filename, content type,
  size and storage time for provenance.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
import time
from pathlib import Path
from typing import BinaryIO

from ..core import crypto
from .base import EvidenceStore, StorageError

READ_ONLY = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH  # 0o444


class ImmutableFileStore(EvidenceStore):
    """Content-addressed, write-once local filesystem store."""

    def __init__(self, evidence_dir: str):
        self.root = Path(evidence_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Path helpers
    # ------------------------------------------------------------------ #
    def _object_path(self, file_hash: str) -> Path:
        return self.root / file_hash[:2] / file_hash

    def path_for(self, file_hash: str) -> str:
        return str(self._object_path(file_hash))

    def _meta_path(self, file_hash: str) -> Path:
        return self.root / file_hash[:2] / f"{file_hash}.meta.json"

    # ------------------------------------------------------------------ #
    # API
    # ------------------------------------------------------------------ #
    def exists(self, file_hash: str) -> bool:
        return self._object_path(file_hash).is_file()

    def store(self, fileobj: BinaryIO, original_filename: str,
              content_type: str = "application/octet-stream") -> dict:
        # Stream to a temp file while hashing
        tmp_fd, tmp_path = tempfile.mkstemp(dir=str(self.root), prefix=".ingest-")
        size = 0
        try:
            with os.fdopen(tmp_fd, "wb") as tmp:
                while True:
                    chunk = fileobj.read(1024 * 1024)
                    if not chunk:
                        break
                    if isinstance(chunk, str):
                        chunk = chunk.encode("utf-8")
                    tmp.write(chunk)
                    size += len(chunk)
            file_hash = crypto.sha256_file(tmp_path)
            dest = self._object_path(file_hash)
            dest.parent.mkdir(parents=True, exist_ok=True)

            if dest.exists():
                # Identical content already stored -> idempotent, drop temp.
                os.unlink(tmp_path)
            else:
                # Atomic move into place, then lock read-only (write-once).
                shutil.move(tmp_path, dest)
                try:
                    os.chmod(dest, READ_ONLY)
                except OSError:
                    pass  # best effort on filesystems without perm support

            descriptor = {
                "file_hash": file_hash,
                "stored_path": str(dest),
                "size": size if not self._meta_path(file_hash).exists()
                else self._read_meta(file_hash).get("size", size),
                "original_filename": original_filename,
                "content_type": content_type,
            }
            self._write_meta(file_hash, descriptor)
            return descriptor
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def _write_meta(self, file_hash: str, descriptor: dict) -> None:
        meta_path = self._meta_path(file_hash)
        if meta_path.exists():
            return  # never overwrite provenance for an existing object
        meta = dict(descriptor)
        meta["stored_at"] = time.time()
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2)
        try:
            os.chmod(meta_path, READ_ONLY)
        except OSError:
            pass

    def _read_meta(self, file_hash: str) -> dict:
        meta_path = self._meta_path(file_hash)
        if not meta_path.exists():
            return {}
        with open(meta_path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def open(self, file_hash: str) -> BinaryIO:
        path = self._object_path(file_hash)
        if not path.is_file():
            raise StorageError(f"Object {file_hash} not found")
        return open(path, "rb")

    def verify(self, file_hash: str) -> bool:
        """Re-hash a stored object and confirm it matches its hash/name."""
        if not self.exists(file_hash):
            return False
        return crypto.sha256_file(self.path_for(file_hash)) == file_hash
