"""
Real PKCE OAuth for BinanceClawBot
Supports: OpenAI Codex, Google Gemini CLI, Antigravity (Google IDE)
Works on BOTH web (runs behind FastAPI) AND CMD (opens browser locally)

Usage:
    CMD: py -3 oauth_connect.py openai
         py -3 oauth_connect.py gemini
         py -3 oauth_connect.py antigravity
"""
from __future__ import annotations
import asyncio
import base64
import hashlib
import json
import os
import secrets
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional
import httpx
from loguru import logger

# ── Token Storage ────────────────────────────────────────────────────────────
TOKEN_DIR = Path.home() / ".config" / "bianceclawbot"
TOKEN_DIR.mkdir(parents=True, exist_ok=True)

def _token_path(provider: str) -> Path:
    return TOKEN_DIR / f"{provider}_token.json"

def save_token(provider: str, token: dict):
    path = _token_path(provider)
    path.write_text(json.dumps(token, indent=2))
    path.chmod(0o600)
    logger.success(f"✅ {provider.upper()} token saved to {path}")

def load_token(provider: str) -> Optional[dict]:
    path = _token_path(provider)
    if path.exists():
        try: return json.loads(path.read_text())
        except Exception: pass
    return None

def get_access_token(provider: str) -> Optional[str]:
    """Get valid access token, refresh if needed"""
    token = load_token(provider)
    if not token:
        return None
    # Check expiry
    if token.get("expires_at", 0) > time.time() + 60:
        return token.get("access_token")
    # Try refresh
    cfg = PROVIDERS.get(provider, {})
    if token.get("refresh_token") and cfg.get("token_url"):
        try:
            refreshed = _refresh_token(cfg, token["refresh_token"])
            if refreshed:
                refreshed["refresh_token"] = token["refresh_token"]
                save_token(provider, refreshed)
                return refreshed.get("access_token")
        except Exception as e:
            logger.warning(f"Token refresh failed for {provider}: {e}")
    return None

def _refresh_token(cfg: dict, refresh_token: str) -> Optional[dict]:
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": cfg["client_id"],
    }
    r = httpx.post(cfg["token_url"], data=data)
    r.raise_for_status()
    result = r.json()
    result["expires_at"] = time.time() + result.get("expires_in", 3600)
    return result

# ── PKCE Helpers ─────────────────────────────────────────────────────────────
def pkce_pair() -> tuple[str, str]:
    """Returns (verifier, challenge_S256)"""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge

# ── Provider Definitions ─────────────────────────────────────────────────────
PROVIDERS = {
    # ─ OpenAI Codex ─────────────────────────────────────────────────────────
    # Public client used by Codex CLI (no secret needed - PKCE only)
    # Source: openai/codex-cli, client_id confirmed public
    "openai": {
        "client_id": "app_EMoamEEZ73f0CkXaXp7hrann",
        "auth_url": "https://auth.openai.com/oauth/authorize",
        "token_url": "https://auth.openai.com/oauth/token",
        "scopes": "openid profile email offline_access",
        "redirect_port": 1455,
        "redirect_path": "/auth/callback",
        "extra_params": {
            "codex_cli_simplified_flow": "true",
            "id_token_add_organizations": "true",
            "originator": "bianceclawbot",
        },
    },
    # ─ Google Gemini CLI ────────────────────────────────────────────────────
    # Gemini CLI uses Google OAuth with PKCE, user's own Google account
    # Scope: cloud-platform for Vertex AI or generative-language for Gemini API
    "gemini": {
        "client_id": os.environ.get("GEMINI_OAUTH_CLIENT_ID", ""),
        "client_secret": os.environ.get("GEMINI_OAUTH_CLIENT_SECRET", ""),
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": "openid email profile https://www.googleapis.com/auth/generative-language",
        "redirect_port": 8085,
        "redirect_path": "/oauth2callback",
        "extra_params": {
            "access_type": "offline",
            "prompt": "consent",
        },
    },
    # ─ Antigravity (Google's internal IDE — same Google OAuth) ──────────────
    # Uses Google accounts.google.com with generativelanguage scope
    # The Antigravity client_id is the same as Gemini CLI's Google project
    "antigravity": {
        "client_id": os.environ.get("ANTIGRAVITY_OAUTH_CLIENT_ID", ""),
        "client_secret": os.environ.get("ANTIGRAVITY_OAUTH_CLIENT_SECRET", ""),
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": "openid email profile https://www.googleapis.com/auth/cloud-platform",
        "redirect_port": 8086,
        "redirect_path": "/oauth2callback",
        "extra_params": {
            "access_type": "offline",
            "prompt": "consent",
        },
    },
}

# ── Local Callback Server ────────────────────────────────────────────────────
class _CallbackReceiver:
    """Tiny HTTP server that catches the OAuth callback"""
    def __init__(self):
        self.code: Optional[str] = None
        self.error: Optional[str] = None

def _run_callback_server(port: int, path: str) -> Optional[str]:
    receiver = _CallbackReceiver()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass  # silence logs
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != path:
                self.send_response(404); self.end_headers(); return
            params = dict(urllib.parse.parse_qsl(parsed.query))
            if "code" in params:
                receiver.code = params["code"]
                html = b"<h1>Authentication successful!</h1><p>You can close this window and return to BinanceClawBot.</p>"
            else:
                receiver.error = params.get("error", "unknown")
                html = b"<h1>Authentication failed</h1><p>Check terminal for details.</p>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html)

    server = HTTPServer(("127.0.0.1", port), Handler)
    server.timeout = 120  # 2 minute timeout
    server.handle_request()
    server.server_close()
    return receiver.code

# ── Main Auth Flow ────────────────────────────────────────────────────────────
def authenticate_pkce(provider: str) -> bool:
    """
    Full PKCE OAuth flow for CMD usage.
    Opens browser automatically, handles callback on local port.
    """
    cfg = PROVIDERS.get(provider)
    if not cfg:
        logger.error(f"Unknown provider: {provider}. Choose: openai, gemini, antigravity")
        return False

    if not cfg.get("client_id"):
        logger.error(f"❌ {provider.upper()} OAuth requires GEMINI_OAUTH_CLIENT_ID / ANTIGRAVITY_OAUTH_CLIENT_ID in .env")
        logger.info("📝 For Gemini/Antigravity: create OAuth 2.0 'Desktop' app at console.cloud.google.com")
        return False

    verifier, challenge = pkce_pair()
    state = secrets.token_hex(16)
    port = cfg["redirect_port"]
    redirect_uri = f"http://127.0.0.1:{port}{cfg['redirect_path']}"

    params = {
        "response_type": "code",
        "client_id": cfg["client_id"],
        "redirect_uri": redirect_uri,
        "scope": cfg["scopes"],
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
        **cfg.get("extra_params", {}),
    }
    auth_url = cfg["auth_url"] + "?" + urllib.parse.urlencode(params)

    print(f"\n{'='*60}")
    print(f"  🔑 {provider.upper()} OAuth Login")
    print(f"{'='*60}")
    print(f"  Browser will open. Sign in and return here.")
    print(f"  Callback: {redirect_uri}")
    print(f"{'='*60}\n")
    print(f"  If browser doesn't open, paste this URL:\n  {auth_url}\n")

    webbrowser.open(auth_url)
    print("  Waiting for callback... (2 minute timeout)\n")

    code = _run_callback_server(port, cfg["redirect_path"])
    if not code:
        logger.error("❌ No authorization code received")
        return False

    # Exchange code for token
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": cfg["client_id"],
        "code_verifier": verifier,
    }
    if cfg.get("client_secret"):
        token_data["client_secret"] = cfg["client_secret"]

    r = httpx.post(cfg["token_url"], data=token_data)
    if r.status_code != 200:
        logger.error(f"❌ Token exchange failed: {r.text}")
        return False

    token = r.json()
    token["expires_at"] = time.time() + token.get("expires_in", 3600)
    save_token(provider, token)
    logger.success(f"✅ {provider.upper()} authenticated successfully!")
    return True

def pkce_auth_url(provider: str, redirect_uri: str) -> tuple[str, str, str]:
    """
    Generate PKCE auth URL for web OAuth (Vercel).
    Returns (auth_url, state, verifier) — store state+verifier in session.
    """
    cfg = PROVIDERS[provider]
    verifier, challenge = pkce_pair()
    state = secrets.token_hex(16)
    params = {
        "response_type": "code",
        "client_id": cfg["client_id"],
        "redirect_uri": redirect_uri,
        "scope": cfg["scopes"],
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
        **cfg.get("extra_params", {}),
    }
    url = cfg["auth_url"] + "?" + urllib.parse.urlencode(params)
    return url, state, verifier

def exchange_code(provider: str, code: str, redirect_uri: str, verifier: str) -> Optional[dict]:
    """Exchange auth code + PKCE verifier for access token (web flow)"""
    cfg = PROVIDERS[provider]
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": cfg["client_id"],
        "code_verifier": verifier,
    }
    if cfg.get("client_secret"):
        data["client_secret"] = cfg["client_secret"]
    r = httpx.post(cfg["token_url"], data=data)
    if r.status_code != 200:
        logger.error(f"Token exchange failed: {r.text}")
        return None
    token = r.json()
    token["expires_at"] = time.time() + token.get("expires_in", 3600)
    return token

def status() -> dict:
    """Check auth status for all providers"""
    result = {}
    for p in PROVIDERS:
        token = load_token(p)
        if token:
            expired = token.get("expires_at", 0) < time.time()
            result[p] = {"connected": True, "expired": expired, "has_refresh": bool(token.get("refresh_token"))}
        else:
            result[p] = {"connected": False}
    return result

# ── CLI Entry Point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    providers_list = list(PROVIDERS.keys())

    if len(sys.argv) < 2 or sys.argv[1] not in providers_list + ["status", "all"]:
        print(f"\nUsage: py oauth_connect.py <provider>")
        print(f"\nProviders:")
        for p in providers_list:
            print(f"  {p}")
        print(f"\nOther commands:")
        print(f"  status   — Check all connections")
        print(f"  all      — Connect all providers\n")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "status":
        s = status()
        print("\n📊 OAuth Connection Status:")
        for p, info in s.items():
            icon = "✅" if info["connected"] else "❌"
            detail = ""
            if info["connected"]:
                detail = " ⚠️ (expired)" if info.get("expired") else " (active)"
            print(f"  {icon} {p.upper()}{detail}")
        print()
    elif cmd == "all":
        for p in providers_list:
            print(f"\n→ Connecting {p.upper()}...")
            authenticate_pkce(p)
    else:
        authenticate_pkce(cmd)
