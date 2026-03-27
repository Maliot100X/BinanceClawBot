import subprocess
import time
import sys
import os
from loguru import logger

def run_command(cmd, cwd=None, name=""):
    logger.info(f"Starting {name}...")
    return subprocess.Popen(cmd, shell=True, cwd=cwd)

def main():
    logger.info("🚀 Starting BinanceClawBot All-in-One Loader")
    
    # 1. API Server
    api_proc = run_command("py -3 api_server.py", name="API Server (FastAPI)")
    
    # 2. Telegram Bot
    bot_proc = run_command("py -3 main.py", name="Telegram Bot")
    
    # 3. Dashboard
    dash_proc = run_command("npm run dev", cwd="dashboard", name="Next.js Dashboard")
    
    logger.success("✅ All systems initialized! Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
            if api_proc.poll() is not None:
                logger.error("API Server stopped unexpectedly!")
                break
            if bot_proc.poll() is not None:
                logger.error("Telegram Bot stopped unexpectedly!")
                break
            if dash_proc.poll() is not None:
                logger.error("Dashboard stopped unexpectedly!")
                break
    except KeyboardInterrupt:
        logger.info("Stopping all systems...")
        api_proc.terminate()
        bot_proc.terminate()
        dash_proc.terminate()
        logger.info("Done.")

if __name__ == "__main__":
    main()
