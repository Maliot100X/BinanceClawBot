import subprocess
import time
import sys
import os
import shutil
import socket

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
        return s.connect_ex(('localhost', port)) == 0

def kill_port(port):
    if os.name == 'nt':
        try:
            output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
            for line in output.splitlines():
                if "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    os.system(f"taskkill /F /PID {pid}")
        except: pass
    else:
        os.system(f"fuser -k {port}/tcp > /dev/null 2>&1")

def main():
    print("\n[START] Launching KaiNova BinanceClawBot system...")
    py = get_python_cmd()

    # SECTION 1: INTERACTIVE LOGIN FIRST
    print(f"\n🔑 STEP 1: Authenticating OpenAI Codex...")
    login_cmd = [py, "codex.py", "login", "--provider", "openai"]
    try:
        # This call is interactive and will wait for the browser flow to complete
        subprocess.call(login_cmd)
        print("✅ CLI Login finalized.")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        input("Press Enter to exit...")
        return

    # SECTION 2: CLEAR PORTS
    print("\n🧹 STEP 2: Cleaning up ports...")
    for p in [3000, 8000]:
        if check_port(p):
            kill_port(p)
            time.sleep(1)

    # SECTION 3: START WEB SERVER
    print("\n⏳ STEP 3: Starting Web Dashboard...")
    dash_proc = subprocess.Popen("npm run dev", shell=True, cwd="dashboard", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for dashboard
    retries = 20
    while retries > 0:
        if check_port(3000):
            print("[OK] Backend running on http://localhost:3000")
            break
        time.sleep(1)
        retries -= 1
    
    if retries == 0:
        print("❌ Dashboard failed to start on port 3000.")
        input("Press Enter to exit...")
        return

    # BRIDGE SESSION TO LOCAL DASHBOARD (Crucial for sync)
    if os.path.exists("session.json"):
        import json, httpx
        try:
            with open("session.json", "r") as f:
                sess_data = json.load(f)
                httpx.post("http://localhost:3000/api/connect", json=sess_data, timeout=5)
                print("🔄 Synchronized CLI session with Local Dashboard.")
        except Exception as e:
            print(f"⚠️ Failed to sync session to dashboard: {e}")

    # SECTION 4: START API SERVER
    print("⏳ STEP 4: Starting API Server...")
    api_proc = subprocess.Popen(f"{py} api_server.py", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for API
    retries = 10
    while retries > 0:
        if check_port(8000):
            break
        time.sleep(1)
        retries -= 1
        
    print("[OK] Ready for Codex login (Synchronized)")
    print("\n🚀 ALL SYSTEMS LIVE!")
    print("👉 Dashboard is active at http://localhost:3000")
    
    try:
        while True:
            time.sleep(5)
            if dash_proc.poll() is not None:
                print("❌ Dashboard process stopped.")
                break
            if api_proc.poll() is not None:
                print("❌ API Server stopped.")
                break
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down...")
        dash_proc.terminate()
        api_proc.terminate()

if __name__ == "__main__":
    main()
