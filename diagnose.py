import sys
import os
import json
from pathlib import Path
from loguru import logger

# Add root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

def diagnose():
    print("\n" + "="*50)
    print("🧠 KAINOVA SYSTEM DIAGNOSTICS")
    print("="*50)

    # 1. Environment Check
    print(f"\n📁 ROOT DIRECTORY: {BASE_DIR}")
    env_path = BASE_DIR / ".env"
    print(f"📄 .env exists: {'✅' if env_path.exists() else '❌'}")
    
    # 2. Configuration Loading
    try:
        from config.settings import settings
        print(f"⚙️ Binance API Key: {'✅ Loaded (***' + settings.binance_api_key[-4:] + ')' if settings.binance_api_key else '❌ Missing'}")
        print(f"⚙️ Binance Secret: {'✅ Loaded' if settings.binance_secret_key else '❌ Missing'}")
        print(f"⚙️ OpenAI Client: {'✅ Loaded' if settings.openai_oauth_client_id else '❌ Missing'}")
    except Exception as e:
        print(f"❌ Settings Load Error: {e}")

    # 3. Session / Tokens
    sess_path = BASE_DIR / "session.json"
    print(f"🔑 CLI Session (session.json): {'✅ Active' if sess_path.exists() else '❌ Not Found'}")
    
    token_dir = BASE_DIR / ".tokens"
    print(f"📁 Token Storage (.tokens): {'✅ Exists' if token_dir.exists() else '❌ Not Found'}")

    # 4. Imports Check (FastAPI, etc)
    print("\n📦 DEPENDENCY CHECK:")
    libs = ["fastapi", "uvicorn", "httpx", "aiohttp", "pydantic_settings", "dotenv", "loguru"]
    for lib in libs:
        try:
            __import__(lib)
            print(f"  - {lib}: ✅ Installed")
        except ImportError:
            print(f"  - {lib}: ❌ MISSING")

    # 5. Core Files Verification
    print("\n📄 CORE FILES:")
    files = ["api_server.py", "main.py", "start_all.py", "ai/oauth.py", "ai/codex_agent.py"]
    for f in files:
        p = BASE_DIR / f
        print(f"  - {f}: {'✅' if p.exists() else '❌'}")

    print("\n" + "="*50)
    print("🚀 Status: " + ("Ready to trade" if env_path.exists() and sess_path.exists() else "Needs configuration"))
    print("="*50 + "\n")

if __name__ == "__main__":
    diagnose()
