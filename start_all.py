import subprocess
import time
import sys
import os
import shutil
from loguru import logger

def get_python_cmd():
    """Detect the correct python command for the current environment."""
    for cmd in ["py", "python3", "python"]:
        if shutil.which(cmd):
            # Verify it's actually working
            try:
                subprocess.check_call([cmd, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return cmd
            except:
                continue
    return "python"

def run_command(cmd, cwd=None, name=""):
    logger.info(f"Starting {name}...")
    # Use shell=True for npm, but handle python explicitly if needed
    return subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def monitor_output(proc, name):
    """Print the first few lines of output to verify startup."""
    line = proc.stdout.readline()
    if line:
        logger.debug(f"[{name}] {line.strip()}")

def main():
    logger.info("🚀 Starting BinanceClawBot All-in-One Loader")
    py = get_python_cmd()
    logger.info(f"Using Python command: {py}")
    
    # 1. API Server
    api_proc = run_command(f"{py} api_server.py", name="API Server (FastAPI)")
    
    # 2. Telegram Bot
    bot_proc = run_command(f"{py} main.py", name="Telegram Bot")
    
    # 3. Dashboard
    dash_proc = run_command("npm run dev", cwd="dashboard", name="Next.js Dashboard")
    
    logger.success("✅ All systems initialized! Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(2)
            # Check for immediate crashes
            if api_proc.poll() is not None:
                err = api_proc.stderr.read()
                logger.error(f"API Server stopped! Error: {err}")
                break
            if bot_proc.poll() is not None:
                err = bot_proc.stderr.read()
                logger.error(f"Telegram Bot stopped! Error: {err}")
                break
            if dash_proc.poll() is not None:
                logger.error("Dashboard stopped unexpectedly!")
                break
            
            # Briefly show what they are doing
            monitor_output(api_proc, "API")
            monitor_output(bot_proc, "BOT")
            
    except KeyboardInterrupt:
        logger.info("Stopping all systems...")
        api_proc.terminate()
        bot_proc.terminate()
        dash_proc.terminate()
        logger.info("Done.")

if __name__ == "__main__":
    main()
