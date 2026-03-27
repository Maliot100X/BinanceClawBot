"""
Central settings — all values read from .env / environment variables.
No secrets are hard-coded.
"""
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Binance ────────────────────────────────────────────
    binance_api_key: str = Field(default="", alias="BINANCE_API_KEY")
    binance_secret_key: str = Field(default="", alias="BINANCE_SECRET_KEY")
    binance_testnet: bool = Field(default=False, alias="BINANCE_TESTNET")

    # ── OpenAI OAuth ───────────────────────────────────────
    openai_oauth_client_id: str = Field(default="", alias="OPENAI_OAUTH_CLIENT_ID")
    openai_oauth_client_secret: str = Field(default="", alias="OPENAI_OAUTH_CLIENT_SECRET")
    openai_redirect_uri: str = Field(default="http://localhost:8080/callback", alias="OPENAI_REDIRECT_URI")
    openai_scopes: str = Field(default="openid profile email", alias="OPENAI_SCOPES")

    # ── Telegram ───────────────────────────────────────────
    telegram_bot_token: str = Field(default="8435117487:AAGOAgK2gJ9OxsGsnQ9bXbwcgSmKvTSIIOI", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="7764037225", alias="TELEGRAM_CHAT_ID")

    # ── Optional data sources ──────────────────────────────
    dexscreener_api: str = Field(default="", alias="DEXSCREENER_API")
    birdeye_api: str = Field(default="", alias="BIRDEYE_API")
    coingecko_api: str = Field(default="", alias="COINGECKO_API")

    # ── Risk settings ──────────────────────────────────────
    max_position_size_pct: float = Field(default=5.0, alias="MAX_POSITION_SIZE_PCT")
    max_daily_loss_pct: float = Field(default=10.0, alias="MAX_DAILY_LOSS_PCT")
    max_leverage: int = Field(default=5, alias="MAX_LEVERAGE")

    # ── Trading ────────────────────────────────────────────
    scan_interval_sec: int = Field(default=30, alias="SCAN_INTERVAL_SEC")
    default_trade_usdt: float = Field(default=100.0, alias="DEFAULT_TRADE_USDT")
    dry_run: bool = Field(default=False, alias="DRY_RUN")

    # ── Dashboard ──────────────────────────────────────────
    dashboard_port: int = Field(default=8080, alias="DASHBOARD_PORT")
    dashboard_host: str = Field(default="0.0.0.0", alias="DASHBOARD_HOST")

    # ── Token storage ──────────────────────────────────────
    token_file: Path = Field(default=BASE_DIR / ".oauth_tokens.json", alias="TOKEN_FILE")


settings = Settings()
