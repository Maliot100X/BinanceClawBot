#!/usr/bin/env python3
"""
🔧 KaiNova Provider Setup — CMD Dashboard
Real provider selection, API key entry, and connection testing.

Usage:
  py provider_setup.py            # Interactive setup
  py provider_setup.py status     # Show current provider status
  py provider_setup.py test       # Test current AI connection
"""
import os, sys, json, time
import httpx
from pathlib import Path
from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH, override=True)

# ── Provider Registry ─────────────────────────────────────────────────────────
PROVIDERS = {
    "1": {
        "id": "openai",
        "name": "OpenAI (OAuth / API Key)",
        "env_var": "OPENAI_API_KEY",
    },
    "2": {
        "id": "groq",
        "name": "Groq (FREE)",
        "env_var": "GROQ_API_KEY",
    },
    "3": {
        "id": "deepseek",
        "name": "DeepSeek",
        "env_var": "DEEPSEEK_API_KEY",
    },
    "4": {
        "id": "openrouter",
        "name": "OpenRouter",
        "env_var": "OPENROUTER_API_KEY",
    },
    "5": {
        "id": "gemini",
        "name": "Google Gemini",
        "env_var": "GEMINI_API_KEY",
    },
    "6": {
        "id": "ollama",
        "name": "Ollama (Local / Cloud)",
        "env_var": "OLLAMA_URL",
        "default": "http://localhost:11434",
    },
    "7": {
        "id": "antigravity",
        "name": "Google Antigravity (OAuth)",
        "env_var": "ANTIGRAVITY_TOKEN",
        "oauth_only": True,
    },
    "8": {
        "id": "nvidia",
        "name": "NVIDIA Build (FREE Cloud)",
        "env_var": "NVIDIA_API_KEY",
    },
}

# ── NVIDIA Build Free Model Catalog ──────────────────────────────────────────
NVIDIA_MODELS = [
    "deepseek-ai/deepseek-v3.1",
    "deepseek-ai/deepseek-v3.2",
    "minimaxai/minimax-m2.5",
    "z-ai/glm5",
    "moonshotai/kimi-k2.5",
]
NVIDIA_DEFAULT_MODEL = "deepseek-ai/deepseek-v3.1"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


def banner():
    print("\n" + "="*60)
    print("  🤖  KaiNova AI Provider Setup — Real Connections")
    print("="*60)

def show_status():
    """Show which providers are configured and the active one."""
    print("\n📊 Current Provider Status:")
    print("-" * 50)
    
    active = os.environ.get("ACTIVE_AI_PROVIDER", "").lower()
    if active:
        print(f"  🌟 ACTIVE PROVIDER: {active.upper()}")
    else:
        print(f"  ⚠️  ACTIVE PROVIDER: Auto-detect (First available)")
    print("-" * 50)

    # Check OAuth
    sess_path = BASE_DIR / "session.json"
    if sess_path.exists():
        try:
            sess = json.loads(sess_path.read_text())
            if sess.get("access_token") and sess.get("expires_at", 0) > time.time():
                print(f"  ✅ OpenAI OAuth   — CONNECTED (expires in {int((sess['expires_at'] - time.time()) / 3600)}h)")
            else:
                print(f"  ❌ OpenAI OAuth   — NOT CONNECTED")
        except:
             print(f"  ❌ OpenAI OAuth   — CORRUPT")
    else:
        print(f"  ❌ OpenAI OAuth   — NOT CONNECTED")
    
    # Check API keys
    for key, p in PROVIDERS.items():
        if p["id"] == "ollama":
            url = os.environ.get(p["env_var"], p["default"])
            print(f"  OK {p['name']:<22} -- {url}")
            continue
        
        # Antigravity uses OAuth tokens, not API keys
        if p["id"] == "antigravity":
            ag_token_path = BASE_DIR / ".tokens" / "antigravity_token.json"
            if ag_token_path.exists():
                try:
                    ag_data = json.loads(ag_token_path.read_text())
                    if ag_data.get("access_token") and ag_data.get("expires_at", 0) > time.time():
                        proj = ag_data.get("project_id", "unknown")
                        print(f"  OK {p['name']:<22} -- CONNECTED (Project: {proj})")
                    else:
                        print(f"  -- {p['name']:<22} -- TOKEN EXPIRED")
                except:
                    print(f"  -- {p['name']:<22} -- CORRUPT TOKEN")
            else:
                print(f"  -- {p['name']:<22} -- NOT CONNECTED")
            continue

        val = os.environ.get(p["env_var"], "")
        if val and val not in ("", "your_key_here"):
            masked = val[:8] + "..." + val[-4:]
            print(f"  OK {p['name']:<22} -- {masked}")
        else:
            print(f"  -- {p['name']:<22} -- NOT SET")
    
    print("-" * 50)

def test_provider():
    """Test the current active AI connection."""
    print("\n🧪 Testing Active AI Connection...")
    
    sys.path.insert(0, str(BASE_DIR))
    from ai.oauth import oauth
    provider, token = oauth.best_token()
    
    if not token:
        # For antigravity, also try loading token directly
        active_prov = os.environ.get("ACTIVE_AI_PROVIDER", "").lower()
        if active_prov == "antigravity":
            ag_path = BASE_DIR / ".tokens" / "antigravity_token.json"
            if ag_path.exists():
                try:
                    ag_data = json.loads(ag_path.read_text())
                    token = ag_data.get("access_token")
                    provider = "antigravity"
                except: pass
        if not token:
            print("  No AI provider configured or selected. Run setup.")
            return False
    
    print(f"  Active Provider: {provider.upper()}")
    if provider != "ollama":
        print(f"  Token: {token[:12]}...{token[-6:]}")
    
    if provider == "openai":
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Say hello"}], "max_tokens": 10}
    elif provider == "groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        # 70b-versatile is the current standard and less likely to be blocked than the instant/preview models
        payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "Say hello"}], "max_tokens": 10}
    elif provider == "deepseek":
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": "Say hello"}], "max_tokens": 10}
    elif provider == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={token}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": "Say hello in one word"}]}]}
    elif provider == "ollama":
        ollama_base = os.environ.get("OLLAMA_URL", "http://localhost:11434")
        
        # Determine the first available model to test
        test_model = "minimax-m2:cloud"
        try:
            r_tags = httpx.get(f"{ollama_base}/api/tags", headers={"Authorization": f"Bearer {token}"} if token and token != "local" else {}, timeout=5.0)
            if r_tags.status_code == 200:
                tags = r_tags.json().get("models", [])
                if tags:
                    test_model = tags[0]["name"]
        except: pass

        url = f"{ollama_base}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if token and token != "local":
            headers["Authorization"] = f"Bearer {token}"
            
        payload = {"model": test_model, "messages": [{"role": "user", "content": "Say hello"}], "max_tokens": 10}
    elif provider == "antigravity":
        # Antigravity OAuth uses Bearer token with standard Gemini API
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "contents": [{"parts": [{"text": "Reply with only: hello"}]}]
        }
    elif provider == "nvidia":
        url = f"{NVIDIA_BASE_URL}/chat/completions"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"model": NVIDIA_DEFAULT_MODEL, "messages": [{"role": "user", "content": "Say hello"}], "max_tokens": 10}
    else:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "HTTP-Referer": "https://github.com/Maliot100X/BinanceClawBot"}
        payload = {"model": "google/gemini-2.5-flash", "messages": [{"role": "user", "content": "Say hello"}], "max_tokens": 10}
    
    try:
        r = httpx.post(url, headers=headers, json=payload, timeout=20.0)
        if r.status_code == 200:
            resp = r.json()
            if provider in ("gemini", "antigravity"):
                text = resp["candidates"][0]["content"]["parts"][0]["text"]
            else:
                text = resp["choices"][0]["message"]["content"]
            print(f"  ✅ WORKING! AI says: {text.strip()}")
            return True
        else:
            print(f"  ❌ Error {r.status_code}: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return False

def setup_provider():
    """Interactive provider setup."""
    banner()
    show_status()
    
    print("\n🔧 Setup Menu:\n")
    for key, prov in PROVIDERS.items():
        print(f"  [{key}] Configure {prov['name']}")
    print(f"\n  [A] Set ACTIVE Provider (Crucial!)")
    print(f"  [T] Test current active connection")
    print(f"  [S] Show status")
    print(f"  [C] Clean / Reset All Models")
    print(f"  [Q] Quit\n")
    
    choice = input("  Choice: ").strip().upper()
    
    if choice == "Q":
        return
    elif choice == "T":
        test_provider()
        return
    elif choice == "S":
        show_status()
        return
    elif choice == "A":
        set_active_provider()
        return
    elif choice == "C":
        reset_all_models()
        return
    elif choice not in PROVIDERS:
        print("❌ Invalid choice")
        return
    
    prov = PROVIDERS[choice]
    
    if prov["id"] == "openai":
        print("\n🔑 OpenAI Setup")
        print("  [1] Browser OAuth (Free ChatGPT account)")
        print("  [2] Direct API Key (Paid API)")
        sub = input("  Choice: ").strip()
        if sub == "1":
            sys.path.insert(0, str(BASE_DIR))
            from ai.oauth import oauth
            oauth.login("openai")
            set_active("openai")
            return
        elif sub == "2":
            pass
        else:
            return

    if prov["id"] == "antigravity":
        print("\n[AG] Google Antigravity Setup (OAuth)")
        print("  This will open Google login in your browser.")
        print("  You'll get access to: Gemini 3 Pro, Claude Opus 4.6, etc.")
        print("")
        print("  \u26a0\ufe0f  WARNING: Using Antigravity OAuth may violate Google ToS.")
        print("  Your Google account could be banned. Proceed at your own risk.")
        print("")
        proceed = input("  Continue? (Y/n): ").strip().upper()
        if proceed == "N":
            print("  Skipped.")
            return
        
        sys.path.insert(0, str(BASE_DIR))
        from ai.oauth import oauth
        oauth.login("antigravity")
        set_active("antigravity")
        return

    if prov.get("oauth_only"):
        print(f"\n\u26a0\ufe0f {prov['name']} requires Browser OAuth login.")
        return

    if prov["id"] == "gemini":
        print("\n🔑 Google Gemini Setup")
        print("  [1] Browser Google Cloud SDK (OAuth)")
        print("  [2] Direct API Key")
        sub = input("  Choice: ").strip()
        if sub == "1":
            sys.path.insert(0, str(BASE_DIR))
            from ai.oauth import oauth
            oauth.login("gemini")
            set_active("gemini")
            return
        elif sub == "2":
            pass
        else:
            return

    env_var = prov["env_var"]
    print(f"\n🔑 Configure {prov['name']}")
    
    current = os.environ.get(env_var, "")
    if current and current not in ("", "your_key_here"):
        print(f"  Current value: {current}")
    
    if prov["id"] == "ollama":
        url = input(f"  Enter Ollama URL (default: http://localhost:11434): ").strip()
        if not url: url = "http://localhost:11434"
        set_key(str(ENV_PATH), "OLLAMA_URL", url)
        os.environ["OLLAMA_URL"] = url
        print(f"  ✅ OLLAMA_URL saved to .env")

        # FIX: Restore API Key prompt for Ollama Cloud
        api_key_current = os.environ.get("OLLAMA_API_KEY", "")
        if api_key_current:
            print(f"  Current API Key: {api_key_current[:8]}...{api_key_current[-4:]}")
        
        api_key = input(f"  Enter Ollama API Key (optional, for Cloud models): ").strip()
        if api_key:
            set_key(str(ENV_PATH), "OLLAMA_API_KEY", api_key)
            os.environ["OLLAMA_API_KEY"] = api_key
            print(f"  ✅ OLLAMA_API_KEY saved to .env")
        
        print("\n📥 Model Management")
        print("  [1] List installed models")
        print("  [2] Pull new model (e.g. deepseek-v3:cloud)")
        print("  [3] Skip")
        m_choice = input("  Choice: ").strip()
        
        if m_choice == "1":
            try:
                r = httpx.get(f"{url}/api/tags", timeout=5.0)
                models = [m["name"] for m in r.json().get("models", [])]
                print(f"  Available: {', '.join(models)}")
            except: print("  ❌ Could not list models.")
        elif m_choice == "2":
            m_name = input("  Enter model name (e.g. llama3.2): ").strip()
            if m_name:
                print(f"  🚀 Starting pull for {m_name}... (this may take minutes)")
                sys.path.insert(0, str(BASE_DIR))
                from ai.codex_agent import codex_agent
                import asyncio
                success = asyncio.run(codex_agent.pull_model(m_name))
                if success: print(f"  ✅ Successfully pulled {m_name}")
                else: print(f"  ❌ Pull failed.")

        set_active(prov["id"])
        return
    else:
        key = input(f"  Enter your {prov['name']} API key: ").strip()
    
    if not key:
        print("  Skipped.")
        return
    
    # Save to .env file
    set_key(str(ENV_PATH), env_var, key)
    os.environ[env_var] = key
    print(f"\n  ✅ {env_var} saved to .env")
    
    set_active(prov["id"])

def set_active(prov_id):
    ans = input(f"\n  Use {prov_id.upper()} as the active AI? (Y/n): ").strip().upper()
    if ans != "N":
        set_key(str(ENV_PATH), "ACTIVE_AI_PROVIDER", prov_id)
        os.environ["ACTIVE_AI_PROVIDER"] = prov_id
        print(f"  🌟 ACTIVE_AI_PROVIDER set to {prov_id.upper()}")
        test_provider()

def reset_all_models():
    print("\n🧹 Cleaning / Resetting All Models...")
    
    # 1. Delete session.json
    sess_path = BASE_DIR / "session.json"
    if sess_path.exists():
        try:
            sess_path.unlink()
            print("  ✅ Deleted session.json (OAuth session removed)")
        except:
            print("  ❌ Could not delete session.json")
    
    # 2. Clear out AI keys from .env
    keys_to_clear = [
        "ACTIVE_AI_PROVIDER", "OPENAI_API_KEY", "GROQ_API_KEY", 
        "DEEPSEEK_API_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY",
        "OLLAMA_URL", "OLLAMA_API_KEY", "ANTIGRAVITY_TOKEN",
        "NVIDIA_API_KEY"
    ]
    
    for k in keys_to_clear:
        if k in os.environ:
            set_key(str(ENV_PATH), k, "")
            os.environ[k] = ""
            
    print("  ✅ All API keys and Active Provider flags cleared from .env")
    print("\n✨ Reset complete! You can now start fresh.")
    show_status()

def set_active_provider():
    print("\n🌟 Set Active Provider")
    print("  Which AI should the bot use natively?")
    opts = [p["id"] for p in PROVIDERS.values()]
    for i, p in enumerate(opts, 1):
        print(f"  [{i}] {p.upper()}")
    
    c = input("\n  Choice: ").strip()
    try:
        idx = int(c) - 1
        if 0 <= idx < len(opts):
            set_active(opts[idx])
        else:
            print("❌ Invalid selection")
    except:
        pass

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "status":
            banner()
            show_status()
        elif cmd == "test":
            banner()
            test_provider()
        else:
            setup_provider()
    else:
        setup_provider()

if __name__ == "__main__":
    main()
