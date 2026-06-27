"""JWT auth helpers and Flask decorators for role/permission enforcement."""
from __future__ import annotations

import functools
import time
from typing import Callable

import jwt
from flask import current_app, g, jsonify, request

from .users import UserManager


def issue_token(user: dict, secret: str, expiry_hours: int) -> str:
    now = int(time.time())
    payload = {
        "sub": user["id"],
        "username": user["username"],
        "role": user["role"],
        "iat": now,
        "exp": now + expiry_hours * 3600,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> dict:
    return jwt.decode(token, secret, algorithms=["HS256"])


def _extract_token() -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return request.args.get("token")


def login_required(fn: Callable) -> Callable:
    """Authenticate the request and attach the user to ``g.user``."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "authentication required"}), 401
        try:
            payload = decode_token(token, current_app.config["JWT_SECRET"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "invalid token"}), 401
        users: UserManager = current_app.config["SERVICE"].users
        user = users.users.get(payload["sub"])
        if not user or not user.get("active", True):
            return jsonify({"error": "user not found or inactive"}), 401
        g.user = user
        return fn(*args, **kwargs)

    return wrapper


def require_permission(permission: str) -> Callable:
    """Ensure the authenticated user's role grants ``permission``."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if not UserManager.has_permission(g.user, permission):
                return jsonify({
                    "error": "forbidden",
                    "required_permission": permission,
                    "role": g.user["role"],
                }), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator
