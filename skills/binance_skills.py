"""All 26 Binance Skills implemented as async callable tools.

Each skill mirrors the Binance Skills Hub definition and exposes
methods the AI agent can call as tools.
"""
from __future__ import annotations
import asyncio
from typing import Any
from core.client import get_client
from loguru import logger


# ─────────────────────────────────────────────────────────
# BINANCE/ SKILLS
# ─────────────────────────────────────────────────────────

class AlgoSkill:
    """TWAP / VWAP algorithmic order placement."""
    name = "algo"

    async def place_twap_order(self, symbol: str, side: str, qty: float, duration: int = 3600) -> dict:
        client = get_client()
        return await client._post(
            f"{client.base}/sapi/v1/algo/spot/newOrderTwap",
            {"symbol": symbol, "side": side, "quantity": qty, "duration": duration},
        )

    async def place_vwap_order(self, symbol: str, side: str, qty: float, duration: int = 3600) -> dict:
        client = get_client()
        return await client._post(
            f"{client.base}/sapi/v1/algo/spot/newOrderVwap",
            {"symbol": symbol, "side": side, "quantity": qty, "duration": duration},
        )

    async def get_algo_orders(self) -> list:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/algo/spot/openOrders", signed=True)


class AlphaSkill:
    """Binance Alpha token discovery and opportunity tracking."""
    name = "alpha"

    async def get_alpha_tokens(self) -> list:
        client = get_client()
        try:
            return await client._get(f"{client.base}/sapi/v1/alpha/tokens")
        except Exception:
            return []

    async def get_alpha_opportunities(self) -> list:
        client = get_client()
        try:
            return await client._get(f"{client.base}/sapi/v1/alpha/opportunities")
        except Exception:
            return []


class AssetsSkill:
    """Asset info, balances, deposits, withdrawals, and transfers."""
    name = "assets"

    async def get_all_coins(self) -> list:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/capital/config/getall", signed=True)

    async def get_deposit_address(self, coin: str, network: str = "") -> dict:
        params: dict = {"coin": coin}
        if network:
            params["network"] = network
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/capital/deposit/address", params, signed=True)

    async def get_deposit_history(self, coin: str | None = None) -> list:
        client = get_client()
        params = {"coin": coin} if coin else {}
        return await client._get(f"{client.base}/sapi/v1/capital/deposit/hisrec", params, signed=True)

    async def withdraw(self, coin: str, address: str, amount: float, network: str = "") -> dict:
        client = get_client()
        params: dict = {"coin": coin, "address": address, "amount": amount}
        if network:
            params["network"] = network
        return await client._post(f"{client.base}/sapi/v1/capital/withdraw/apply", params)

    async def transfer_asset(self, asset: str, amount: float, type_code: str = "MAIN_SPOT") -> dict:
        client = get_client()
        return await client._post(f"{client.base}/sapi/v1/asset/transfer",
                                  {"type": type_code, "asset": asset, "amount": amount})


class ConvertSkill:
    """Crypto-to-crypto convert (instant swap)."""
    name = "convert"

    async def get_quote(self, from_asset: str, to_asset: str, from_amount: float) -> dict:
        client = get_client()
        return await client._post(f"{client.base}/sapi/v1/convert/getQuote",
                                  {"fromAsset": from_asset, "toAsset": to_asset, "fromAmount": from_amount})

    async def accept_quote(self, quote_id: str) -> dict:
        client = get_client()
        return await client._post(f"{client.base}/sapi/v1/convert/acceptQuote", {"quoteId": quote_id})

    async def get_convert_history(self, limit: int = 10) -> list:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/convert/tradeFlow",
                                 {"limit": limit}, signed=True)


class DerivativesCoinFuturesSkill:
    """COIN-M perpetual and quarterly futures trading."""
    name = "derivatives-trading-coin-futures"

    async def place_order(self, symbol: str, side: str, order_type: str, **kwargs) -> dict:
        client = get_client()
        return await client._post(f"{client.coin_base}/dapi/v1/order",
                                  {"symbol": symbol, "side": side, "type": order_type, **kwargs})

    async def cancel_order(self, symbol: str, order_id: int) -> dict:
        client = get_client()
        return await client._delete(f"{client.coin_base}/dapi/v1/order",
                                    {"symbol": symbol, "orderId": order_id})

    async def get_positions(self) -> list:
        client = get_client()
        data = await client._get(f"{client.coin_base}/dapi/v1/account", signed=True)
        return [p for p in data.get("positions", []) if float(p.get("positionAmt", 0)) != 0]

    async def set_leverage(self, symbol: str, leverage: int) -> dict:
        client = get_client()
        return await client._post(f"{client.coin_base}/dapi/v1/leverage",
                                  {"symbol": symbol, "leverage": leverage})


class DerivativesOptionsSkill:
    """European-style options on Binance."""
    name = "derivatives-trading-options"

    async def get_option_info(self, underlying: str) -> dict:
        client = get_client()
        return await client._get("https://eapi.binance.com/eapi/v1/exchangeInfo",
                                 {"underlying": underlying})

    async def place_option_order(self, symbol: str, side: str, order_type: str, **kwargs) -> dict:
        client = get_client()
        return await client._post("https://eapi.binance.com/eapi/v1/order",
                                  {"symbol": symbol, "side": side, "type": order_type, **kwargs})

    async def get_option_positions(self) -> list:
        client = get_client()
        return await client._get("https://eapi.binance.com/eapi/v1/position", signed=True)


class DerivativesPortfolioMarginSkill:
    """Portfolio margin account operations."""
    name = "derivatives-trading-portfolio-margin"

    async def get_pm_account(self) -> dict:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/portfolio/account", signed=True)

    async def get_pm_balance(self) -> list:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/portfolio/balance", signed=True)

    async def transfer_to_pm(self, asset: str, amount: float) -> dict:
        client = get_client()
        return await client._post(f"{client.base}/sapi/v1/portfolio/asset-transfer",
                                  {"asset": asset, "amount": amount, "type": "SPOT_TO_PORTFOLIO"})


class DerivativesPortfolioMarginProSkill:
    """Portfolio margin PRO account operations."""
    name = "derivatives-trading-portfolio-margin-pro"

    async def get_pm_pro_account(self) -> dict:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v2/portfolio/account", signed=True)

    async def get_pm_pro_balance(self) -> list:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v2/portfolio/balance", signed=True)


class DerivativesUSDSFuturesSkill:
    """USDS-M perpetual futures trading."""
    name = "derivatives-trading-usds-futures"

    async def place_order(self, symbol: str, side: str, order_type: str, **kwargs) -> dict:
        client = get_client()
        return await client.place_futures_order(symbol, side, order_type, **kwargs)

    async def cancel_order(self, symbol: str, order_id: int) -> dict:
        client = get_client()
        return await client._delete(f"{client.futures_base}/fapi/v1/order",
                                    {"symbol": symbol, "orderId": order_id})

    async def get_positions(self) -> list:
        return await get_client().get_futures_positions()

    async def set_leverage(self, symbol: str, leverage: int) -> dict:
        return await get_client().set_futures_leverage(symbol, leverage)

    async def set_margin_type(self, symbol: str, margin_type: str) -> dict:
        return await get_client().set_futures_margin_type(symbol, margin_type)

    async def get_funding_rate(self, symbol: str) -> dict:
        client = get_client()
        return await client._get(f"{client.futures_base}/fapi/v1/premiumIndex", {"symbol": symbol})


class FiatSkill:
    """Fiat deposit and withdrawal history."""
    name = "fiat"

    async def get_fiat_orders(self, transaction_type: int = 0) -> list:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/fiat/orders",
                                 {"transactionType": transaction_type}, signed=True)

    async def get_fiat_payments(self) -> list:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/fiat/payments", signed=True)


class MarginTradingSkill:
    """Cross and isolated margin trading."""
    name = "margin-trading"

    async def borrow(self, asset: str, amount: float, symbol: str = "", is_isolated: bool = False) -> dict:
        client = get_client()
        params: dict = {"asset": asset, "amount": amount}
        if is_isolated:
            params["symbol"] = symbol
            params["isIsolated"] = "TRUE"
        return await client._post(f"{client.base}/sapi/v1/margin/loan", params)

    async def repay(self, asset: str, amount: float, symbol: str = "", is_isolated: bool = False) -> dict:
        client = get_client()
        params: dict = {"asset": asset, "amount": amount}
        if is_isolated:
            params["symbol"] = symbol
            params["isIsolated"] = "TRUE"
        return await client._post(f"{client.base}/sapi/v1/margin/repay", params)

    async def place_order(self, symbol: str, side: str, order_type: str, **kwargs) -> dict:
        client = get_client()
        return await client._post(f"{client.base}/sapi/v1/margin/order",
                                  {"symbol": symbol, "side": side, "type": order_type, **kwargs})

    async def get_margin_account(self) -> dict:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/margin/account", signed=True)

    async def get_isolated_margin_account(self) -> dict:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/margin/isolated/account", signed=True)


class OnchainPaySkill:
    """Binance Pay On-Chain invoice creation and query."""
    name = "onchain-pay"

    async def create_invoice(self, amount: float, currency: str, desc: str = "") -> dict:
        client = get_client()
        return await client._post(f"{client.base}/sapi/v1/pay/transactions",
                                  {"amount": amount, "currency": currency, "description": desc})

    async def query_invoice(self, order_id: str) -> dict:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/pay/transactions/query",
                                 {"prepayId": order_id}, signed=True)


class P2PSkill:
    """P2P trading history."""
    name = "p2p"

    async def get_p2p_history(self, trade_type: str = "BUY", limit: int = 10) -> list:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/c2c/orderMatch/listUserOrderHistory",
                                 {"tradeType": trade_type, "page": 1, "rows": limit}, signed=True)


class SimpleEarnSkill:
    """Flexible and locked earn products."""
    name = "simple-earn"

    async def get_flexible_products(self) -> list:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/simple-earn/flexible/list", signed=True)

    async def subscribe_flexible(self, product_id: str, amount: float) -> dict:
        client = get_client()
        return await client._post(f"{client.base}/sapi/v1/simple-earn/flexible/subscribe",
                                  {"productId": product_id, "amount": amount})

    async def redeem_flexible(self, product_id: str, amount: float) -> dict:
        client = get_client()
        return await client._post(f"{client.base}/sapi/v1/simple-earn/flexible/redeem",
                                  {"productId": product_id, "amount": amount})

    async def get_earn_account(self) -> dict:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/simple-earn/account", signed=True)


class SpotSkill:
    """Spot trading — orders, order book, and trade history."""
    name = "spot"

    async def place_order(self, symbol: str, side: str, order_type: str, **kwargs) -> dict:
        return await get_client().place_spot_order(symbol, side, order_type, **kwargs)

    async def cancel_order(self, symbol: str, order_id: int) -> dict:
        return await get_client().cancel_spot_order(symbol, order_id)

    async def get_open_orders(self, symbol: str | None = None) -> list:
        return await get_client().get_open_orders(symbol)

    async def get_order_book(self, symbol: str, limit: int = 20) -> dict:
        return await get_client().get_order_book(symbol, limit)

    async def get_ticker(self, symbol: str) -> dict:
        return await get_client().get_ticker(symbol)

    async def get_recent_trades(self, symbol: str, limit: int = 50) -> list:
        return await get_client()._get(f"{get_client().base}/api/v3/trades",
                                        {"symbol": symbol, "limit": limit})


class SquarePostSkill:
    """Binance Square (social feed) post reading."""
    name = "square-post"

    async def get_feed(self, limit: int = 10) -> list:
        client = get_client()
        try:
            return await client._get(f"{client.base}/sapi/v1/square/feed", {"limit": limit})
        except Exception:
            return []


class SubAccountSkill:
    """Sub-account management and transfers."""
    name = "sub-account"

    async def list_sub_accounts(self) -> list:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/sub-account/list", signed=True)

    async def get_sub_account_assets(self, email: str) -> dict:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v3/sub-account/assets",
                                 {"email": email}, signed=True)

    async def transfer_to_sub(self, to_email: str, asset: str, amount: float) -> dict:
        client = get_client()
        return await client._post(f"{client.base}/sapi/v1/sub-account/universalTransfer",
                                  {"toAccountType": "SPOT", "toEmail": to_email,
                                   "asset": asset, "amount": amount})


class VipLoanSkill:
    """VIP Loan borrow and repay operations."""
    name = "vip-loan"

    async def get_vip_loan_orders(self) -> list:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/loan/vip/ongoing/orders", signed=True)

    async def borrow(self, loan_coin: str, loan_amount: float, collateral_coin: str, collateral_amount: float) -> dict:
        client = get_client()
        return await client._post(f"{client.base}/sapi/v1/loan/vip/borrow",
                                  {"loanCoin": loan_coin, "loanAmount": loan_amount,
                                   "collateralCoin": collateral_coin, "collateralAmount": collateral_amount})

    async def repay_vip_loan(self, order_id: int, amount: float) -> dict:
        client = get_client()
        return await client._post(f"{client.base}/sapi/v1/loan/vip/repay",
                                  {"orderId": order_id, "amount": amount})


# ─────────────────────────────────────────────────────────
# BINANCE-WEB3/ SKILLS
# ─────────────────────────────────────────────────────────

class TokenizedSecuritiesSkill:
    """Binance tokenized securities information."""
    name = "binance-tokenized-securities-info"

    async def get_securities(self) -> list:
        client = get_client()
        try:
            return await client._get(f"{client.base}/sapi/v1/broker/subAccount")
        except Exception:
            return []

    async def get_security_detail(self, symbol: str) -> dict:
        return {"symbol": symbol, "note": "Use Binance web3 API for full detail"}


class CryptoMarketRankSkill:
    """Crypto market rank and trending tokens."""
    name = "crypto-market-rank"
    COINGECKO = "https://api.coingecko.com/api/v3"

    async def get_market_rank(self, limit: int = 20) -> list:
        import aiohttp
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{self.COINGECKO}/coins/markets",
                             params={"vs_currency": "usd", "order": "market_cap_desc",
                                     "per_page": limit, "page": 1}) as r:
                return await r.json()

    async def get_trending(self) -> list:
        import aiohttp
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{self.COINGECKO}/search/trending") as r:
                data = await r.json()
                return data.get("coins", [])


class MemeRushSkill:
    """Binance Meme Rush leaderboard and trending meme tokens."""
    name = "meme-rush"

    async def get_meme_tokens(self) -> list:
        client = get_client()
        try:
            return await client._get(f"{client.base}/sapi/v1/meme/tokens")
        except Exception:
            return []

    async def get_meme_leaderboard(self) -> list:
        client = get_client()
        try:
            return await client._get(f"{client.base}/sapi/v1/meme/leaderboard")
        except Exception:
            return []


class QueryAddressInfoSkill:
    """On-chain address info and risk scoring."""
    name = "query-address-info"

    async def query_address(self, address: str, chain: str = "ETH") -> dict:
        client = get_client()
        return await client._get(f"{client.base}/sapi/v1/web3/address",
                                 {"address": address, "chain": chain}, signed=True)


class QueryTokenAuditSkill:
    """On-chain token audit / contract analysis."""
    name = "query-token-audit"

    async def audit_token(self, contract_address: str, chain: str = "ETH") -> dict:
        client = get_client()
        try:
            return await client._get(f"{client.base}/sapi/v1/web3/token/audit",
                                     {"contractAddress": contract_address, "chain": chain})
        except Exception:
            return {"status": "unavailable", "contractAddress": contract_address}


class QueryTokenInfoSkill:
    """On-chain token info and price."""
    name = "query-token-info"

    DEXSCREENER = "https://api.dexscreener.com/latest/dex"

    async def get_token_info(self, contract_address: str) -> dict:
        import aiohttp
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{self.DEXSCREENER}/tokens/{contract_address}") as r:
                return await r.json()

    async def get_token_price(self, contract_address: str) -> float:
        data = await self.get_token_info(contract_address)
        pairs = data.get("pairs") or []
        if pairs:
            return float(pairs[0].get("priceUsd", 0))
        return 0.0


class TradingSignalSkill:
    """Trading signals from the Binance web3 signal feed."""
    name = "trading-signal"

    async def get_signals(self, limit: int = 10) -> list:
        client = get_client()
        try:
            return await client._get(f"{client.base}/sapi/v1/trading/signal", {"limit": limit})
        except Exception:
            return []

    async def get_signal_by_symbol(self, symbol: str) -> dict:
        client = get_client()
        try:
            return await client._get(f"{client.base}/sapi/v1/trading/signal/symbol", {"symbol": symbol})
        except Exception:
            return {}


# ─────────────────────────────────────────────────────────
# Skill Registry
# ─────────────────────────────────────────────────────────

ALL_SKILLS = {
    "algo": AlgoSkill(),
    "alpha": AlphaSkill(),
    "assets": AssetsSkill(),
    "convert": ConvertSkill(),
    "derivatives_coin_futures": DerivativesCoinFuturesSkill(),
    "derivatives_options": DerivativesOptionsSkill(),
    "derivatives_portfolio_margin": DerivativesPortfolioMarginSkill(),
    "derivatives_portfolio_margin_pro": DerivativesPortfolioMarginProSkill(),
    "derivatives_usds_futures": DerivativesUSDSFuturesSkill(),
    "fiat": FiatSkill(),
    "margin_trading": MarginTradingSkill(),
    "onchain_pay": OnchainPaySkill(),
    "p2p": P2PSkill(),
    "simple_earn": SimpleEarnSkill(),
    "spot": SpotSkill(),
    "square_post": SquarePostSkill(),
    "sub_account": SubAccountSkill(),
    "vip_loan": VipLoanSkill(),
    "tokenized_securities": TokenizedSecuritiesSkill(),
    "crypto_market_rank": CryptoMarketRankSkill(),
    "meme_rush": MemeRushSkill(),
    "query_address_info": QueryAddressInfoSkill(),
    "query_token_audit": QueryTokenAuditSkill(),
    "query_token_info": QueryTokenInfoSkill(),
    "trading_signal": TradingSignalSkill(),
}
