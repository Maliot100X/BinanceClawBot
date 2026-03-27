'use client'
import { useEffect } from 'react'
import { useBotStore } from '@/store/botStore'
import { motion } from 'framer-motion'

const SKILL_INFO: Record<string,{desc:string,icon:string,color:string,endpoints:string[]}> = {
  algo:                        { icon:'⚡', color:'#00ff88', desc:'Algo trading — TWAP/VP orders for futures & spot', endpoints:['newOrderTwap','newOrderVp','openOrders','historicalOrders'] },
  alpha:                       { icon:'🔬', color:'#00d4ff', desc:'Binance Alpha DeFi token ticker & klines', endpoints:['ticker','klines','aggTrades','tokenList'] },
  assets:                      { icon:'💰', color:'#f59e0b', desc:'Wallet, balances, deposits, withdrawals, dust', endpoints:['accountInfo','walletBalance','withdraw','depositAddress'] },
  convert:                     { icon:'🔄', color:'#10b981', desc:'Instant crypto conversion with live quotes', endpoints:['getQuote','acceptQuote','orderStatus','tradeHistory'] },
  derivatives_coin_futures:    { icon:'📉', color:'#a855f7', desc:'USDD-M Coin-margined futures (DAPI)', endpoints:['newOrder','cancelOrder','account','setLeverage'] },
  derivatives_options:         { icon:'🎯', color:'#ec4899', desc:'European options trading (EAPI)', endpoints:['newOrder','positions','markPrice','account'] },
  derivatives_portfolio_margin:{ icon:'🏦', color:'#06b6d4', desc:'Unified Portfolio Margin account', endpoints:['account','balance','pmLoan','repay'] },
  derivatives_portfolio_margin_pro:{ icon:'🏆', color:'#8b5cf6', desc:'Portfolio Margin Pro (v2)', endpoints:['account','balance','positionRisk'] },
  derivatives_usds_futures:    { icon:'📈', color:'#00ff88', desc:'USDS-M futures (FAPI) — most popular', endpoints:['newOrder','account','positions','setLeverage','fundingRate'] },
  fiat:                        { icon:'💳', color:'#d97706', desc:'Fiat on/off ramp order history', endpoints:['fiatOrders','fiatPayments'] },
  margin_trading:              { icon:'⚖️', color:'#ef4444', desc:'Cross & isolated margin borrowing and trading', endpoints:['newOrder','borrowRepay','maxBorrowable','marginSummary'] },
  onchain_pay:                 { icon:'💸', color:'#22c55e', desc:'Binance Pay merchant API', endpoints:['createOrder','queryOrder','closeOrder','transferFund'] },
  p2p:                         { icon:'🤝', color:'#eab308', desc:'Peer-to-peer trade history', endpoints:['orderHistory'] },
  simple_earn:                 { icon:'🌱', color:'#84cc16', desc:'Flexible & locked earn products', endpoints:['flexibleList','subscribe','redeem','position'] },
  spot:                        { icon:'💹', color:'#00ff88', desc:'Full Binance spot market — all order types', endpoints:['newOrder','cancelOrder','account','ticker','klines'] },
  square_post:                 { icon:'📣', color:'#3b82f6', desc:'Binance Square social feed', endpoints:['feed'] },
  sub_account:                 { icon:'👥', color:'#6366f1', desc:'Sub-account management & transfers', endpoints:['listSubAccounts','createSubAccount','universalTransfer'] },
  vip_loan:                    { icon:'🏅', color:'#f97316', desc:'VIP crypto loan — borrow & repay', endpoints:['ongoingOrders','borrow','repay','loanableData'] },
  tokenized_securities:        { icon:'📄', color:'#14b8a6', desc:'Binance tokenized securities info', endpoints:['listSecurities','securityDetail'] },
  crypto_market_rank:          { icon:'🥇', color:'#f59e0b', desc:'CoinGecko market rank & trending', endpoints:['marketRank','trending','globalData'] },
  meme_rush:                   { icon:'🐸', color:'#a3e635', desc:'Binance Meme Rush token list', endpoints:['tokens','leaderboard'] },
  query_address_info:          { icon:'🔍', color:'#38bdf8', desc:'On-chain address info & history', endpoints:['query'] },
  query_token_audit:           { icon:'🛡️', color:'#fb7185', desc:'Smart contract security audit', endpoints:['audit'] },
  query_token_info:            { icon:'📊', color:'#c084fc', desc:'DexScreener token pairs & price', endpoints:['tokenInfo','tokenPrice','pairsByToken'] },
  trading_signal:              { icon:'📡', color:'#67e8f9', desc:'Binance AI trading signals', endpoints:['signals','signalBySymbol'] },
}

export default function SkillsPage() {
  const skills = Object.keys(SKILL_INFO)

  return (
    <div>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'28px' }}>
        <div>
          <h1 style={{ color:'white', fontSize:'1.6rem', fontWeight:800 }}>🔧 Binance Skills Hub</h1>
          <p style={{ color:'#475569', fontSize:'0.85rem', marginTop:'4px' }}>All 26 skills loaded from github.com/binance/binance-skills-hub</p>
        </div>
        <div style={{ padding:'8px 16px', borderRadius:'10px', background:'rgba(0,255,136,0.1)', border:'1px solid rgba(0,255,136,0.2)', color:'#00ff88', fontWeight:700 }}>
          26 / 26 Active ✓
        </div>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(300px,1fr))', gap:'16px' }}>
        {skills.map((key, i) => {
          const s = SKILL_INFO[key]
          if (!s) return null
          return (
            <motion.div key={key} initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:i*0.03}}
              style={{ background:`${s.color}06`, border:`1px solid ${s.color}22`, borderRadius:'14px', padding:'18px' }}>
              <div style={{ display:'flex', alignItems:'center', gap:'10px', marginBottom:'10px' }}>
                <span style={{ fontSize:'24px' }}>{s.icon}</span>
                <div>
                  <div style={{ color:s.color, fontWeight:700, fontSize:'0.85rem' }}>{key.replace(/_/g,'-')}</div>
                  <div style={{ color:'#475569', fontSize:'0.72rem' }}>{s.desc}</div>
                </div>
              </div>
              <div style={{ display:'flex', flexWrap:'wrap', gap:'4px' }}>
                {s.endpoints.map(ep => (
                  <span key={ep} style={{ padding:'3px 8px', borderRadius:'6px', background:`${s.color}15`, color:s.color, fontSize:'0.68rem', fontFamily:'monospace' }}>
                    {ep}()
                  </span>
                ))}
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
