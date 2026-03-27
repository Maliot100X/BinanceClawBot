'use client'
import { useEffect } from 'react'
import { useBotStore } from '@/store/botStore'
import { motion } from 'framer-motion'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import toast from 'react-hot-toast'

const genChart = () => Array.from({length:24},(_,i)=>({h:`${i}h`, v:60000+Math.random()*4000-2000}))

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

export default function DashboardPage() {
  const { status, isRunning, fetchStatus, fetchPortfolio, portfolio, fetchSignals, signals, startBot, stopBot, fetchPositions, positions } = useBotStore()

  useEffect(() => {
    fetchStatus(); fetchPortfolio(); fetchSignals(); fetchPositions()
    const interval = setInterval(() => { fetchStatus(); fetchSignals() }, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleStart = async () => {
    try { await startBot(); toast.success('✅ Bot started — scanning every 30s') }
    catch { toast.error('Failed to start — is main.py running?') }
  }
  const handleStop = async () => {
    try { await stopBot(); toast.success('⏹ Bot stopped') }
    catch { toast.error('Failed to stop bot') }
  }

  const usdt = portfolio?.balances?.find((b:any) => b.asset === 'USDT')?.free || '0'
  const totalPnl = portfolio?.daily_pnl || 0

  return (
    <div>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:'28px' }}>
        <div>
          <h1 style={{ color:'white', fontSize:'1.6rem', fontWeight:800 }}>📊 Dashboard</h1>
          <p style={{ color:'#475569', fontSize:'0.85rem', marginTop:'4px' }}>
            {status ? 'Backend connected' : '⚠️ Backend offline — run python main.py'}
          </p>
        </div>
        <div style={{ display:'flex', gap:'10px' }}>
          <button onClick={handleStart} style={{ padding:'10px 20px', borderRadius:'10px', border:'1px solid rgba(0,255,136,0.3)', background:'rgba(0,255,136,0.1)', color:'#00ff88', cursor:'pointer', fontWeight:600, fontSize:'0.85rem' }}>
            ▶ Start Bot
          </button>
          <button onClick={handleStop} style={{ padding:'10px 20px', borderRadius:'10px', border:'1px solid rgba(255,68,85,0.3)', background:'rgba(255,68,85,0.1)', color:'#ff4455', cursor:'pointer', fontWeight:600, fontSize:'0.85rem' }}>
            ⏹ Stop Bot
          </button>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(180px,1fr))', gap:'16px', marginBottom:'28px' }}>
        <Card title="USDT Balance" value={`$${parseFloat(usdt).toLocaleString('en',{maximumFractionDigits:2})}`} sub="Available" icon="💰" color="#00ff88"/>
        <Card title="Daily PnL" value={`${totalPnl >= 0?'+':''}${totalPnl.toFixed(2)}%`} icon="📈" color={totalPnl>=0?'#00ff88':'#ff4455'}/>
        <Card title="Open Positions" value={positions.length} sub={positions.map((p:any)=>p.symbol).join(' · ')||'None'} icon="📋" color="#a855f7"/>
        <Card title="Bot Status" value={isRunning?'LIVE 🟢':'STOPPED 🔴'} sub="30s scan interval" icon="⚡" color={isRunning?'#00ff88':'#ff4455'}/>
        <Card title="Active Skills" value="26" sub="All Binance skills loaded" icon="🔧" color="#f59e0b"/>
        <Card title="Signals Today" value={signals.length} sub="Analyzed" icon="📡" color="#00d4ff"/>
      </div>

      {/* Chart + Live Signals */}
      <div style={{ display:'grid', gridTemplateColumns:'1.5fr 1fr', gap:'20px' }}>
        <div style={{ background:'rgba(0,255,136,0.04)', border:'1px solid rgba(0,255,136,0.1)', borderRadius:'16px', padding:'24px' }}>
          <div style={{ display:'flex', justifyContent:'space-between', marginBottom:'16px' }}>
            <h2 style={{ color:'#00ff88', fontWeight:700 }}>BTC/USDT — 24h</h2>
            <span style={{ color:'#475569', fontSize:'0.8rem' }}>Live</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={genChart()}>
              <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#00ff88" stopOpacity={0.3}/><stop offset="95%" stopColor="#00ff88" stopOpacity={0}/></linearGradient></defs>
              <XAxis dataKey="h" tick={{ fill:'#475569', fontSize:10 }}/>
              <YAxis domain={['dataMin-200','dataMax+200']} tick={{ fill:'#475569', fontSize:10 }}/>
              <Tooltip contentStyle={{ background:'#0f172a', border:'1px solid #00ff8833', borderRadius:'8px' }} formatter={(v:number)=>`$${v.toFixed(0)}`}/>
              <Area type="monotone" dataKey="v" stroke="#00ff88" fill="url(#g)" strokeWidth={2}/>
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div style={{ background:'rgba(0,212,255,0.04)', border:'1px solid rgba(0,212,255,0.1)', borderRadius:'16px', padding:'24px' }}>
          <h2 style={{ color:'#00d4ff', fontWeight:700, marginBottom:'16px' }}>📡 Latest Signals</h2>
          {signals.length === 0 ? (
            <div style={{ color:'#475569', textAlign:'center', padding:'30px 0' }}>No signals yet — start the bot or click Scan</div>
          ) : signals.slice(0,6).map((s:any, i:number) => (
            <div key={i} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'10px 0', borderBottom:'1px solid rgba(255,255,255,0.05)' }}>
              <span style={{ color:'white', fontWeight:600, fontSize:'0.85rem' }}>{s.symbol}</span>
              <span style={{ fontSize:'0.8rem', padding:'3px 10px', borderRadius:'20px',
                background: s.signal==='BUY'?'rgba(0,255,136,0.1)': s.signal==='SELL'?'rgba(255,68,85,0.1)':'rgba(250,204,21,0.1)',
                color: s.signal==='BUY'?'#00ff88': s.signal==='SELL'?'#ff4455':'#facc15', fontWeight:600 }}>{s.signal}</span>
              <span style={{ color:'#475569', fontSize:'0.8rem' }}>{s.confidence?.toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
