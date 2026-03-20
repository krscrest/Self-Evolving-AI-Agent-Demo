import hashlib
import secrets
from app.config import settings

# Simple in-memory session store for demo purposes
_sessions: dict[str, str] = {}


def authenticate(username: str, password: str) -> str | None:
    """Authenticate user and return a session token, or None if invalid."""
    if username == settings.LOGIN_USERNAME and password == settings.LOGIN_PASSWORD:
        token = secrets.token_hex(32)
        _sessions[token] = username
        return token
    return None


def validate_session(token: str) -> bool:
    """Check if a session token is valid."""
    return token in _sessions


def logout(token: str) -> None:
    """Remove a session token."""
    _sessions.pop(token, None)
