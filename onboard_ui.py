import os
import json
import time
from pathlib import Path

def print_banner():
    print("\n" + "="*60)
    print("🦞 KAINOVA NANO-ONBOARDING — OPENCLAW PRO FLOW")
    print("="*60)

def main():
    print_banner()

    # 1. PROVIDER & MODEL
    print("\n[STEP 1] Model Provider Setup")
    print("Available: openai, anthropic, google, openrouter")
    provider = input("Enter provider [openai]: ") or "openai"
    
    print("\nDynamic Model Selection")
    print("1. gpt-5.3-codex (Professional Agentic)")
    print("2. gpt-4o (Standard)")
    print("3. claude-3-5-sonnet (High-Reasoning)")
    choice = input("Select model [1]: ") or "1"
    model = {
        "1": "openai/gpt-5.3-codex",
        "2": "openai/gpt-4o",
        "3": "anthropic/claude-3-5-sonnet"
    }.get(choice, "openai/gpt-5.3-codex")

    # 2. AUTHENTICATION
    print(f"\n[STEP 2] Authenticating {provider}...")
    if provider == "openai":
        print("Starting OAuth flow...")
        import subprocess
        subprocess.call(["py", "codex.py", "login", "--provider", "openai"])
    else:
        api_key = input(f"Enter {provider} API Key: ")
        # Update .env
        with open(".env", "a") as f:
            f.write(f"\n{provider.upper()}_API_KEY={api_key}\n")

    # 3. BINANCE CONFIG
    print("\n[STEP 3] Binance Pulse Sync")
    binance_key = input("Enter Binance API Key (Enter to skip): ")
    if binance_key:
        binance_secret = input("Enter Binance API Secret: ")
        with open(".env", "a") as f:
            f.write(f"\nBINANCE_API_KEY={binance_key}\n")
            f.write(f"\nBINANCE_SECRET_KEY={binance_secret}\n")

    # 4. TELEGRAM SYNC
    print("\n[STEP 4] Telegram Heartbeat Sync")
    bot_token = input("Enter Telegram Bot Token (Enter to skip): ")
    if bot_token:
        chat_id = input("Enter Telegram Chat ID (Your ID): ")
        with open(".env", "a") as f:
            f.write(f"\nTELEGRAM_BOT_TOKEN={bot_token}\n")
            f.write(f"\nTELEGRAM_CHAT_ID={chat_id}\n")

    # 5. INITIALIZE ECOSYSTEM
    print("\n" + "="*60)
    print("✨ ONBOARDING COMPLETE ✨")
    print(f"👉 Brain:   {model}")
    print(f"👉 Keys:    Synchronized in .env")
    print(f"👉 Launch:  Type 'nano start' or 'py start_all.py'")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
