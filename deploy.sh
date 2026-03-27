#!/bin/bash
# BinanceClawBot — Ubuntu 24/7 Deploy Script
# GitHub: https://github.com/Maliot100X/BinanceClawBot
set -e

echo "🤖 BinanceClawBot — Ubuntu Deploy"
echo "=================================================="

# Install Docker if needed
if ! command -v docker &>/dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "✅ Docker installed. Re-run this script."
    exit 0
fi

# Clone or pull latest
REPO_DIR="BinanceClawBot"
if [ -d "$REPO_DIR" ]; then
    echo "Pulling latest code..."
    cd "$REPO_DIR"
    git pull origin main
else
    echo "Cloning BinanceClawBot..."
    git clone https://github.com/Maliot100X/BinanceClawBot.git "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Clone Binance Skills Hub if missing
if [ ! -d "binance-skills-hub" ]; then
    echo "Cloning Binance Skills Hub..."
    git clone --depth=1 https://github.com/binance/binance-skills-hub.git
fi

# Setup .env if not present
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env with your credentials before starting:"
    echo "    nano .env"
    echo ""
    echo "Required:"
    echo "  BINANCE_API_KEY=..."
    echo "  BINANCE_SECRET_KEY=..."
    echo "  TELEGRAM_BOT_TOKEN=..."
    echo "  TELEGRAM_CHAT_ID=..."
    echo ""
    exit 1
fi

# Build & start
echo "Building Docker containers..."
docker compose build --no-cache
docker compose up -d

echo ""
echo "=================================================="
echo "✅ BinanceClawBot is running 24/7!"
echo ""
echo "📊 View logs:    docker compose logs -f"
echo "⏹ Stop bot:     docker compose down"
echo "🔄 Restart:      docker compose restart"
echo ""
echo "📱 Telegram: Open your bot and send /start"
echo "🌐 Web UI:   http://$(curl -s ifconfig.me):3000"
echo "🔌 API:      http://$(curl -s ifconfig.me):8000"
echo "=================================================="
