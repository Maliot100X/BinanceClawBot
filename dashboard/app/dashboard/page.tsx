'use client'
import { useEffect } from 'react'
import { useBotStore } from '@/store/botStore'
import { motion } from 'framer-motion'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import toast from 'react-hot-toast'
import { useSession } from 'next-auth/react'
import Link from 'next/link'

function Card({ title, value, sub, icon, color='#00ff88' }: any) {
  return (
    <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}}
      style={{ background:`${color}08`, border:`1px solid ${color}22`, borderRadius:'16px', padding:'20px' }}>
      <div style={{ display:'flex', alignItems:'center', gap:'8px', marginBottom:'6px' }}>
        <span style={{ fontSize:'18px' }}>{icon}</span>
        <span style={{ color:'#475569', fontSize:'0.75rem', textTransform:'uppercase', letterSpacing:'0.1em' }}>{title}</span>
      </div>
      <div style={{ color, fontSize:'1.6rem', fontWeight:800 }}>{value}</div>
      {sub && <div style={{ color:'#475569', fontSize:'0.75rem', marginTop:'4px' }}>{sub}</div>}
    </motion.div>
  )
}

const genChart = () => Array.from({length:24},(_,i)=>({h:`${i}h`, v:60000+Math.random()*4000-2000}))

export default function DashboardPage() {
  const { data: session } = useSession()
  const { 
    isRunning, 
    startBot, 
    stopBot, 
    fetchStatus, 
    status, 
    cliConnected, 
    fetchCliStatus,
    binanceKey,
    portfolio,
    fetchPortfolio,
    positions,
    fetchPositions,
    signals,
    fetchSignals 
  } = useBotStore()

  useEffect(() => {
    fetchStatus()
    fetchCliStatus()
    fetchPortfolio()
    fetchPositions()
    fetchSignals()
    const interval = setInterval(() => {
      fetchStatus()
      fetchCliStatus()
      fetchSignals()
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const isBrainConnected = !!session || cliConnected
  const isBinanceReady = binanceKey && binanceKey !== "Missing"
  const canStartBot = isBrainConnected && isBinanceReady

  const handleStart = async () => {
    if (!isBrainConnected) { toast.error('Please Connect Brain first!'); return }
    try { await startBot(); toast.success('✅ Bot started — scanning every 30s') }
    catch { toast.error('Failed to start — is main.py running?') }
  }
  const handleStop = async () => {
    if (!isBrainConnected) return
    try { await stopBot(); toast.success('⏹ Bot stopped') }
    catch { toast.error('Failed to stop bot') }
  }

  const usdt = portfolio?.balances?.find((b:any) => b.asset === 'USDT')?.free || '0'
  const totalPnl = portfolio?.daily_pnl || 0

  return (
    <div style={{ position:'relative' }}>
      {!isBrainConnected && (
        <div style={{ 
          position:'absolute', top:0, left:0, right:0, bottom:0, 
          background:'rgba(2,4,8,0.7)', backdropFilter:'blur(8px)', zIndex:50,
          display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
          borderRadius:'24px', border:'1px solid rgba(0,255,136,0.2)', padding:'20px'
        }}>
          <motion.div initial={{scale:0.9, opacity:0}} animate={{scale:1, opacity:1}}
            style={{ textAlign:'center', background:'#0f172a', padding:'40px', borderRadius:'24px', border:'1px solid #00ff8833', boxShadow:'0 20px 50px rgba(0,0,0,0.5)' }}>
            <div style={{ fontSize:'64px', marginBottom:'24px' }}>🛡️</div>
            <h2 style={{ color:'white', marginBottom:'8px', fontSize:'1.8rem' }}>AI Brain Required</h2>
            <p style={{ color:'#94a3b8', maxWidth:'350px', marginBottom:'32px', fontSize:'1rem', lineHeight:1.6 }}>
              You are currently in <b>Preview Mode</b>. Connect your AI Brain (OpenAI Codex, Gemini, or Antigravity) to enable live signals and automated trading.
            </p>
            <Link href="/login" style={{ 
              padding:'14px 40px', borderRadius:'14px', background:'#00ff88', color:'#020408', 
              textDecoration:'none', fontWeight:800, fontSize:'1.1rem', display:'inline-block',
              boxShadow:'0 0 20px rgba(0,255,136,0.3)'
            }}>
              Connect Now 🧠
            </Link>
          </motion.div>
        </div>
      )}

      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:'32px', opacity: isBrainConnected?1:0.4 }}>
        <div>
          <h1 style={{ color:'white', fontSize:'1.8rem', fontWeight:800, margin:0 }}>📊 Dashboard Summary</h1>
          <p style={{ color:'#64748b', fontSize:'0.9rem', marginTop:'6px' }}>
            {!isBrainConnected ? 'Guest Preview Mode • KaiNova Simulation' : 
             !isBinanceReady ? '⚠️ Binance Keys Missing (Check .env)' : 
             status ? `✅ Engine Active • Binance: ${binanceKey}` : '⚠️ Backend offline'}
          </p>
        </div>
        <div style={{ display:'flex', gap:'12px' }}>
          <button onClick={handleStart} disabled={!canStartBot} style={{ 
            padding:'12px 24px', borderRadius:'12px', border:`1px solid ${canStartBot ? 'rgba(0,255,136,0.3)' : 'rgba(148,163,184,0.3)'}`, 
            background: canStartBot ? 'rgba(0,255,136,0.1)' : 'rgba(148,163,184,0.05)', 
            color: canStartBot ? '#00ff88' : '#94a3b8', 
            cursor: canStartBot ? 'pointer' : 'not-allowed', 
            fontWeight: 700, fontSize:'0.85rem' 
          }}>
            ▶ Start Bot
          </button>
          <button onClick={handleStop} disabled={!canStartBot} style={{ 
            padding:'12px 24px', borderRadius:'12px', border:`1px solid ${canStartBot ? 'rgba(255,68,85,0.3)' : 'rgba(148,163,184,0.3)'}`, 
            background: canStartBot ? 'rgba(255,68,85,0.1)' : 'rgba(148,163,184,0.05)', 
            color: canStartBot ? '#ff4455' : '#94a3b8', 
            cursor: canStartBot ? 'pointer' : 'not-allowed', 
            fontWeight: 700, fontSize:'0.85rem' 
          }}>
            ⏹ Stop Bot
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))', gap:'20px', marginBottom:'32px', opacity: session?1:0.4 }}>
        <Card title="USDT Balance" value={`$${parseFloat(usdt).toLocaleString('en',{maximumFractionDigits:2})}`} sub="Available" icon="💰" color="#00ff88"/>
        <Card title="Daily PnL" value={`${totalPnl >= 0?'+':''}${totalPnl.toFixed(2)}%`} icon="📈" color={totalPnl>=0?'#00ff88':'#ff4455'}/>
        <Card title="Open Positions" value={positions.length} sub={positions.map((p:any)=>p.symbol).join(' · ')||'None'} icon="📋" color="#a855f7"/>
        <Card title="Bot Status" value={isRunning?'LIVE 🟢':'STOPPED 🔴'} sub="30s scan interval" icon="⚡" color={isRunning?'#00ff88':'#ff4455'}/>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'1.5fr 1fr', gap:'24px', opacity: session?1:0.4 }}>
        <div style={{ background:'rgba(0,255,136,0.03)', border:'1px solid rgba(0,255,136,0.1)', borderRadius:'20px', padding:'24px' }}>
          <div style={{ display:'flex', justifyContent:'space-between', marginBottom:'20px' }}>
            <h2 style={{ color:'#00ff88', fontWeight:700, fontSize:'1.1rem', margin:0 }}>BTC/USDT Performance</h2>
            <span style={{ color:'#64748b', fontSize:'0.8rem' }}>Live Stream</span>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={genChart()}>
              <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#00ff88" stopOpacity={0.2}/><stop offset="95%" stopColor="#00ff88" stopOpacity={0}/></linearGradient></defs>
              <XAxis dataKey="h" tick={{ fill:'#475569', fontSize:10 }} axisLine={false} tickLine={false}/>
              <YAxis domain={['dataMin-100','dataMax+100']} hide/>
              <Tooltip contentStyle={{ background:'#0f172a', border:'1px solid #00ff8822', borderRadius:'12px' }} formatter={(v:number)=>`$${v.toFixed(0)}`}/>
              <Area type="monotone" dataKey="v" stroke="#00ff88" fill="url(#g)" strokeWidth={3}/>
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div style={{ background:'rgba(0,212,255,0.03)', border:'1px solid rgba(0,212,255,0.1)', borderRadius:'20px', padding:'24px' }}>
          <h2 style={{ color:'#00d4ff', fontWeight:700, fontSize:'1.1rem', marginBottom:'20px', margin:0 }}>📡 Intelligence Signals</h2>
          {signals.length === 0 ? (
            <div style={{ color:'#64748b', textAlign:'center', padding:'60px 0', fontSize:'0.9rem' }}>Waiting for system scan...</div>
          ) : signals.slice(0,6).map((s:any, i:number) => (
            <div key={i} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'14px 0', borderBottom:'1px solid rgba(255,255,255,0.05)' }}>
              <span style={{ color:'white', fontWeight:600, fontSize:'0.9rem' }}>{s.symbol}</span>
              <span style={{ fontSize:'0.75rem', padding:'4px 12px', borderRadius:'20px',
                background: s.signal==='BUY'?'rgba(0,255,136,0.1)': s.signal==='SELL'?'rgba(255,68,85,0.1)':'rgba(250,204,21,0.1)',
                color: s.signal==='BUY'?'#00ff88': s.signal==='SELL'?'#ff4455':'#facc15', fontWeight:700 }}>{s.signal}</span>
              <span style={{ color:'#64748b', fontSize:'0.85rem' }}>{s.confidence?.toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>
      {/* ── Floating Guide Bot ───────────────────────────────────────────── */}
      <motion.div 
        drag
        whileHover={{ scale: 1.1 }}
        style={{ 
          position:'fixed', bottom:'30px', right:'30px', zIndex:100,
          width:'64px', height:'64px', borderRadius:'32px',
          background:'linear-gradient(135deg, #00ff88 0%, #00ccff 100%)',
          display:'flex', alignItems:'center', justifyContent:'center',
          fontSize:'32px', boxShadow:'0 10px 30px rgba(0,255,136,0.4)',
          cursor:'pointer', border:'2px solid rgba(2,4,8,0.5)'
        }}
        onClick={() => toast('🤖 KaiNova: "The Brain is 100% active. Use /ai in Telegram or the Chat here to trade!"')}
      >
        🧠
        <motion.div 
          animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
          style={{ position:'absolute', width:'100%', height:'100%', borderRadius:'32px', border:'2px solid #00ff88' }}
        />
      </motion.div>
    </div>
  )
}
