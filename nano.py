import os
import json
import socket
import time
from pathlib import Path
import httpx

def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('localhost', port)) == 0

def get_session():
    p = Path("session.json")
    if p.exists():
        try:
            return json.loads(p.read_text())
        except: return None
    return None

def main():
    print("\n" + "="*60)
    print("🛰️  KAINOVA NANO-STATUS — ECOSYSTEM DIAGNOSTIC")
    print("="*60)

    # 1. CORE BRAIN
    sess = get_session()
    if sess:
        model = sess.get("model", "gpt-5.3-codex")
        print(f"🧠 AI BRAIN:  🟢 CONNECTED ({model})")
    else:
        print(f"🧠 AI BRAIN:  🔴 OFFLINE (No session.json)")

    # 2. BINANCE
    env_exists = os.path.exists(".env")
    if env_exists:
        with open(".env", "r") as f:
            env_data = f.read()
            has_key = "BINANCE_API_KEY=" in env_data
            has_sec = "BINANCE_SECRET_KEY=" in env_data
        if has_key and has_sec:
            print(f"💳 BINANCE:   🟢 SECRETS LOADED")
        else:
            print(f"💳 BINANCE:   ⚠️ SECRETS MISSING FROM .env")
    else:
        print(f"💳 BINANCE:   🔴 .env FILE NOT FOUND")

    # 3. INFRASTRUCTURE
    dash_live = check_port(3000)
    api_live = check_port(8000)
    print(f"🌐 DASHBOARD: {'🟢 LIVE' if dash_live else '🔴 DOWN'} (Port 3000)")
    print(f"🔌 API BACKEND: {'🟢 LIVE' if api_live else '🔴 DOWN'} (Port 8000)")

    # 4. TELEGRAM HEARTBEAT
    bot_alive = False
    if api_live:
        try:
            r = httpx.get("http://localhost:8000/api/status", timeout=2)
            if r.status_code == 200:
                status = r.json()
                bot_alive = status.get("bot_active", False)
        except: pass
    print(f"🤖 TELEGRAM:  {'🟢 ACTIVE' if bot_alive else '🔴 UNKNOWN/PAUSED'}")

    # 5. LOG INTEGRITY
    log_dir = Path("logs")
    if log_dir.exists():
        count = len(list(log_dir.glob("*.log")))
        print(f"📝 LOG FILES:  ✅ {count} Active Streams")
    else:
        print(f"📝 LOG FILES:  ⚠️ Directory missing, run 'py start_all.py' first.")

    print("="*60)
    print("👉 To restart everything: py start_all.py")
    print("👉 To see EVERYTHING in a full report: py KAINOVA_NANO.py")
    print("="*60 + "\n")
    
    # Auto-trigger full report for the user's convenience
    if os.path.exists("KAINOVA_NANO.py"):
        import subprocess
        subprocess.run([sys.executable, "KAINOVA_NANO.py"])

if __name__ == "__main__":
    import sys
    main()
