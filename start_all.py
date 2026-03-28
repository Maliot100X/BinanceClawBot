import subprocess
import time
import sys
import os
import shutil
import socket
import json

def get_python_cmd():
    for cmd in ["py", "python3", "python"]:
        if shutil.which(cmd):
            try:
                subprocess.check_call([cmd, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return cmd
            except:
                continue
    return sys.executable

def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0

def kill_port(port):
    if os.name == 'nt':
        scripts_to_kill = ["main.py", "api_server.py", "codex.py"]
        for script in scripts_to_kill:
            try:
                os.system(f'wmic process where "CommandLine like \'%{script}%\'" call terminate >nul 2>&1')
            except: pass
        try:
            output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
            for line in output.splitlines():
                parts = line.strip().split()
                if len(parts) > 4:
                    pid = parts[-1]
                    if pid and pid != "0":
                        print(f"  🔨 Cleaning ghost process {pid} on port {port}...")
                        os.system(f"taskkill /F /PID {pid} /T >nul 2>&1")
        except: pass
    else:
        os.system(f"fuser -k {port}/tcp > /dev/null 2>&1")

def wait_for_http(url, timeout=30):
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.getcode() == 200:
                    return True
        except Exception as e:
            pass
        time.sleep(1)
    return False

def main():
    print("\n" + "="*60)
    print("🚀 KAINOVA NANO-LAUNCHER — ZERO-FRICTION FLOW")
    print("="*60)
    
    # 0. SECRETS GUARD
    if not os.path.exists(".env"):
        print("❌ CRITICAL: .env file missing in root!")
        return
    
    py = get_python_cmd()

    # 1. PROCESS CLEANUP
    print("\n🧹 STEP 1: Aggressive Process Hardening...")
    for p in [3000, 8000]:
        kill_port(p)
    time.sleep(2)

    # 2. LOGIN / SESSION SYNC
    print("\n🔑 STEP 2: Authenticating AI Brain...")
    # Use our new auth checking approach
    try:
        sys.path.insert(0, os.getcwd())
        from ai.oauth import oauth
        provider, token = oauth.best_token()
        if token:
            print(f"✅ Brain Authenticated: {provider.upper()} Registered")
        else:
            print("❌ CRITICAL: No AI provider configured!")
            ans = input("Would you like to run the setup now? (Y/n): ").strip().upper()
            if ans != "N":
                os.system(f"{py} provider_setup.py")
                # Re-check after setup
                provider, token = oauth.best_token()
                if not token:
                    print("❌ Setup aborted or failed. Exiting.")
                    return
                print(f"✅ Brain Authenticated: {provider.upper()} Registered")
            else:
                print("⚠️ Exiting. Bot requires an AI Brain to run.")
                return
    except Exception as e:
        print(f"⚠️ Auth check failed: {e}")
        return

    # 3. DASHBOARD
    print("\n⏳ STEP 3: Starting Web Dashboard (Next.js)...")
    os.makedirs("logs", exist_ok=True)
    with open("logs/dashboard.log", "w") as f:
        dash_proc = subprocess.Popen("npm run dev", shell=True, cwd="dashboard", stdout=f, stderr=f)
    
    if wait_for_http("http://localhost:3000"):
        print("[OK] Dashboard live at http://localhost:3000")
        # Sync mechanism removed: Next.js API now natively proxies via FastAPI
    else:
        print("❌ Dashboard timeout. Check logs/dashboard.log")
        return

    # 4. API SERVER
    print("\n⏳ STEP 4: Starting API Server (FastAPI)...")
    kill_port(8000) # Double-tap for Windows resilience
    with open("logs/api.log", "w") as f:
        api_proc = subprocess.Popen(f"{py} api_server.py", shell=True, stdout=f, stderr=f)
    
    server_live = False
    for i in range(30):
        if api_proc.poll() is not None:
            break
        if i % 5 == 0: print(f"  ... checking readiness ({i}/30)")
        try:
            with open("logs/api.log", "r", encoding="utf-8", errors="ignore") as logf:
                if "Application startup complete" in logf.read():
                    server_live = True
                    break
        except: pass
        time.sleep(1)

    if server_live:
        print("[OK] API Server live at http://127.0.0.1:8000")
    else:
        print("\n❌ API Server failed to start or crashed.")
        if os.path.exists("logs/api.log"):
            print("📜 LATEST API LOGS:")
            with open("logs/api.log", "r", encoding="utf-8", errors="ignore") as logf:
                lines = logf.readlines()
                for line in lines[-15:]:
                    print(f"  | {line.strip()}")
        print("\n👉 Run 'py api_server.py' manually to see the full error.")
        api_proc.kill()
        return

    # 5. TELEGRAM BOT
    print("\n⏳ STEP 5: Starting Telegram Bot...")
    with open("logs/bot.log", "w") as f:
        bot_proc = subprocess.Popen(f"{py} main.py", shell=True, stdout=f, stderr=f)
    
    time.sleep(5)
    if bot_proc.poll() is not None:
        print("❌ Telegram Bot failed to start!")
        with open("logs/bot.log", "r") as f:
            print(f"LAST LOGS:\n{f.read()[-500:]}")
        return
    
    print("✅ Telegram bot active and monitoring market.")

    # Get real model name dynamically
    active_prov = "Unknown"
    try:
        sys.path.insert(0, os.getcwd())
        from ai.codex_agent import codex_agent
        active_prov = f"{codex_agent.provider}/{codex_agent._model}"
    except:
        try:
            from ai.oauth import oauth
            p, _ = oauth.best_token()
            active_prov = str(p).upper()
        except: pass

    print("\n" + "="*60)
    print("✨ ALL SYSTEMS LIVE & SYNCHRONIZED ✨")
    print("👉 Dashboard: http://localhost:3000")
    print(f"👉 AI Engine: {active_prov}")
    print("👉 Skills: 26 Active")
    print("👉 Logs: check ./logs/ directory")
    print("="*60 + "\n")
    
    try:
        while True:
            time.sleep(10)
            if dash_proc.poll() is not None: break
            if api_proc.poll() is not None: break
            if bot_proc.poll() is not None: break
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down...")
        dash_proc.terminate()
        api_proc.terminate()
        bot_proc.terminate()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ CRITICAL CRASH: {e}")
        import traceback
        traceback.print_exc()
        input("\n[ERROR] Window is held open for diagnosis. Press Enter to close...")
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down...")
