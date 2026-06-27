"""JSON Schema validation for evidence metadata.

Loads the bundled schema once and validates metadata dicts, raising a
descriptive ``MetadataValidationError`` on failure so the API can return a
helpful 400 response.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft7Validator

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
EVIDENCE_SCHEMA_PATH = SCHEMA_DIR / "evidence_metadata.schema.json"


class MetadataValidationError(ValueError):
    """Raised when evidence metadata fails schema validation."""

    def __init__(self, errors):
        self.errors = errors
        super().__init__("Metadata validation failed: " + "; ".join(errors))


@lru_cache(maxsize=4)
def _load_validator(schema_path: str) -> Draft7Validator:
    with open(schema_path, "r", encoding="utf-8") as fh:
        schema = json.load(fh)
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)


def validate_evidence_metadata(metadata: dict) -> None:
    """Validate metadata against the evidence schema. Raises on failure."""
    validator = _load_validator(str(EVIDENCE_SCHEMA_PATH))
    errors = sorted(validator.iter_errors(metadata), key=lambda e: e.path)
    if errors:
        messages = []
        for err in errors:
            loc = "/".join(str(p) for p in err.path) or "(root)"
            messages.append(f"{loc}: {err.message}")
        raise MetadataValidationError(messages)


def get_schema() -> dict:
    """Return the raw evidence metadata schema (for the API/docs)."""
    with open(EVIDENCE_SCHEMA_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)
