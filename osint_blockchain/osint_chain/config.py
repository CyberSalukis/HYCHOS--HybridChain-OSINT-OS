"""Configuration loader for the OSINT Evidence Blockchain.

Configuration precedence (highest first):
  1. Environment variables (OSINT_<KEY>)
  2. config.json in the project root (or path given by OSINT_CONFIG)
  3. Built-in defaults
"""
import json
import os
from pathlib import Path

# Project root = parent of the osint_chain package directory
ROOT = Path(__file__).resolve().parent.parent

DEFAULTS = {
    "data_dir": "data",
    "evidence_dir": "data/evidence",
    "chain_file": "data/chain/chain.jsonl",
    "users_file": "data/users.json",
    "keys_dir": "data/keys",
    "ntp_servers": ["pool.ntp.org", "time.google.com", "time.cloudflare.com"],
    "ntp_timeout": 3,
    "ntp_enabled": True,
    "timestamp_authority": "pool.ntp.org",
    "max_upload_mb": 200,
    "jwt_secret": "CHANGE_ME_IN_PRODUCTION_USE_ENV_OSINT_JWT_SECRET",
    "jwt_expiry_hours": 12,
    "host": "0.0.0.0",
    "port": 3000,
}

# Keys that should be cast away from string when read from environment
_INT_KEYS = {"ntp_timeout", "max_upload_mb", "jwt_expiry_hours", "port"}
_BOOL_KEYS = {"ntp_enabled"}
_LIST_KEYS = {"ntp_servers"}


class Config:
    """Resolved configuration object with attribute and dict-style access."""

    def __init__(self, overrides=None):
        cfg = dict(DEFAULTS)

        # Layer 2: config.json
        cfg_path = os.environ.get("OSINT_CONFIG", str(ROOT / "config.json"))
        if Path(cfg_path).is_file():
            with open(cfg_path, "r", encoding="utf-8") as fh:
                try:
                    cfg.update(json.load(fh))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid config.json: {exc}") from exc

        # Layer 1: environment variables
        for key in DEFAULTS:
            env_key = "OSINT_" + key.upper()
            if env_key in os.environ:
                cfg[key] = self._coerce(key, os.environ[env_key])

        # Explicit overrides (e.g. from CLI)
        if overrides:
            cfg.update({k: v for k, v in overrides.items() if v is not None})

        self._cfg = cfg

    @staticmethod
    def _coerce(key, value):
        if key in _INT_KEYS:
            return int(value)
        if key in _BOOL_KEYS:
            return str(value).lower() in ("1", "true", "yes", "on")
        if key in _LIST_KEYS:
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    def __getattr__(self, name):
        try:
            return self._cfg[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __getitem__(self, name):
        return self._cfg[name]

    def get(self, name, default=None):
        return self._cfg.get(name, default)

    def abspath(self, key):
        """Return an absolute path for a path-style config key."""
        val = self._cfg[key]
        p = Path(val)
        return p if p.is_absolute() else (ROOT / p)

    def ensure_dirs(self):
        """Create all required directories if they do not exist."""
        for key in ("data_dir", "evidence_dir", "keys_dir"):
            self.abspath(key).mkdir(parents=True, exist_ok=True)
        self.abspath("chain_file").parent.mkdir(parents=True, exist_ok=True)

    def as_dict(self):
        out = dict(self._cfg)
        out["jwt_secret"] = "***redacted***"
        return out


_INSTANCE = None


def get_config(reload=False, overrides=None):
    """Return a singleton Config instance."""
    global _INSTANCE
    if _INSTANCE is None or reload or overrides:
        _INSTANCE = Config(overrides=overrides)
    return _INSTANCE
