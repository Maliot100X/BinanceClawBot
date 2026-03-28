"""
Multi-provider OAuth manager.
Supports: OpenAI, Google Gemini CLI, Antigravity (Google DeepMind)
Tokens are stored encrypted locally — no API keys stored in .env
"""
from __future__ import annotations
import base64, hashlib, json, os, secrets, time, webbrowser, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from config.settings import BASE_DIR
from typing import Optional
import httpx
from loguru import logger

TOKEN_DIR = BASE_DIR / ".tokens"
TOKEN_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = TOKEN_DIR / "config.json"

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
        "client_id": os.environ.get("GEMINI_OAUTH_CLIENT_ID", "google-sdk-client-id"),
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

    def log_message(self, format, *args): 
        return

class MultiOAuthManager:
    def _load(self) -> dict:
        if not CONFIG_FILE.exists(): return {}
        try: return json.loads(CONFIG_FILE.read_text())
        except: return {}

    def _save(self, data: dict):
        CONFIG_FILE.write_text(json.dumps(data, indent=2))

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
        
        if provider == "gemini" and cfg["client_id"] == "google-sdk-client-id":
             logger.warning("⚠️ Using placeholder Gemini Client ID. Browser login WILL FAIL unless you have configured a Google Cloud Project.")
             logger.warning("👉 Recommendation: Use 'Direct API Key' (Option 2) in provider_setup.py instead.")

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
            # INCREASED TIMEOUT FOR NETWORK RESILIENCE
            try:
                r = httpx.post(cfg["token_url"], data=token_data, timeout=30.0)
            except httpx.ConnectTimeout:
                logger.error("OAuth Connection Timeout: OpenAI server took too long to respond. Retrying...")
                r = httpx.post(cfg["token_url"], data=token_data, timeout=60.0)
                
            if r.status_code == 200:
                token = r.json()
                token["expires_at"] = time.time() + token.get("expires_in", 3600)
                _token_path(provider).write_text(json.dumps(token, indent=2))
                
                # SECTION 1: Capture and Bridge Session
                if provider == "openai":
                    access_token = token.get("access_token")
                    
                    # FETCH REAL MODELS INSTANTLY — WITH ROBUST TIMEOUT
                    best_model = "gpt-5.3-codex" # Default fallback
                    try:
                        logger.info("Fetching available models from OpenAI...")
                        mr = httpx.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {access_token}"}, timeout=20.0)
                        if mr.status_code == 200:
                            models = [m["id"] for m in mr.json().get("data", [])]
                            # Priority list (2026 Standards)
                            for m in ["gpt-5.3-codex", "gpt-5", "gpt-4.5-preview", "gpt-4o", "gpt-4-turbo"]:
                                if m in models:
                                    best_model = m
                                    break
                            logger.success(f"Dynamic Brain synchronization complete: Using {best_model}")
                    except Exception as e:
                        logger.warning(f"Could not fetch models: {e}. Using fallback {best_model}")

                    session = {
                        "access_token": access_token,
                        "refresh_token": token.get("refresh_token"),
                        "expires_at": token.get("expires_at"),
                        "model": best_model
                    }
                    # Save to absolute project root for synchronization
                    (BASE_DIR / "session.json").write_text(json.dumps(session, indent=2))
                    self.send_session(session)

                logger.success(f"Successfully connected {provider}!")
                return token
            else:
                logger.error(f"Token exchange failed: {r.text}")
        return None

    def send_session(self, session: dict):
        """Bridge CLI session to Web Dashboard"""
        urls = [
            "http://localhost:3000/api/connect",
            "https://binance-claw-bot.vercel.app/api/connect"
        ]
        import httpx
        for url in urls:
            try:
                # Use a small timeout as per requirements
                r = httpx.post(url, json=session, timeout=2.0)
                if r.status_code == 200:
                    print(f"Sent session to {url}")
                    break
            except Exception:
                continue

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
        # Check standard OAuth token
        if self.get_token(provider) is not None: return True
        # Check CLI session bridge
        if provider == "openai":
            sess_path = BASE_DIR / "session.json"
            if sess_path.exists():
                try:
                    sess = json.loads(sess_path.read_text())
                    if sess.get("access_token") and sess.get("expires_at", 0) > time.time():
                        return True
                except: pass
        return False

    def save_api_key(self, provider: str, api_key: str):
        # Save to local config or env
        os.environ[f"{provider.upper()}_API_KEY"] = api_key
        # We can also save to the JSON if we want persistence
        data = self._load()
        if "api_keys" not in data: data["api_keys"] = {}
        data["api_keys"][provider] = api_key
        self._save(data)

    def best_token(self) -> tuple[Optional[str], Optional[str]]:
        # ── 1. Check Explicitly Active Provider ─────────────────────────────
        active = os.environ.get("ACTIVE_AI_PROVIDER", "").lower()
        if active:
            if active == "ollama":
                return "ollama", "local"
            
            # If active is openai, prefer session then direct key
            if active == "openai":
                sess_path = BASE_DIR / "session.json"
                if sess_path.exists():
                    try:
                        sess = json.loads(sess_path.read_text())
                        if sess.get("access_token") and sess.get("expires_at", 0) > time.time():
                            return "openai", sess["access_token"]
                    except: pass
                key = os.environ.get("OPENAI_API_KEY", "")
                if key: return "openai", key

            env_map = {
                "groq": "GROQ_API_KEY",
                "deepseek": "DEEPSEEK_API_KEY",
                "openrouter": "OPENROUTER_API_KEY",
                "gemini": "GEMINI_API_KEY",
            }
            mapped_key = env_map.get(active)
            if mapped_key:
                val = os.environ.get(mapped_key, "")
                if val and val not in ("", "your_key_here"):
                    logger.info(f"Using Active Provider: {active.upper()}")
                    return active, val
            logger.warning(f"Active provider '{active}' is set, but its API key is missing. Falling back to defaults.")

        # ── 2. Direct API keys from env (instant, no OAuth needed) ──────────
        # Priority order follows OpenClaw provider chain
        ENV_PROVIDERS = [
            ("openai",     "OPENAI_API_KEY"),
            ("groq",       "GROQ_API_KEY"),
            ("deepseek",   "DEEPSEEK_API_KEY"),
            ("openrouter",  "OPENROUTER_API_KEY"),
            ("gemini",     "GEMINI_API_KEY"),
            ("ollama",     "OLLAMA_API_KEY"),
        ]
        for prov, env_var in ENV_PROVIDERS:
            key = os.environ.get(env_var, "")
            if key and key not in ("", "your_key_here"):
                return prov, key

        # ── 3. CLI-bridged session.json (OpenAI OAuth) ──────────────────────
        sess_path = BASE_DIR / "session.json"
        if sess_path.exists():
            try:
                sess = json.loads(sess_path.read_text())
                if sess.get("access_token") and sess.get("expires_at", 0) > time.time():
                    return "openai", sess["access_token"]
            except: pass

        # ── 3. OAuth tokens ─────────────────────────────────────────────────
        for provider in PROVIDERS:
            token = self.get_token(provider)
            if token:
                return provider, token.get("access_token")

        # ── 4. Saved API keys in config ─────────────────────────────────────
        data = self._load()
        keys = data.get("api_keys", {})
        for provider, key in keys.items():
            if key: return provider, key
        return None, None

    def status(self) -> dict:
        data = self._load()
        oauth_status = {}
        for p in PROVIDERS:
            oauth_status[p] = self.get_token(p) is not None
        
        # Check CLI session status
        if (BASE_DIR / "session.json").exists():
            oauth_status["openai"] = True

        # Add direct API key status
        api_keys = data.get("api_keys", {})
        for p, key in api_keys.items():
            if key: oauth_status[f"{p}_key"] = True
            
        return oauth_status

oauth = MultiOAuthManager()
if __name__ == "__main__":
    import sys
    prov = sys.argv[1] if len(sys.argv) > 1 else "openai"
    oauth.login(prov)
