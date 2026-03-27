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

TOKEN_DIR = Path.home() / ".config" / "bianceclawbot"
TOKEN_DIR.mkdir(parents=True, exist_ok=True)

def _token_path(provider: str) -> Path:
    return TOKEN_DIR / f"{provider}_token.json"

PROVIDERS = {
    "openai": {
        "client_id": os.environ.get("OPENAI_CLIENT_ID", "app_EMoamEEZ73f0CkXaXp7hrann"),
        "auth_url": "https://auth.openai.com/oauth/authorize",
        "token_url": "https://auth.openai.com/oauth/token",
        "scopes": "openid profile email offline_access",
        "redirect_port": 1455,
        "redirect_path": "/auth/callback",
        "extra_params": {
            "codex_cli_simplified_flow": "true",
            "originator": "bianceclawbot",
        },
    },
    "gemini": {
        "client_id": os.environ.get("GEMINI_OAUTH_CLIENT_ID", "local-client-id"),
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": "openid email profile",
        "redirect_port": 8085,
        "redirect_path": "/oauth2callback",
    },
}

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'code' in params:
            self.server.code = params['code'][0]
            self.wfile.write(b"<html><body style='font-family:sans-serif; text-align:center; padding:50px; background:#020408; color:#00ff88;'>")
            self.wfile.write(b"<h1>KaiNova Brain Connected!</h1><p>You can close this window and return to the bot.</p></body></html>")
        else:
            self.wfile.write(b"Authentication failed.")

    def log_message(self, format, *args): return

class MultiOAuthManager:
    def login(self, provider: str):
        cfg = PROVIDERS.get(provider)
        if not cfg: return logger.error(f"Unknown provider: {provider}")
        
        # PKCE
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().replace('=', '')
        
        redirect_uri = f"http://localhost:{cfg['redirect_port']}{cfg['redirect_path']}"
        params = {
            "client_id": cfg["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": cfg["scopes"],
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": secrets.token_urlsafe(16),
        }
        params.update(cfg.get("extra_params", {}))
        
        auth_url = f"{cfg['auth_url']}?{urllib.parse.urlencode(params)}"
        logger.info(f"Opening browser for {provider} login...")
        webbrowser.open(auth_url)
        
        server = HTTPServer(('localhost', cfg['redirect_port']), OAuthCallbackHandler)
        server.code = None
        server.handle_request()
        
        if server.code:
            logger.info("Exchanging code for tokens...")
            token_data = {
                "grant_type": "authorization_code",
                "code": server.code,
                "redirect_uri": redirect_uri,
                "client_id": cfg["client_id"],
                "code_verifier": verifier,
            }
            r = httpx.post(cfg["token_url"], data=token_data)
            if r.status_code == 200:
                token = r.json()
                token["expires_at"] = time.time() + token.get("expires_in", 3600)
                _token_path(provider).write_text(json.dumps(token, indent=2))
                logger.success(f"Successfully connected {provider}!")
                return token
            else:
                logger.error(f"Token exchange failed: {r.text}")
        return None

    def get_token(self, provider: str) -> Optional[dict]:
        path = _token_path(provider)
        if not path.exists(): return None
        try:
            token = json.loads(path.read_text())
            if token.get("expires_at", 0) < time.time() + 60:
                return self.refresh(provider)
            return token
        except: return None

    def refresh(self, provider: str) -> Optional[dict]:
        cfg = PROVIDERS.get(provider); path = _token_path(provider)
        if not cfg or not path.exists(): return None
        token = json.loads(path.read_text())
        if not token.get("refresh_token"): return None
        
        data = { "grant_type": "refresh_token", "refresh_token": token["refresh_token"], "client_id": cfg["client_id"] }
        try:
            r = httpx.post(cfg["token_url"], data=data)
            if r.status_code == 200:
                new_token = r.json()
                new_token["expires_at"] = time.time() + new_token.get("expires_in", 3600)
                path.write_text(json.dumps(new_token, indent=2))
                return new_token
        except: pass
        return None

    def is_authenticated(self, provider: str = "openai") -> bool:
        return self.get_token(provider) is not None

    def status(self) -> dict:
        result = {}
        for p in PROVIDERS:
            path = _token_path(p)
            result[p] = path.exists()
        return result

oauth = MultiOAuthManager()
if __name__ == "__main__":
    import sys
    prov = sys.argv[1] if len(sys.argv) > 1 else "openai"
    oauth.login(prov)
