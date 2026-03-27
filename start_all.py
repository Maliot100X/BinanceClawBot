import subprocess
import time
import sys
import os
import shutil
from loguru import logger

def get_python_cmd():
    for cmd in ["py", "python3", "python"]:
        if shutil.which(cmd):
            try:
                subprocess.check_call([cmd, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return cmd
            except:
                continue
    return sys.executable

def check_dependencies(py):
    deps = ["fastapi", "numpy", "pandas", "aiohttp", "python-telegram-bot", "pydantic"]
    missing = []
    for d in deps:
        try:
            # Try to import or check via pip
            subprocess.check_call([py, "-c", f"import {d.replace('-','_')}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            missing.append(d)
    
    if missing:
        logger.warning(f"⚠️ Missing dependencies: {', '.join(missing)}. Attempting auto-install...")
        try:
            subprocess.check_call([py, "-m", "pip", "install"] + missing)
            logger.success("✅ Dependencies installed successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
    return True

def run_command(cmd, cwd=None, name=""):
    logger.info(f"Starting {name}...")
    return subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')

def main():
    logger.info("🚀 KaiNova BinanceClawBot — All-in-One Loader")
    py = get_python_cmd()
    logger.info(f"Using Python: {py}")
    
    if not check_dependencies(py):
        logger.error("Stop. Cannot proceed without dependencies.")
        return

    # 1. API Server
    api_proc = run_command(f"{py} api_server.py", name="API Server (FastAPI)")
    
    # 2. Telegram Bot
    bot_proc = run_command(f"{py} main.py", name="Telegram Bot (KaiNova)")
    
    # 3. Dashboard
    dash_proc = run_command("npm run dev", cwd="dashboard", name="Next.js Dashboard")
    
    logger.success("📊 ALL SYSTEMS LIVE! Access Dashboard at http://localhost:3000")
    
    try:
        while True:
            time.sleep(2)
            if api_proc.poll() is not None:
                logger.error(f"❌ API Server CRASHED: {api_proc.stderr.read()}")
                break
            if bot_proc.poll() is not None:
                logger.error(f"❌ Telegram Bot CRASHED: {bot_proc.stderr.read()}")
                break
            if dash_proc.poll() is not None:
                logger.error("❌ Dashboard CRASHED")
                break
            
    except KeyboardInterrupt:
        logger.info("Stopping all systems...")
        api_proc.terminate()
        bot_proc.terminate()
        dash_proc.terminate()

if __name__ == "__main__":
    main()
