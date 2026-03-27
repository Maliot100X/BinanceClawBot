"""
Binance Skills Hub Loader
Imports all 26 skills from the cloned binance-skills-hub repo.
Each skill wraps the exact endpoints defined in its SKILL.md.
"""
from __future__ import annotations
import hmac, hashlib, time, urllib.parse, json
from pathlib import Path
from typing import Any
import aiohttp
from loguru import logger
from config.settings import settings

SKILLS_HUB = Path(__file__).resolve().parent.parent / "binance-skills-hub" / "skills"
BASE          = "https://api.binance.com"
FUTURES_BASE  = "https://fapi.binance.com"
COIN_BASE     = "https://dapi.binance.com"
OPTIONS_BASE  = "https://eapi.binance.com"
ALPHA_BASE    = "https://www.binance.com"
DEMO_BASE     = "https://demo-api.binance.com"


# ── Shared signing helper ─────────────────────────────────────────────────────
def _sign(params: dict, secret: str) -> dict:
    params["timestamp"] = int(time.time() * 1000)
    qs = urllib.parse.urlencode(params)
    sig = hmac.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    params["signature"] = sig
    return params


class SkillBase:
    """Base class for all 26 Binance skills. Handles auth + HTTP."""
    skill_name: str = "base"

    def __init__(self):
        self._ua      = f"binance-{self.skill_name}/1.1.0 (Skill)"
        skill_path    = SKILLS_HUB / "binance" / self.skill_name / "SKILL.md"
        if not skill_path.exists():
            skill_path = SKILLS_HUB / "binance-web3" / self.skill_name / "SKILL.md"
        self.skill_md = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""
        logger.debug(f"Loaded skill: {self.skill_name}")

    @property
    def _api_key(self) -> str:
        import os
        return os.environ.get("BINANCE_API_KEY") or settings.binance_api_key

    @property
    def _secret(self) -> str:
        import os
        return os.environ.get("BINANCE_SECRET_KEY") or settings.binance_secret_key

    def _headers(self) -> dict:
        return {"X-MBX-APIKEY": self._api_key, "User-Agent": self._ua, "Content-Type": "application/json"}

    async def _get(self, url: str, params: dict | None = None, signed: bool = False) -> Any:
        p = dict(params or {})
        if signed: p = _sign(p, self._secret)
        async with aiohttp.ClientSession(headers=self._headers()) as s:
            async with s.get(url, params=p) as r:
                r.raise_for_status()
                return await r.json()

    async def _post(self, url: str, params: dict | None = None, signed: bool = True) -> Any:
        p = dict(params or {})
        if signed: p = _sign(p, self._secret)
        async with aiohttp.ClientSession(headers=self._headers()) as s:
            async with s.post(url, params=p) as r:
                r.raise_for_status()
                return await r.json()

    async def _delete(self, url: str, params: dict | None = None) -> Any:
        p = _sign(dict(params or {}), self._secret)
        async with aiohttp.ClientSession(headers=self._headers()) as s:
            async with s.delete(url, params=p) as r:
                r.raise_for_status()
                return await r.json()

    def endpoints(self) -> str:
        """Return the Quick Reference table from the real SKILL.md."""
        lines = self.skill_md.split("\n")
        in_table = False
        out = []
        for l in lines:
            if "| Endpoint |" in l:
                in_table = True
            if in_table:
                if l.startswith("|"):
                    out.append(l)
                elif out:
                    break
        return "\n".join(out)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ALGO  (/sapi/v1/algo/...)
# ═══════════════════════════════════════════════════════════════════════════════
class AlgoSkill(SkillBase):
    skill_name = "algo"

    # Futures algo
    async def new_twap_futures(self, symbol, side, quantity, duration=3600, **kw):
        return await self._post(f"{BASE}/sapi/v1/algo/futures/newOrderTwap",
            {"symbol": symbol, "side": side, "quantity": quantity, "duration": duration, **kw})

    async def new_vp_futures(self, symbol, side, quantity, urgency="LOW", **kw):
        return await self._post(f"{BASE}/sapi/v1/algo/futures/newOrderVp",
            {"symbol": symbol, "side": side, "quantity": quantity, "urgency": urgency, **kw})

    async def cancel_futures_algo(self, algo_id: int):
        return await self._delete(f"{BASE}/sapi/v1/algo/futures/order", {"algoId": algo_id})

    async def open_futures_algo_orders(self):
        return await self._get(f"{BASE}/sapi/v1/algo/futures/openOrders", signed=True)

    async def historical_futures_algo_orders(self, **kw):
        return await self._get(f"{BASE}/sapi/v1/algo/futures/historicalOrders", kw, signed=True)

    async def futures_sub_orders(self, algo_id: int, **kw):
        return await self._get(f"{BASE}/sapi/v1/algo/futures/subOrders", {"algoId": algo_id, **kw}, signed=True)

    # Spot algo
    async def new_twap_spot(self, symbol, side, quantity, duration=3600, **kw):
        return await self._post(f"{BASE}/sapi/v1/algo/spot/newOrderTwap",
            {"symbol": symbol, "side": side, "quantity": quantity, "duration": duration, **kw})

    async def cancel_spot_algo(self, algo_id: int):
        return await self._delete(f"{BASE}/sapi/v1/algo/spot/order", {"algoId": algo_id})

    async def open_spot_algo_orders(self):
        return await self._get(f"{BASE}/sapi/v1/algo/spot/openOrders", signed=True)

    async def historical_spot_algo_orders(self, **kw):
        return await self._get(f"{BASE}/sapi/v1/algo/spot/historicalOrders", kw, signed=True)

    async def spot_sub_orders(self, algo_id: int, **kw):
        return await self._get(f"{BASE}/sapi/v1/algo/spot/subOrders", {"algoId": algo_id, **kw}, signed=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ALPHA  (/bapi/defi/v1/public/alpha-trade/...)
# ═══════════════════════════════════════════════════════════════════════════════
class AlphaSkill(SkillBase):
    skill_name = "alpha"
    _B = f"{ALPHA_BASE}/bapi/defi/v1/public/alpha-trade"

    async def ticker(self, symbol: str):
        return await self._get(f"{self._B}/ticker", {"symbol": symbol})

    async def agg_trades(self, symbol: str, **kw):
        return await self._get(f"{self._B}/agg-trades", {"symbol": symbol, **kw})

    async def exchange_info(self):
        return await self._get(f"{self._B}/get-exchange-info")

    async def klines(self, symbol: str, interval: str = "1h", **kw):
        return await self._get(f"{self._B}/klines", {"symbol": symbol, "interval": interval, **kw})

    async def token_list(self):
        return await self._get(
            f"{ALPHA_BASE}/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ASSETS  (/sapi/v1/asset/..., /sapi/v1/capital/...)
# ═══════════════════════════════════════════════════════════════════════════════
class AssetsSkill(SkillBase):
    skill_name = "assets"

    async def api_trading_status(self): return await self._get(f"{BASE}/sapi/v1/account/apiTradingStatus", signed=True)
    async def account_info(self): return await self._get(f"{BASE}/sapi/v1/account/info", signed=True)
    async def account_status(self): return await self._get(f"{BASE}/sapi/v1/account/status", signed=True)
    async def api_restrictions(self): return await self._get(f"{BASE}/sapi/v1/account/apiRestrictions", signed=True)
    async def account_snapshot(self, type_: str = "SPOT", **kw): return await self._get(f"{BASE}/sapi/v1/accountSnapshot", {"type": type_, **kw}, signed=True)
    async def asset_detail(self, asset: str | None = None): return await self._get(f"{BASE}/sapi/v1/asset/assetDetail", {"asset": asset} if asset else {}, signed=True)
    async def asset_dividend(self, **kw): return await self._get(f"{BASE}/sapi/v1/asset/assetDividend", kw, signed=True)
    async def dust_log(self, **kw): return await self._get(f"{BASE}/sapi/v1/asset/dribblet", kw, signed=True)
    async def funding_wallet(self, **kw): return await self._post(f"{BASE}/sapi/v1/asset/get-funding-asset", kw)
    async def user_asset(self, **kw): return await self._post(f"{BASE}/sapi/v3/asset/getUserAsset", kw)
    async def wallet_balance(self, **kw): return await self._get(f"{BASE}/sapi/v1/asset/wallet/balance", kw, signed=True)
    async def trade_fee(self, symbol: str | None = None): return await self._get(f"{BASE}/sapi/v1/asset/tradeFee", {"symbol": symbol} if symbol else {}, signed=True)
    async def transfer(self, type_: str, asset: str, amount: float): return await self._post(f"{BASE}/sapi/v1/asset/transfer", {"type": type_, "asset": asset, "amount": amount})
    async def transfer_history(self, type_: str, **kw): return await self._get(f"{BASE}/sapi/v1/asset/transfer", {"type": type_, **kw}, signed=True)
    async def all_coins(self): return await self._get(f"{BASE}/sapi/v1/capital/config/getall", signed=True)
    async def deposit_address(self, coin: str, network: str = "", **kw): return await self._get(f"{BASE}/sapi/v1/capital/deposit/address", {"coin": coin, "network": network, **kw}, signed=True)
    async def deposit_history(self, **kw): return await self._get(f"{BASE}/sapi/v1/capital/deposit/hisrec", kw, signed=True)
    async def withdraw_history(self, **kw): return await self._get(f"{BASE}/sapi/v1/capital/withdraw/history", kw, signed=True)
    async def withdraw(self, coin: str, address: str, amount: float, **kw): return await self._post(f"{BASE}/sapi/v1/capital/withdraw/apply", {"coin": coin, "address": address, "amount": amount, **kw})
    async def system_status(self): return await self._get(f"{BASE}/sapi/v1/system/status")
    async def open_symbol_list(self): return await self._get(f"{BASE}/sapi/v1/spot/open-symbol-list")
    async def delist_schedule(self): return await self._get(f"{BASE}/sapi/v1/spot/delist-schedule")
    async def dust_transfer(self, asset: list[str], **kw): return await self._post(f"{BASE}/sapi/v1/asset/dust", {"asset": ",".join(asset), **kw})
    async def bnb_burn(self, spot: bool = True, interest: bool = True): return await self._post(f"{BASE}/sapi/v1/bnbBurn", {"spotBNBBurn": str(spot).lower(), "interestBNBBurn": str(interest).lower()})


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CONVERT
# ═══════════════════════════════════════════════════════════════════════════════
class ConvertSkill(SkillBase):
    skill_name = "convert"

    async def list_pairs(self, **kw): return await self._get(f"{BASE}/sapi/v1/convert/exchangeInfo", kw)
    async def get_quote(self, from_asset, to_asset, from_amount=None, to_amount=None, **kw):
        p = {"fromAsset": from_asset, "toAsset": to_asset}
        if from_amount: p["fromAmount"] = from_amount
        if to_amount: p["toAmount"] = to_amount
        return await self._post(f"{BASE}/sapi/v1/convert/getQuote", {**p, **kw})
    async def accept_quote(self, quote_id: str): return await self._post(f"{BASE}/sapi/v1/convert/acceptQuote", {"quoteId": quote_id})
    async def order_status(self, order_id: str = "", client_order_id: str = ""):
        p = {}
        if order_id: p["orderId"] = order_id
        if client_order_id: p["clientOrderId"] = client_order_id
        return await self._get(f"{BASE}/sapi/v1/convert/orderStatus", p, signed=True)
    async def trade_history(self, start_time: int, end_time: int, **kw):
        return await self._get(f"{BASE}/sapi/v1/convert/tradeFlow", {"startTime": start_time, "endTime": end_time, **kw}, signed=True)
    async def asset_info(self): return await self._get(f"{BASE}/sapi/v1/convert/assetInfo", signed=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. DERIVATIVES – COIN FUTURES (/dapi/v1/...)
# ═══════════════════════════════════════════════════════════════════════════════
class DerivativesCoinFuturesSkill(SkillBase):
    skill_name = "derivatives-trading-coin-futures"

    async def ping(self): return await self._get(f"{COIN_BASE}/dapi/v1/ping")
    async def time(self): return await self._get(f"{COIN_BASE}/dapi/v1/time")
    async def exchange_info(self): return await self._get(f"{COIN_BASE}/dapi/v1/exchangeInfo")
    async def order_book(self, symbol, limit=20): return await self._get(f"{COIN_BASE}/dapi/v1/depth", {"symbol": symbol, "limit": limit})
    async def klines(self, symbol, interval="1h", limit=200): return await self._get(f"{COIN_BASE}/dapi/v1/klines", {"symbol": symbol, "interval": interval, "limit": limit})
    async def ticker_24hr(self, symbol=None): return await self._get(f"{COIN_BASE}/dapi/v1/ticker/24hr", {"symbol": symbol} if symbol else {})
    async def ticker_price(self, symbol=None): return await self._get(f"{COIN_BASE}/dapi/v1/ticker/price", {"symbol": symbol} if symbol else {})
    async def new_order(self, symbol, side, type_, **kw): return await self._post(f"{COIN_BASE}/dapi/v1/order", {"symbol": symbol, "side": side, "type": type_, **kw})
    async def cancel_order(self, symbol, order_id): return await self._delete(f"{COIN_BASE}/dapi/v1/order", {"symbol": symbol, "orderId": order_id})
    async def cancel_all_orders(self, symbol): return await self._delete(f"{COIN_BASE}/dapi/v1/allOpenOrders", {"symbol": symbol})
    async def open_orders(self, symbol=None): return await self._get(f"{COIN_BASE}/dapi/v1/openOrders", {"symbol": symbol} if symbol else {}, signed=True)
    async def all_orders(self, symbol, **kw): return await self._get(f"{COIN_BASE}/dapi/v1/allOrders", {"symbol": symbol, **kw}, signed=True)
    async def account(self): return await self._get(f"{COIN_BASE}/dapi/v2/account", signed=True)
    async def positions(self, symbol=None): d = await self.account(); return [p for p in d.get("positions",[]) if float(p.get("positionAmt",0))!=0]
    async def set_leverage(self, symbol, leverage): return await self._post(f"{COIN_BASE}/dapi/v1/leverage", {"symbol": symbol, "leverage": leverage})
    async def set_margin_type(self, symbol, margin_type): return await self._post(f"{COIN_BASE}/dapi/v1/marginType", {"symbol": symbol, "marginType": margin_type})
    async def my_trades(self, symbol, **kw): return await self._get(f"{COIN_BASE}/dapi/v1/userTrades", {"symbol": symbol, **kw}, signed=True)
    async def funding_rate(self, symbol, **kw): return await self._get(f"{COIN_BASE}/dapi/v1/fundingRate", {"symbol": symbol, **kw})
    async def premium_index(self, symbol=None): return await self._get(f"{COIN_BASE}/dapi/v1/premiumIndex", {"symbol": symbol} if symbol else {})


# ═══════════════════════════════════════════════════════════════════════════════
# 6. DERIVATIVES – OPTIONS (/eapi/v1/...)
# ═══════════════════════════════════════════════════════════════════════════════
class DerivativesOptionsSkill(SkillBase):
    skill_name = "derivatives-trading-options"

    async def exchange_info(self): return await self._get(f"{OPTIONS_BASE}/eapi/v1/exchangeInfo")
    async def index(self, underlying): return await self._get(f"{OPTIONS_BASE}/eapi/v1/index", {"underlying": underlying})
    async def mark_price(self, symbol=None): return await self._get(f"{OPTIONS_BASE}/eapi/v1/mark", {"symbol": symbol} if symbol else {})
    async def new_order(self, symbol, side, type_, quantity, price=None, **kw):
        p = {"symbol": symbol, "side": side, "type": type_, "quantity": quantity}
        if price: p["price"] = price
        return await self._post(f"{OPTIONS_BASE}/eapi/v1/order", {**p, **kw})
    async def cancel_order(self, symbol, order_id): return await self._delete(f"{OPTIONS_BASE}/eapi/v1/order", {"symbol": symbol, "orderId": order_id})
    async def open_orders(self, symbol=None): return await self._get(f"{OPTIONS_BASE}/eapi/v1/openOrders", {"symbol": symbol} if symbol else {}, signed=True)
    async def positions(self): return await self._get(f"{OPTIONS_BASE}/eapi/v1/position", signed=True)
    async def account(self): return await self._get(f"{OPTIONS_BASE}/eapi/v1/account", signed=True)
    async def option_info(self, symbol): return await self._get(f"{OPTIONS_BASE}/eapi/v1/ticker", {"symbol": symbol})


# ═══════════════════════════════════════════════════════════════════════════════
# 7. PORTFOLIO MARGIN
# ═══════════════════════════════════════════════════════════════════════════════
class DerivativesPortfolioMarginSkill(SkillBase):
    skill_name = "derivatives-trading-portfolio-margin"

    async def account(self): return await self._get(f"{BASE}/sapi/v1/portfolio/account", signed=True)
    async def balance(self): return await self._get(f"{BASE}/sapi/v1/portfolio/balance", signed=True)
    async def collateral_rate(self): return await self._get(f"{BASE}/sapi/v1/portfolio/collateralRate")
    async def pm_loan(self): return await self._get(f"{BASE}/sapi/v1/portfolio/pmLoan", signed=True)
    async def repay(self, **kw): return await self._post(f"{BASE}/sapi/v1/portfolio/repay", kw)
    async def asset_transfer(self, asset, amount, from_account="SPOT", to_account="PORTFOLIO"):
        return await self._post(f"{BASE}/sapi/v1/portfolio/asset-transfer", {"asset": asset, "amount": amount, "type": f"{from_account}_TO_{to_account}"})
    async def margin_asset_leverage(self): return await self._get(f"{BASE}/sapi/v1/portfolio/marginAssetLeverage")
    async def pm_position_risk(self): return await self._get(f"{BASE}/sapi/v1/portfolio/pmPositionRisk", signed=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 8. PORTFOLIO MARGIN PRO
# ═══════════════════════════════════════════════════════════════════════════════
class DerivativesPortfolioMarginProSkill(SkillBase):
    skill_name = "derivatives-trading-portfolio-margin-pro"

    async def account(self): return await self._get(f"{BASE}/sapi/v2/portfolio/account", signed=True)
    async def balance(self): return await self._get(f"{BASE}/sapi/v2/portfolio/balance", signed=True)
    async def position_risk(self): return await self._get(f"{BASE}/sapi/v2/portfolio/pmPositionRisk", signed=True)
    async def repay(self, **kw): return await self._post(f"{BASE}/sapi/v2/portfolio/repay", kw)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. DERIVATIVES – USDS FUTURES (/fapi/v1/...)
# ═══════════════════════════════════════════════════════════════════════════════
class DerivativesUSDSFuturesSkill(SkillBase):
    skill_name = "derivatives-trading-usds-futures"

    async def ping(self): return await self._get(f"{FUTURES_BASE}/fapi/v1/ping")
    async def time(self): return await self._get(f"{FUTURES_BASE}/fapi/v1/time")
    async def exchange_info(self): return await self._get(f"{FUTURES_BASE}/fapi/v1/exchangeInfo")
    async def order_book(self, symbol, limit=20): return await self._get(f"{FUTURES_BASE}/fapi/v1/depth", {"symbol": symbol, "limit": limit})
    async def klines(self, symbol, interval="1h", limit=200): return await self._get(f"{FUTURES_BASE}/fapi/v1/klines", {"symbol": symbol, "interval": interval, "limit": limit})
    async def ticker_24hr(self, symbol=None): return await self._get(f"{FUTURES_BASE}/fapi/v1/ticker/24hr", {"symbol": symbol} if symbol else {})
    async def ticker_price(self, symbol=None): return await self._get(f"{FUTURES_BASE}/fapi/v2/ticker/price", {"symbol": symbol} if symbol else {})
    async def premium_index(self, symbol=None): return await self._get(f"{FUTURES_BASE}/fapi/v1/premiumIndex", {"symbol": symbol} if symbol else {})
    async def funding_rate(self, symbol, **kw): return await self._get(f"{FUTURES_BASE}/fapi/v1/fundingRate", {"symbol": symbol, **kw})
    async def new_order(self, symbol, side, type_, **kw): return await self._post(f"{FUTURES_BASE}/fapi/v1/order", {"symbol": symbol, "side": side, "type": type_, **kw})
    async def cancel_order(self, symbol, order_id): return await self._delete(f"{FUTURES_BASE}/fapi/v1/order", {"symbol": symbol, "orderId": order_id})
    async def cancel_all_orders(self, symbol): return await self._delete(f"{FUTURES_BASE}/fapi/v1/allOpenOrders", {"symbol": symbol})
    async def open_orders(self, symbol=None): return await self._get(f"{FUTURES_BASE}/fapi/v1/openOrders", {"symbol": symbol} if symbol else {}, signed=True)
    async def account(self): return await self._get(f"{FUTURES_BASE}/fapi/v2/account", signed=True)
    async def balance(self): return await self._get(f"{FUTURES_BASE}/fapi/v2/balance", signed=True)
    async def positions(self): d = await self.account(); return [p for p in d.get("positions",[]) if float(p.get("positionAmt",0))!=0]
    async def set_leverage(self, symbol, leverage): return await self._post(f"{FUTURES_BASE}/fapi/v1/leverage", {"symbol": symbol, "leverage": leverage})
    async def set_margin_type(self, symbol, margin_type): return await self._post(f"{FUTURES_BASE}/fapi/v1/marginType", {"symbol": symbol, "marginType": margin_type})
    async def set_position_mode(self, dual: bool): return await self._post(f"{FUTURES_BASE}/fapi/v1/positionSide/dual", {"dualSidePosition": str(dual).lower()})
    async def my_trades(self, symbol, **kw): return await self._get(f"{FUTURES_BASE}/fapi/v1/userTrades", {"symbol": symbol, **kw}, signed=True)
    async def income_history(self, **kw): return await self._get(f"{FUTURES_BASE}/fapi/v1/income", kw, signed=True)
    async def top_trader_positions(self, symbol, period="5m"): return await self._get(f"{FUTURES_BASE}/futures/data/topLongShortPositionRatio", {"symbol": symbol, "period": period})


# ═══════════════════════════════════════════════════════════════════════════════
# 10. FIAT
# ═══════════════════════════════════════════════════════════════════════════════
class FiatSkill(SkillBase):
    skill_name = "fiat"

    async def fiat_orders(self, transaction_type=0, **kw): return await self._get(f"{BASE}/sapi/v1/fiat/orders", {"transactionType": transaction_type, **kw}, signed=True)
    async def fiat_payments(self, transaction_type=0, **kw): return await self._get(f"{BASE}/sapi/v1/fiat/payments", {"transactionType": transaction_type, **kw}, signed=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 11. MARGIN TRADING
# ═══════════════════════════════════════════════════════════════════════════════
class MarginTradingSkill(SkillBase):
    skill_name = "margin-trading"

    async def cross_margin_account(self): return await self._get(f"{BASE}/sapi/v1/margin/account", signed=True)
    async def isolated_margin_account(self, symbols=None): return await self._get(f"{BASE}/sapi/v1/margin/isolated/account", {"symbols": symbols} if symbols else {}, signed=True)
    async def borrow_repay(self, asset, is_isolated, symbol, amount, type_): return await self._post(f"{BASE}/sapi/v1/margin/borrow-repay", {"asset": asset, "isIsolated": is_isolated, "symbol": symbol, "amount": amount, "type": type_})
    async def borrow_repay_records(self, type_, **kw): return await self._get(f"{BASE}/sapi/v1/margin/borrow-repay", {"type": type_, **kw}, signed=True)
    async def max_borrowable(self, asset, isolated_symbol=None): return await self._get(f"{BASE}/sapi/v1/margin/maxBorrowable", {"asset": asset, **({"isolatedSymbol": isolated_symbol} if isolated_symbol else {})}, signed=True)
    async def max_transferable(self, asset, isolated_symbol=None): return await self._get(f"{BASE}/sapi/v1/margin/maxTransferable", {"asset": asset, **({"isolatedSymbol": isolated_symbol} if isolated_symbol else {})}, signed=True)
    async def new_order(self, symbol, side, type_, **kw): return await self._post(f"{BASE}/sapi/v1/margin/order", {"symbol": symbol, "side": side, "type": type_, **kw})
    async def cancel_order(self, symbol, order_id, **kw): return await self._delete(f"{BASE}/sapi/v1/margin/order", {"symbol": symbol, "orderId": order_id, **kw})
    async def open_orders(self, symbol=None, is_isolated=False): return await self._get(f"{BASE}/sapi/v1/margin/openOrders", {"symbol": symbol, "isIsolated": is_isolated} if symbol else {}, signed=True)
    async def all_orders(self, symbol, **kw): return await self._get(f"{BASE}/sapi/v1/margin/allOrders", {"symbol": symbol, **kw}, signed=True)
    async def my_trades(self, symbol, **kw): return await self._get(f"{BASE}/sapi/v1/margin/myTrades", {"symbol": symbol, **kw}, signed=True)
    async def interest_history(self, **kw): return await self._get(f"{BASE}/sapi/v1/margin/interestHistory", kw, signed=True)
    async def all_assets(self): return await self._get(f"{BASE}/sapi/v1/margin/allAssets")
    async def all_pairs(self): return await self._get(f"{BASE}/sapi/v1/margin/allPairs")
    async def price_index(self, symbol): return await self._get(f"{BASE}/sapi/v1/margin/priceIndex", {"symbol": symbol})
    async def margin_summary(self): return await self._get(f"{BASE}/sapi/v1/margin/tradeCoeff", signed=True)
    async def force_liquidation_record(self, **kw): return await self._get(f"{BASE}/sapi/v1/margin/forceLiquidationRec", kw, signed=True)
    async def set_max_leverage(self, max_leverage: int): return await self._post(f"{BASE}/sapi/v1/margin/max-leverage", {"maxLeverage": max_leverage})
    async def capital_flow(self, **kw): return await self._get(f"{BASE}/sapi/v1/margin/capital-flow", kw, signed=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 12. ONCHAIN PAY
# ═══════════════════════════════════════════════════════════════════════════════
class OnchainPaySkill(SkillBase):
    skill_name = "onchain-pay"

    async def create_order(self, merchant_trade_no, order_amount, currency, goods_name, **kw):
        return await self._post(f"{BASE}/binancepay/openapi/v3/order",
            {"merchantTradeNo": merchant_trade_no, "orderAmount": order_amount,
             "currency": currency, "goods": {"goodsName": goods_name}, **kw})

    async def query_order(self, merchant_trade_no=None, prepay_id=None):
        p = {}
        if merchant_trade_no: p["merchantTradeNo"] = merchant_trade_no
        if prepay_id: p["prepayId"] = prepay_id
        return await self._post(f"{BASE}/binancepay/openapi/v3/order/query", p)

    async def close_order(self, merchant_trade_no): return await self._post(f"{BASE}/binancepay/openapi/v3/order/close", {"merchantTradeNo": merchant_trade_no})
    async def transfer_fund(self, request_id, currency, amount, transfer_type, **kw):
        return await self._post(f"{BASE}/binancepay/openapi/wallet/transfer", {"requestId": request_id, "currency": currency, "amount": amount, "transferType": transfer_type, **kw})


# ═══════════════════════════════════════════════════════════════════════════════
# 13. P2P
# ═══════════════════════════════════════════════════════════════════════════════
class P2PSkill(SkillBase):
    skill_name = "p2p"

    async def order_history(self, trade_type="BUY", page=1, rows=10, **kw):
        return await self._get(f"{BASE}/sapi/v1/c2c/orderMatch/listUserOrderHistory",
            {"tradeType": trade_type, "page": page, "rows": rows, **kw}, signed=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 14. SIMPLE EARN
# ═══════════════════════════════════════════════════════════════════════════════
class SimpleEarnSkill(SkillBase):
    skill_name = "simple-earn"

    async def flexible_product_list(self, **kw): return await self._get(f"{BASE}/sapi/v1/simple-earn/flexible/list", kw, signed=True)
    async def locked_product_list(self, **kw): return await self._get(f"{BASE}/sapi/v1/simple-earn/locked/list", kw, signed=True)
    async def subscribe_flexible(self, product_id, amount, **kw): return await self._post(f"{BASE}/sapi/v1/simple-earn/flexible/subscribe", {"productId": product_id, "amount": amount, **kw})
    async def redeem_flexible(self, product_id, **kw): return await self._post(f"{BASE}/sapi/v1/simple-earn/flexible/redeem", {"productId": product_id, **kw})
    async def subscribe_locked(self, project_id, amount, **kw): return await self._post(f"{BASE}/sapi/v1/simple-earn/locked/subscribe", {"projectId": project_id, "amount": amount, **kw})
    async def redeem_locked(self, position_id, **kw): return await self._post(f"{BASE}/sapi/v1/simple-earn/locked/redeem", {"positionId": position_id, **kw})
    async def flexible_position(self, **kw): return await self._get(f"{BASE}/sapi/v1/simple-earn/flexible/position", kw, signed=True)
    async def locked_position(self, **kw): return await self._get(f"{BASE}/sapi/v1/simple-earn/locked/position", kw, signed=True)
    async def account(self): return await self._get(f"{BASE}/sapi/v1/simple-earn/account", signed=True)
    async def flexible_rewards_history(self, type_, **kw): return await self._get(f"{BASE}/sapi/v1/simple-earn/flexible/history/rewardsRecord", {"type": type_, **kw}, signed=True)
    async def rate_history(self, product_id, **kw): return await self._get(f"{BASE}/sapi/v1/simple-earn/flexible/history/rateHistory", {"productId": product_id, **kw}, signed=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 15. SPOT (/api/v3/...)
# ═══════════════════════════════════════════════════════════════════════════════
class SpotSkill(SkillBase):
    skill_name = "spot"

    async def ping(self): return await self._get(f"{BASE}/api/v3/ping")
    async def server_time(self): return await self._get(f"{BASE}/api/v3/time")
    async def exchange_info(self, symbol=None): return await self._get(f"{BASE}/api/v3/exchangeInfo", {"symbol": symbol} if symbol else {})
    async def order_book(self, symbol, limit=20): return await self._get(f"{BASE}/api/v3/depth", {"symbol": symbol, "limit": limit})
    async def recent_trades(self, symbol, limit=500): return await self._get(f"{BASE}/api/v3/trades", {"symbol": symbol, "limit": limit})
    async def agg_trades(self, symbol, **kw): return await self._get(f"{BASE}/api/v3/aggTrades", {"symbol": symbol, **kw})
    async def klines(self, symbol, interval="1h", limit=200, **kw): return await self._get(f"{BASE}/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit, **kw})
    async def avg_price(self, symbol): return await self._get(f"{BASE}/api/v3/avgPrice", {"symbol": symbol})
    async def ticker_24hr(self, symbol=None): return await self._get(f"{BASE}/api/v3/ticker/24hr", {"symbol": symbol} if symbol else {})
    async def ticker_price(self, symbol=None): return await self._get(f"{BASE}/api/v3/ticker/price", {"symbol": symbol} if symbol else {})
    async def book_ticker(self, symbol=None): return await self._get(f"{BASE}/api/v3/ticker/bookTicker", {"symbol": symbol} if symbol else {})
    async def account(self, **kw): return await self._get(f"{BASE}/api/v3/account", kw, signed=True)
    async def my_trades(self, symbol, **kw): return await self._get(f"{BASE}/api/v3/myTrades", {"symbol": symbol, **kw}, signed=True)
    async def open_orders(self, symbol=None): return await self._get(f"{BASE}/api/v3/openOrders", {"symbol": symbol} if symbol else {}, signed=True)
    async def all_orders(self, symbol, **kw): return await self._get(f"{BASE}/api/v3/allOrders", {"symbol": symbol, **kw}, signed=True)
    async def new_order(self, symbol, side, type_, new_client_order_id=None, **kw):
        p = {"symbol": symbol, "side": side, "type": type_}
        cid = (new_client_order_id or f"agent-{''.join(__import__('secrets').token_hex(9))}")
        p["newClientOrderId"] = f"agent-{cid}" if not cid.startswith("agent-") else cid
        return await self._post(f"{BASE}/api/v3/order", {**p, **kw})
    async def cancel_order(self, symbol, order_id=None, orig_client_order_id=None):
        p: dict = {"symbol": symbol}
        if order_id: p["orderId"] = order_id
        if orig_client_order_id: p["origClientOrderId"] = orig_client_order_id
        return await self._delete(f"{BASE}/api/v3/order", p)
    async def cancel_replace(self, symbol, side, type_, cancel_replace_mode, **kw):
        return await self._post(f"{BASE}/api/v3/order/cancelReplace", {"symbol": symbol, "side": side, "type": type_, "cancelReplaceMode": cancel_replace_mode, **kw})
    async def new_oco(self, symbol, side, quantity, price, stop_price, **kw):
        return await self._post(f"{BASE}/api/v3/orderList/oco", {"symbol": symbol, "side": side, "quantity": quantity, "aboveType": "LIMIT_MAKER", "belowType": "STOP_LOSS_LIMIT", "abovePrice": price, "belowStopPrice": stop_price, **kw})
    async def rate_limits(self): return await self._get(f"{BASE}/api/v3/rateLimit/order", signed=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 16. SQUARE POST
# ═══════════════════════════════════════════════════════════════════════════════
class SquarePostSkill(SkillBase):
    skill_name = "square-post"

    async def feed(self, **kw):
        try: return await self._get(f"{BASE}/sapi/v1/square/feed", kw, signed=True)
        except Exception: return []


# ═══════════════════════════════════════════════════════════════════════════════
# 17. SUB ACCOUNT
# ═══════════════════════════════════════════════════════════════════════════════
class SubAccountSkill(SkillBase):
    skill_name = "sub-account"

    async def list_sub_accounts(self, **kw): return await self._get(f"{BASE}/sapi/v1/sub-account/list", kw, signed=True)
    async def create_sub_account(self, tag="bot"): return await self._post(f"{BASE}/sapi/v1/sub-account/virtualSubAccount", {"subAccountString": tag})
    async def sub_account_assets(self, email): return await self._get(f"{BASE}/sapi/v3/sub-account/assets", {"email": email}, signed=True)
    async def sub_account_balance(self, email): return await self._get(f"{BASE}/sapi/v4/sub-account/assets", {"email": email}, signed=True)
    async def universal_transfer(self, from_account_type, to_account_type, asset, amount, **kw):
        return await self._post(f"{BASE}/sapi/v1/sub-account/universalTransfer", {"fromAccountType": from_account_type, "toAccountType": to_account_type, "asset": asset, "amount": amount, **kw})
    async def transfer_history(self, **kw): return await self._get(f"{BASE}/sapi/v1/sub-account/transfer/subUserHistory", kw, signed=True)
    async def spot_summary(self): return await self._get(f"{BASE}/sapi/v1/sub-account/spotSummary", signed=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 18. VIP LOAN
# ═══════════════════════════════════════════════════════════════════════════════
class VipLoanSkill(SkillBase):
    skill_name = "vip-loan"

    async def ongoing_orders(self, **kw): return await self._get(f"{BASE}/sapi/v1/loan/vip/ongoing/orders", kw, signed=True)
    async def borrow(self, loan_coin, loan_amount, collateral_coin, collateral_amount):
        return await self._post(f"{BASE}/sapi/v1/loan/vip/borrow", {"loanCoin": loan_coin, "loanAmount": loan_amount, "collateralCoin": collateral_coin, "collateralAmount": collateral_amount})
    async def repay(self, order_id, amount): return await self._post(f"{BASE}/sapi/v1/loan/vip/repay", {"orderId": order_id, "amount": amount})
    async def collateral_asset_data(self, **kw): return await self._get(f"{BASE}/sapi/v1/loan/vip/collateral/data", kw)
    async def loanable_data(self, **kw): return await self._get(f"{BASE}/sapi/v1/loan/vip/loanable/data", kw)
    async def repay_history(self, **kw): return await self._get(f"{BASE}/sapi/v1/loan/vip/repay/history", kw, signed=True)
    async def borrow_history(self, **kw): return await self._get(f"{BASE}/sapi/v1/loan/vip/request/data", kw, signed=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 19-25. BINANCE-WEB3 SKILLS
# ═══════════════════════════════════════════════════════════════════════════════
class TokenizedSecuritiesSkill(SkillBase):
    skill_name = "binance-tokenized-securities-info"
    async def list_securities(self, **kw): return await self._get(f"{BASE}/sapi/v1/rts/list", kw)
    async def security_detail(self, symbol): return await self._get(f"{BASE}/sapi/v1/rts/detail", {"symbol": symbol})


class CryptoMarketRankSkill(SkillBase):
    skill_name = "crypto-market-rank"
    _CG = "https://api.coingecko.com/api/v3"
    async def market_rank(self, limit=20, vs="usd"):
        return await self._get(f"{self._CG}/coins/markets", {"vs_currency": vs, "order": "market_cap_desc", "per_page": limit, "page": 1})
    async def trending(self):
        d = await self._get(f"{self._CG}/search/trending"); return d.get("coins", [])
    async def global_data(self): return await self._get(f"{self._CG}/global")
    async def coin_detail(self, coin_id): return await self._get(f"{self._CG}/coins/{coin_id}")


class MemeRushSkill(SkillBase):
    skill_name = "meme-rush"
    async def tokens(self, **kw):
        try: return await self._get(f"{BASE}/sapi/v1/meme/tokens", kw)
        except Exception: return []
    async def leaderboard(self, **kw):
        try: return await self._get(f"{BASE}/sapi/v1/meme/leaderboard", kw)
        except Exception: return []


class QueryAddressInfoSkill(SkillBase):
    skill_name = "query-address-info"
    async def query(self, address, chain="ETH"):
        try: return await self._get(f"{BASE}/sapi/v1/web3/address", {"address": address, "chain": chain}, signed=True)
        except Exception: return {"address": address, "chain": chain, "status": "unavailable"}


class QueryTokenAuditSkill(SkillBase):
    skill_name = "query-token-audit"
    async def audit(self, contract_address, chain="ETH"):
        try: return await self._get(f"{BASE}/sapi/v1/web3/token/audit", {"contractAddress": contract_address, "chain": chain})
        except Exception: return {"contract": contract_address, "status": "unavailable"}


class QueryTokenInfoSkill(SkillBase):
    skill_name = "query-token-info"
    _DS = "https://api.dexscreener.com/latest/dex"
    async def token_info(self, contract_address):
        return await self._get(f"{self._DS}/tokens/{contract_address}")
    async def token_price(self, contract_address) -> float:
        d = await self.token_info(contract_address)
        pairs = d.get("pairs") or []
        return float(pairs[0]["priceUsd"]) if pairs else 0.0
    async def pairs_by_token(self, token_address):
        return await self._get(f"{self._DS}/tokens/{token_address}")


class TradingSignalSkill(SkillBase):
    skill_name = "trading-signal"
    async def signals(self, limit=10):
        try: return await self._get(f"{BASE}/sapi/v1/trading/signal", {"limit": limit})
        except Exception: return []
    async def signal_by_symbol(self, symbol):
        try: return await self._get(f"{BASE}/sapi/v1/trading/signal/symbol", {"symbol": symbol})
        except Exception: return {}


# ═══════════════════════════════════════════════════════════════════════════════
# SKILL REGISTRY  — import ALL skills as `skills["name"]`
# ═══════════════════════════════════════════════════════════════════════════════
def load_all_skills() -> dict[str, SkillBase]:
    return {
        "algo":                          AlgoSkill(),
        "alpha":                         AlphaSkill(),
        "assets":                        AssetsSkill(),
        "convert":                       ConvertSkill(),
        "derivatives_coin_futures":      DerivativesCoinFuturesSkill(),
        "derivatives_options":           DerivativesOptionsSkill(),
        "derivatives_portfolio_margin":  DerivativesPortfolioMarginSkill(),
        "derivatives_portfolio_margin_pro": DerivativesPortfolioMarginProSkill(),
        "derivatives_usds_futures":      DerivativesUSDSFuturesSkill(),
        "fiat":                          FiatSkill(),
        "margin_trading":                MarginTradingSkill(),
        "onchain_pay":                   OnchainPaySkill(),
        "p2p":                           P2PSkill(),
        "simple_earn":                   SimpleEarnSkill(),
        "spot":                          SpotSkill(),
        "square_post":                   SquarePostSkill(),
        "sub_account":                   SubAccountSkill(),
        "vip_loan":                      VipLoanSkill(),
        "tokenized_securities":          TokenizedSecuritiesSkill(),
        "crypto_market_rank":            CryptoMarketRankSkill(),
        "meme_rush":                     MemeRushSkill(),
        "query_address_info":            QueryAddressInfoSkill(),
        "query_token_audit":             QueryTokenAuditSkill(),
        "query_token_info":              QueryTokenInfoSkill(),
        "trading_signal":                TradingSignalSkill(),
    }

# Singleton — import this everywhere
SKILLS: dict[str, SkillBase] = load_all_skills()
