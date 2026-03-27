#!/bin/bash
# KaiNova Ubuntu 24/7 Deploy Script
set -e

echo "🚀 KaiNova Trading Bot — Ubuntu Deploy"

# Install Docker if needed
if ! command -v docker &>/dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

# Clone or pull latest
if [ -d "Binance-alpha-trader-" ]; then
    cd Binance-alpha-trader-
    git pull origin main
else
    git clone https://github.com/Maliot100X/Binance-alpha-trader-.git
    cd Binance-alpha-trader-
fi

# Setup .env if not present
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Edit .env with your credentials before starting!"
    echo "nano .env"
    exit 1
fi

# Clone skills hub if missing
if [ ! -d "binance-skills-hub" ]; then
    git clone --depth=1 https://github.com/binance/binance-skills-hub.git
fi

# Build & start
docker compose pull 2>/dev/null || true
docker compose build --no-cache
docker compose up -d

echo "✅ KaiNova is running 24/7!"
echo "📊 Logs: docker compose logs -f"
echo "📱 Telegram: @KaioNova_Bot — send /status"
