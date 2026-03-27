#!/usr/bin/env python3
"""
🚀 BinanceClawBot Professional CLI ('codex')
Provides official-style authentication and bot control.

Usage:
  py codex.py login --device-auth
  py codex.py status
  py codex.py start
  py codex.py stop
"""
import sys
import argparse
from loguru import logger
from oauth_connect import authenticate_pkce, status as get_status
from ai.oauth import oauth

def main():
    parser = argparse.ArgumentParser(description="BinanceClawBot Professional CLI")
    subparsers = parser.add_subparsers(dest="command")

    # login
    login_parser = subparsers.add_parser("login", help="Authenticate with AI providers")
    login_parser.add_argument("--device-auth", action="store_true", help="Use device-style OAuth (opens browser)")
    login_parser.add_argument("--provider", choices=["openai", "gemini", "antigravity", "all"], default="all")

    # status
    subparsers.add_parser("status", help="Check system and OAuth status")

    # bot control
    subparsers.add_parser("start", help="Start the trading bot")
    subparsers.add_parser("stop", help="Stop the trading bot")

    args = parser.parse_args()

    if args.command == "login":
        if args.provider == "all":
            for p in ["openai", "gemini", "antigravity"]:
                print(f"\n🔑 Authenticating {p.upper()}...")
                authenticate_pkce(p)
        else:
            authenticate_pkce(args.provider)
            
    elif args.command == "status":
        s = get_status()
        print("\n📊 BinanceClawBot Status:")
        print(f"{'='*30}")
        for p, info in s.items():
            icon = "✅" if info["connected"] else "❌"
            detail = " (active)" if info["connected"] and not info.get("expired") else " (missing/expired)"
            print(f"  {icon} {p.upper():<12} {detail}")
        print(f"{'='*30}\n")
        
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
