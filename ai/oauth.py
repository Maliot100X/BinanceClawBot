"""
Multi-provider OAuth manager.
Supports: OpenAI, Google Gemini CLI, Antigravity (Google DeepMind)
Tokens are stored encrypted locally — no API keys stored in .env
"""
from __future__ import annotations
import base64, hashlib, json, os, secrets, time, webbrowser, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional
import httpx
from loguru import logger

# ── Token Storage (Mirrors oauth_connect.py) ──────────────────────────────────
TOKEN_DIR = Path.home() / ".config" / "bianceclawbot"
TOKEN_DIR.mkdir(parents=True, exist_ok=True)

def _token_path(provider: str) -> Path:
    return TOKEN_DIR / f"{provider}_token.json"

# ── Provider Config ──────────────────────────────────────────────────────────
PROVIDERS = {
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
    "gemini": {
        "client_id": os.environ.get("GEMINI_OAUTH_CLIENT_ID", ""),
        "client_secret": os.environ.get("GEMINI_OAUTH_CLIENT_SECRET", ""),
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": "openid email profile https://www.googleapis.com/auth/generative-language",
        "redirect_port": 8085,
        "redirect_path": "/oauth2callback",
        "extra_params": { "access_type": "offline", "prompt": "consent" },
    },
    "antigravity": {
        "client_id": os.environ.get("ANTIGRAVITY_OAUTH_CLIENT_ID", os.environ.get("GEMINI_OAUTH_CLIENT_ID", "")),
        "client_secret": os.environ.get("ANTIGRAVITY_OAUTH_CLIENT_SECRET", os.environ.get("GEMINI_OAUTH_CLIENT_SECRET", "")),
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": "openid email profile https://www.googleapis.com/auth/cloud-platform",
        "redirect_port": 8086,
        "redirect_path": "/oauth2callback",
        "extra_params": { "access_type": "offline", "prompt": "consent" },
    },
}

class MultiOAuthManager:
    """Manages OpenAI + Gemini + Antigravity OAuth tokens for the bot brain."""
    
    def get_token(self, provider: str) -> Optional[dict]:
        path = _token_path(provider)
        if not path.exists(): return None
        try:
            token = json.loads(path.read_text())
            # Refresh if expired
            if token.get("expires_at", 0) < time.time() + 60:
                return self.refresh(provider)
            return token
        except Exception: return None

    def refresh(self, provider: str) -> Optional[dict]:
        cfg = PROVIDERS.get(provider)
        path = _token_path(provider)
        if not cfg or not path.exists(): return None
        token = json.loads(path.read_text())
        if not token.get("refresh_token"): return None
        
        logger.info(f"Refreshing {provider} token...")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": token["refresh_token"],
            "client_id": cfg["client_id"],
        }
        if cfg.get("client_secret"):
            data["client_secret"] = cfg["client_secret"]
            
        try:
            r = httpx.post(cfg["token_url"], data=data)
            r.raise_for_status()
            new_token = r.json()
            new_token["expires_at"] = time.time() + new_token.get("expires_in", 3600)
            new_token["refresh_token"] = token["refresh_token"] # Keep existing refresh
            path.write_text(json.dumps(new_token, indent=2))
            return new_token
        except Exception as e:
            logger.error(f"Refresh failed for {provider}: {e}")
            return None

    def status(self) -> dict:
        result = {}
        for p in PROVIDERS:
            path = _token_path(p)
            result[p] = path.exists()
        return result

    def best_token(self) -> tuple[str, Optional[str]]:
        """Return (provider_name, token_string) for the first available provider."""
        for p in PROVIDERS:
            token = self.get_token(p)
            if token: return p, token.get("access_token")
        return "none", None

oauth = MultiOAuthManager()

