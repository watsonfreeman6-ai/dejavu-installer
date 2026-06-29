"""Session JWT management for Dejavu MCP client.

Handles:
- Session JWT loading/caching from ~/.dejavu/session.jwt
- Silent refresh on 401 (re-auth with device_id, retry)
- Cache eviction on subscription lapse (>7 days)
- Device identity via random UUID (not hardware-derived)
"""
import json
import os
import time
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

import httpx

DEJAVU_HOME = Path.home() / ".dejavu"

SESSION_PATH = DEJAVU_HOME / "session.jwt"
CONFIG_PATH = DEJAVU_HOME / "config.json"
SKILLS_CACHE = DEJAVU_HOME / "skills"
DEVICE_ID_PATH = DEJAVU_HOME / "device_id"

API_BASE = os.environ.get("DEJAVU_API_BASE", "https://dejavu.keepingtrack.biz")


def load_session() -> Optional[str]:
    """Return cached JWT if locally valid, None if expired or missing."""
    if not SESSION_PATH.exists():
        return None
    try:
        data = json.loads(SESSION_PATH.read_text())
        token = data.get("token", "")
        exp = data.get("expires_at", 0)
        if time.time() > exp:
            return None
        return token
    except Exception:
        return None


def save_session(token: str, expires_in: int) -> None:
    """Cache JWT with local expiry timestamp (5-min safety margin)."""
    SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "token": token,
        "expires_at": int(time.time()) + expires_in - 300,
    }
    SESSION_PATH.write_text(json.dumps(data))


def get_api_key() -> Optional[str]:
    """Read API key from ~/.dejavu/config.json."""
    if not CONFIG_PATH.exists():
        return None
    try:
        return json.loads(CONFIG_PATH.read_text()).get("api_key")
    except Exception:
        return None


def get_device_id() -> str:
    """Return stable device ID. Uses the dejavu-installer module if available."""
    try:
        from dejavu_installer.src.device_id import get_device_id as _get_id
        return _get_id()
    except ImportError:
        pass
    
    # Fallback: read directly
    if DEVICE_ID_PATH.exists():
        return DEVICE_ID_PATH.read_text().strip()
    
    # Generate on first call
    import uuid
    DEJAVU_HOME.mkdir(parents=True, exist_ok=True)
    device_id = str(uuid.uuid4())
    DEVICE_ID_PATH.write_text(device_id + "\n")
    return device_id


def start_session() -> dict:
    """POST /session/start, return {token, expires_in} or raise."""
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("No API key found. Run the Dejavu installer first.")
    
    device_id = get_device_id()
    import socket
    device_name = socket.gethostname()
    
    resp = httpx.post(
        f"{API_BASE}/session/start",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"device_id": device_id, "device_name": device_name},
        timeout=10,
    )
    if resp.status_code == 429:
        raise RuntimeError(
            "Device limit reached (5 devices max). "
            "Revoke an unused device at https://dejavu.dev/dashboard"
        )
    if resp.status_code != 200:
        raise RuntimeError(f"Session start failed: HTTP {resp.status_code}")
    
    data = resp.json()
    save_session(data["token"], data["expires_in"])
    return data


def evict_if_lapsed() -> bool:
    """If subscription lapsed >7 days, clear gated cache. Returns True if evicted."""
    status_path = DEJAVU_HOME / "subscription.json"
    if not status_path.exists():
        return False
    
    try:
        status = json.loads(status_path.read_text())
        lapsed_at = status.get("lapsed_at")
        if not lapsed_at:
            return False
        
        lapsed = datetime.fromisoformat(lapsed_at)
        if datetime.utcnow() - lapsed > timedelta(days=7):
            # Clear gated skill content (not user's own skills)
            if SKILLS_CACHE.exists():
                shutil.rmtree(SKILLS_CACHE)
            # Clear session
            SESSION_PATH.unlink(missing_ok=True)
            return True
    except Exception:
        pass
    return False


class SessionRefreshWrapper:
    """Wrapper that catches 401, silently re-authenticates, retries once."""
    
    def __init__(self):
        self._reauth_in_progress = False
    
    def __call__(self, fn, *args, **kwargs):
        """Call fn. On 401, attempt silent re-auth and retry."""
        result = fn(*args, **kwargs)
        
        # Check for 401 response
        status = None
        if hasattr(result, 'status_code'):
            status = result.status_code
        elif isinstance(result, dict) and 'error' in result:
            # Could be an error dict from MCP
            error_msg = str(result.get('error', '')).lower()
            if '401' in error_msg or 'unauthorized' in error_msg:
                status = 401
        
        if status == 401 and not self._reauth_in_progress:
            self._reauth_in_progress = True
            try:
                start_session()  # Silent re-auth
                result = fn(*args, **kwargs)  # Retry
            except Exception:
                evict_if_lapsed()
                raise RuntimeError(
                    "Dejavu session expired and re-authentication failed. "
                    "Visit https://dejavu.dev/connect to restore your subscription."
                )
            finally:
                self._reauth_in_progress = False
        
        return result


# Singleton
session_refresh = SessionRefreshWrapper()
