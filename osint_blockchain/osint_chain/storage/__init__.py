"""Storage abstraction package."""

from .filesystem import ImmutableFileStore, StorageError

__all__ = ["ImmutableFileStore", "StorageError"]
