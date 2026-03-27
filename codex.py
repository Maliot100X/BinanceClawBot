#!/usr/bin/env python3
"""
🚀 KaiNova BinanceClawBot Professional CLI ('codex')
Provides official-style PKCE authentication and bot control.

Usage:
  py codex.py login --device-auth
  py codex.py status
  py codex.py start
  py codex.py stop
"""
import sys
import argparse
from loguru import logger
from ai.oauth import oauth

def main():
    parser = argparse.ArgumentParser(description="KaiNova BinanceClawBot Professional CLI")
    subparsers = parser.add_subparsers(dest="command")

    # login
    login_parser = subparsers.add_parser("login", help="Authenticate with AI providers")
    login_parser.add_argument("--device-auth", action="store_true", help="Use device-style OAuth (opens browser)")
    login_parser.add_argument("--provider", choices=["openai", "gemini", "antigravity"], default="openai")

    # status
    subparsers.add_parser("status", help="Check system and OAuth status")

    # bot control
    subparsers.add_parser("start", help="Start the trading bot")
    subparsers.add_parser("stop", help="Stop the trading bot")

    args = parser.parse_args()

    if args.command == "login":
        print(f"\n🔑 Initiating KaiNova {args.provider.upper()} Connect...")
        oauth.login(args.provider)
            
    elif args.command == "status":
        s = oauth.status()
        print("\n📊 KaiNova System Status:")
        print(f"{'='*40}")
        for p, connected in s.items():
            icon = "✅" if connected else "❌"
            status = "CONNECTED" if connected else "DISCONNECTED"
            print(f"  {icon} {p.upper():<12} {status}")
        print(f"{'='*40}\n")
        
    elif args.command in ["start", "stop"]:
        import httpx
        try:
            r = httpx.post(f"http://localhost:8000/bot/{args.command}")
            if r.status_code == 200:
                logger.success(f"Bot {args.command}ed successfully")
            else:
                logger.error(f"Failed to {args.command} bot: {r.text}")
        except Exception as e:
            logger.error(f"Is api_server.py running? Error: {e}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
