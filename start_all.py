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
    
    # Port 3000 check
    if check_port(3000):
        print(f"⚠️ Port 3000 in use. Attempting to clear...")
        kill_port(3000)
        time.sleep(1)

    py = get_python_cmd()
    
    # 1. Start Web Server (Next.js Dashboard)
    print("⏳ Starting Web Dashboard...")
    dash_proc = subprocess.Popen("npm run dev", shell=True, cwd="dashboard", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for dashboard
    retries = 15
    while retries > 0:
        if check_port(3000):
            print("[OK] Backend running on http://localhost:3000")
            break
        time.sleep(1)
        retries -= 1
    
    if retries == 0:
        print("❌ Dashboard failed to start on port 3000. Please check 'dashboard' folder and 'npm install'.")
        # Don't exit silently
        input("Press Enter to exit...")
        return

    # 2. Start API Server (FastAPI)
    print("⏳ Starting API Server...")
    api_proc = subprocess.Popen(f"{py} api_server.py", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for API
    retries = 10
    while retries > 0:
        if check_port(8000):
            break
        time.sleep(1)
        retries -= 1
        
    print("[OK] Ready for Codex login")
    print("\n🚀 ACTION REQUIRED:")
    print("👉 Run: py codex.py login --provider openai")
    
    # Keep running
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
