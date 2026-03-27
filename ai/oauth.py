"""
Multi-provider OAuth manager.
Supports: OpenAI, Google Gemini CLI, Antigravity (Google DeepMind)
Tokens are stored encrypted locally — no API keys stored in .env
"""
from __future__ import annotations
import base64, hashlib, json, os, secrets, time, webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode, urlparse, parse_qs
import httpx
from loguru import logger
from config.settings import settings

def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def _pkce():
    v = _b64url(secrets.token_bytes(48))
    c = _b64url(hashlib.sha256(v.encode()).digest())
    return v, c

PROVIDERS = {
    "openai": {
        "auth_url":  "https://auth.openai.com/oauth/authorize",
        "token_url": "https://auth.openai.com/oauth/token",
        "scopes":    "openid profile email",
    },
    "gemini": {
        "auth_url":  "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes":    "openid email profile https://www.googleapis.com/auth/generative-language",
    },
    "antigravity": {
        "auth_url":  "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes":    "openid email profile",
    },
}


class _CallbackHandler(BaseHTTPRequestHandler):
    code: Optional[str] = None
    def do_GET(self):
        p = parse_qs(urlparse(self.path).query)
        _CallbackHandler.code = p.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body style='background:#0a0a0a;color:#00ff88;font-family:sans-serif;text-align:center;padding:60px'><h1>&#10003; Authenticated!</h1><p>You can close this tab.</p></body></html>")
    def log_message(self, *a): pass


class OAuthProvider:
    def __init__(self, name: str, client_id: str, client_secret: str, redirect_uri: str):
        self.name = name
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.cfg = PROVIDERS.get(name, PROVIDERS["openai"])
        self._token_file = Path(settings.token_file).parent / f".oauth_{name}.json"
        self._tokens: dict = {}
        self._load()

    def _load(self):
        if self._token_file.exists():
            try: self._tokens = json.loads(self._token_file.read_text())
            except Exception: pass

    def _save(self, t: dict):
        self._tokens = t
        self._token_file.write_text(json.dumps(t, indent=2))
        try: os.chmod(self._token_file, 0o600)
        except Exception: pass

    def access_token(self) -> Optional[str]:
        if not self._tokens: return None
        if time.time() < self._tokens.get("expires_at", 0) - 60:
            return self._tokens.get("access_token")
        if "refresh_token" in self._tokens:
            return self._refresh()
        return None

    def _refresh(self) -> Optional[str]:
        try:
            r = httpx.post(self.cfg["token_url"], data={
                "grant_type": "refresh_token",
                "refresh_token": self._tokens["refresh_token"],
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            })
            r.raise_for_status()
            t = r.json(); t["expires_at"] = time.time() + t.get("expires_in", 3600)
            self._save(t); return t["access_token"]
        except Exception as e:
            logger.error(f"[{self.name}] Token refresh failed: {e}"); return None

    def authenticate(self, use_pkce: bool = True):
        if not self.client_id:
            logger.warning(f"[{self.name}] No client_id configured"); return
        v, c = _pkce()
        state = secrets.token_urlsafe(16)
        p: dict = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.cfg["scopes"],
            "state": state,
        }
        if use_pkce:
            p["code_challenge"] = c
            p["code_challenge_method"] = "S256"

        url = f"{self.cfg['auth_url']}?{urlencode(p)}"
        logger.info(f"[{self.name}] Open in browser:\n{url}")
        webbrowser.open(url)

        port = int(urlparse(self.redirect_uri).port or 8080)
        _CallbackHandler.code = None
        srv = HTTPServer(("localhost", port), _CallbackHandler)
        srv.timeout = 120
        deadline = time.time() + 120
        while _CallbackHandler.code is None and time.time() < deadline:
            srv.handle_request()

        code = _CallbackHandler.code
        if not code: logger.error(f"[{self.name}] No code received"); return

        data: dict = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if use_pkce: data["code_verifier"] = v
        r = httpx.post(self.cfg["token_url"], data=data)
        r.raise_for_status()
        t = r.json(); t["expires_at"] = time.time() + t.get("expires_in", 3600)
        self._save(t)
        logger.success(f"[{self.name}] Authenticated!")

    def is_authenticated(self) -> bool:
        return self.access_token() is not None


class MultiOAuthManager:
    """Manages OpenAI + Gemini + Antigravity OAuth providers."""
    def __init__(self):
        redirect = settings.openai_redirect_uri
        self.providers: dict[str, OAuthProvider] = {
            "openai": OAuthProvider("openai",
                settings.openai_oauth_client_id,
                settings.openai_oauth_client_secret,
                redirect),
            "gemini": OAuthProvider("gemini",
                os.getenv("GEMINI_OAUTH_CLIENT_ID", ""),
                os.getenv("GEMINI_OAUTH_CLIENT_SECRET", ""),
                redirect),
            "antigravity": OAuthProvider("antigravity",
                os.getenv("ANTIGRAVITY_CLIENT_ID", ""),
                os.getenv("ANTIGRAVITY_CLIENT_SECRET", ""),
                redirect),
        }

    def get_token(self, provider: str = "openai") -> Optional[str]:
        return self.providers[provider].access_token()

    def authenticate(self, provider: str = "openai"):
        self.providers[provider].authenticate()

    def status(self) -> dict:
        return {name: p.is_authenticated() for name, p in self.providers.items()}

    def best_token(self) -> tuple[str, Optional[str]]:
        """Return (provider_name, token) for the first authenticated provider."""
        for name, p in self.providers.items():
            t = p.access_token()
            if t: return name, t
        return "none", None


oauth = MultiOAuthManager()
