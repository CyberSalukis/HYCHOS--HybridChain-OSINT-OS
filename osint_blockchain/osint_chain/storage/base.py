"""Abstract storage interface.

A storage backend is responsible only for storing the *original evidence
bytes* in a write-once manner and returning a descriptor. The blockchain
itself never stores file contents - only hashes and metadata. Implementing
this interface (e.g. for S3 with object-lock) lets the rest of the system
stay unchanged.
"""
from __future__ import annotations

import abc
from typing import BinaryIO


class StorageError(Exception):
    """Raised on storage-level failures (e.g. overwrite attempt)."""


class EvidenceStore(abc.ABC):
    """Abstract write-once evidence store keyed by content hash."""

    @abc.abstractmethod
    def store(self, fileobj: BinaryIO, original_filename: str,
              content_type: str = "application/octet-stream") -> dict:
        """Persist bytes write-once and return a descriptor dict.

        Descriptor contains at least: file_hash, stored_path, size,
        original_filename, content_type.
        """

    @abc.abstractmethod
    def open(self, file_hash: str) -> BinaryIO:
        """Open a stored object for reading by its content hash."""

    @abc.abstractmethod
    def exists(self, file_hash: str) -> bool:
        """Return True if an object with this hash is stored."""

    @abc.abstractmethod
    def path_for(self, file_hash: str) -> str:
        """Return the absolute path/locator for a stored object."""
