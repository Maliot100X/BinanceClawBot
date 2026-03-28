"use client"
import { useEffect, useState } from 'react'
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

  const [isChatOpen, setIsChatOpen] = useState(false)
  const [chatMsg, setChatMsg] = useState('')
  const [messages, setMessages] = useState<{role:'user'|'ai', content:string}[]>([])
  const [isTyping, setIsTyping] = useState(false)

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

  const handleSend = async () => {
    if (!chatMsg.trim()) return
    const userText = chatMsg
    setChatMsg('')
    setMessages(prev => [...prev, { role: 'user', content: userText }])
    setIsTyping(true)
    
    try {
      const resp = await fetch('/api/bot/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userText })
      })
      const data = await resp.json()
      setMessages(prev => [...prev, { role: 'ai', content: data.reply }])
    } catch (err) {
      toast.error('AI Connection Failed')
    } finally {
      setIsTyping(false)
    }
  }

  const usdt = portfolio?.balances?.find((b:any) => b.asset === 'USDT')?.free || '0'
  const totalPnl = portfolio?.daily_pnl || 0
 
  return (
    <>
      <div style={{ position:'relative', minHeight:'100vh', paddingBottom:'100px' }}>
        {!isBrainConnected && (
          <div style={{ 
            position:'absolute', top:0, left:0, right:0, bottom:0, 
            background:'rgba(2,4,8,0.9)', backdropFilter:'blur(15px)', zIndex:50,
            display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
            borderRadius:'24px', border:'1px solid rgba(0,255,136,0.2)', padding:'20px'
          }}>
            <motion.div initial={{scale:0.95, opacity:0}} animate={{scale:1, opacity:1}}
              style={{ textAlign:'center', background:'#0f172a', padding:'50px', borderRadius:'32px', border:'1px solid #00ff8833', boxShadow:'0 50px 100px rgba(0,0,0,0.8)' }}>
              <div style={{ fontSize:'72px', marginBottom:'32px' }}>🛡️</div>
              <h2 style={{ color:'white', marginBottom:'12px', fontSize:'2.2rem', fontWeight:900 }}>AI BRAIN REQUIRED</h2>
              <p style={{ color:'#94a3b8', maxWidth:'420px', marginBottom:'40px', fontSize:'1.1rem', lineHeight:1.7 }}>
                KaiNova is currently in <b>Safe Mode</b>. Connect your AI Brain via CLI to unlock live autonomous trading.
              </p>
              <Link href="/login" style={{ 
                padding:'18px 50px', borderRadius:'18px', background:'linear-gradient(135deg, #00ff88 0%, #00ccff 100%)', color:'#020617', 
                textDecoration:'none', fontWeight:900, fontSize:'1.2rem', display:'inline-block',
                boxShadow:'0 0 40px rgba(0,255,136,0.5)', transition:'0.3s'
              }}>
                CONNECT BRAIN 🧠
              </Link>
            </motion.div>
          </div>
        )}

        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:'32px', opacity: isBrainConnected?1:0.3 }}>
          <div>
            <h1 style={{ color:'white', fontSize:'1.8rem', fontWeight:800, margin:0 }}>📊 Dashboard Summary</h1>
            <p style={{ color:'#64748b', fontSize:'0.9rem', marginTop:'6px' }}>
              {!isBrainConnected ? 'Guest Preview Mode • KaiNova Simulation' : 
               !isBinanceReady ? '⚠️ BINANCE KEYS MISSING (Check .env in root)' : 
               status ? `✅ ENGINE LIVE • BINANCE: ${binanceKey}` : '🔄 Syncing Engine...'}
            </p>
          </div>
          <div style={{ display:'flex', gap:'12px' }}>
            <button onClick={handleStart} disabled={!canStartBot} style={{ 
              padding:'14px 32px', borderRadius:'16px', border:`1px solid ${canStartBot ? '#00ff88' : '#334155'}`, 
              background: canStartBot ? 'rgba(0,255,136,0.15)' : 'rgba(51,65,85,0.05)', 
              color: canStartBot ? '#00ff88' : '#475569', 
              cursor: canStartBot ? 'pointer' : 'not-allowed', 
              fontWeight: 900, fontSize:'0.9rem', textTransform:'uppercase', letterSpacing:'1px'
            }}>
              ▶ START BOT
            </button>
            <button onClick={handleStop} disabled={!isRunning} style={{ 
              padding:'14px 32px', borderRadius:'16px', border:`1px solid ${isRunning ? '#ff4455' : '#334155'}`, 
              background: isRunning ? 'rgba(255,68,85,0.15)' : 'rgba(51,65,85,0.05)', 
              color: isRunning ? '#ff4455' : '#475569', 
              cursor: isRunning ? 'pointer' : 'not-allowed', 
              fontWeight: 900, fontSize:'0.9rem', textTransform:'uppercase', letterSpacing:'1px'
            }}>
              ⏹ STOP BOT
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))', gap:'20px', marginBottom:'32px', opacity: isBrainConnected?1:0.4 }}>
          <Card title="USDT Balance" value={`$${parseFloat(usdt).toLocaleString('en',{maximumFractionDigits:2})}`} sub="Available" icon="💰" color="#00ff88"/>
          <Card title="Daily PnL" value={`${totalPnl >= 0?'+':''}${totalPnl.toFixed(2)}%`} icon="📈" color={totalPnl>=0?'#00ff88':'#ff4455'}/>
          <Card title="Open Positions" value={positions.length} sub={positions.map((p:any)=>p.symbol).join(' · ')||'None'} icon="📋" color="#a855f7"/>
          <Card title="Bot Status" value={isRunning?'LIVE 🟢':'STOPPED 🔴'} sub="30s scan interval" icon="⚡" color={isRunning?'#00ff88':'#ff4455'}/>
        </div>

        <div style={{ display:'grid', gridTemplateColumns:'1.5fr 1fr', gap:'24px', opacity: isBrainConnected?1:0.4 }}>
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

        {/* ── Consolidated BrainChat UI ────────────────────────────────────── */}
        <div style={{ position:'fixed', bottom:'30px', right:'30px', zIndex:9999 }}>
          {isChatOpen && (
            <motion.div initial={{ opacity:0, y:20, scale:0.9 }} animate={{ opacity:1, y:0, scale:1 }}
              style={{ 
                width:'380px', height:'520px', background:'rgba(15,23,42,0.95)', backdropFilter:'blur(20px)',
                borderRadius:'24px', border:'1px solid rgba(0,255,136,0.2)', marginBottom:'20px',
                display:'flex', flexDirection:'column', boxShadow:'0 20px 80px rgba(0,0,0,0.8)', overflow:'hidden'
              }}>
              <div style={{ background:'rgba(0,255,136,0.1)', padding:'15px 20px', borderBottom:'1px solid rgba(0,255,136,0.1)', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                <div style={{ color:'#00ff88', fontWeight:800, fontSize:'0.9rem', display:'flex', alignItems:'center', gap:'8px' }}>
                  <motion.div animate={{ opacity:[1,0.5,1] }} transition={{repeat:Infinity, duration:1.5}} style={{width:'8px', height:'8px', borderRadius:'50%', background:'#00ff88'}}/>
                  KAINOVA BRAIN
                </div>
                <button onClick={()=>setIsChatOpen(false)} style={{ background:'none', border:'none', color:'#64748b', cursor:'pointer' }}>✕</button>
              </div>

              <div style={{ flex:1, padding:'20px', overflowY:'auto', display:'flex', flexDirection:'column', gap:'12px' }}>
                <div style={{ background:'rgba(0,255,136,0.05)', padding:'12px', borderRadius:'12px', border:'1px solid rgba(0,255,136,0.1)', color:'#94a3b8', fontSize:'0.85rem' }}>
                  {isBrainConnected ? '🟢 Intelligence synchronized. I have full access to your 26 Binance Skills, Mobula, and CoinGecko.' : '🔴 Brain Offline. Run "py provider_setup.py" to connect.'}
                </div>
                
                {messages.map((m, i) => (
                  <div key={i} style={{ 
                    alignSelf: m.role==='user'?'flex-end':'flex-start',
                    maxWidth:'85%', padding:'10px 14px', borderRadius:'16px',
                    background: m.role==='user'?'#00ff8822':'#1e293b',
                    border: m.role==='user'?'1px solid #00ff8833':'1px solid #334155',
                    color: m.role==='user'?'#00ff88':'#e2e8f0',
                    fontSize:'0.85rem', lineHeight:1.5
                  }}>
                    {m.content}
                  </div>
                ))}
                {isTyping && <div style={{ color:'#64748b', fontSize:'0.75rem', marginLeft:'4px' }}>KaiNova is thinking...</div>}
              </div>

              <div style={{ padding:'15px', borderTop:'1px solid rgba(255,255,255,0.05)', display:'flex', gap:'10px' }}>
                <input type="text" placeholder="Analyze BTC/USDT using Mobula..." 
                  value={chatMsg} onChange={(e)=>setChatMsg(e.target.value)} 
                  onKeyDown={(e)=>e.key==='Enter' && handleSend()}
                  style={{ flex:1, background:'rgba(0,0,0,0.3)', border:'1px solid rgba(255,255,255,0.1)', borderRadius:'12px', padding:'10px 14px', color:'white', outline:'none', fontSize:'0.85rem' }}/>
                <button onClick={handleSend} style={{ background:'#00ff88', border:'none', borderRadius:'12px', width:'42px', height:'42px', display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer', boxShadow:'0 0 15px rgba(0,255,136,0.3)' }}>
                  🚀
                </button>
              </div>
            </motion.div>
          )}
          
          <motion.div 
            onClick={() => setIsChatOpen(!isChatOpen)}
            whileHover={{ scale: 1.1, rotate:5 }}
            whileTap={{ scale: 0.9 }}
            style={{ 
              width:'72px', height:'72px', borderRadius:'100%',
              background:'linear-gradient(135deg, #020617 0%, #0f172a 100%)',
              display:'flex', alignItems:'center', justifyContent:'center',
              cursor:'pointer', border: isBrainConnected?'2px solid #00ff88':'2px solid #334155',
              boxShadow: isBrainConnected?'0 0 30px rgba(0,255,136,0.4)':'0 10px 30px rgba(0,0,0,0.5)',
              position:'relative'
            }}
          >
            <span style={{ fontSize:'32px' }}>🧠</span>
            {isBrainConnected && (
              <motion.div animate={{ scale:[1,1.4,1], opacity:[0.5,0.1,0.5] }} transition={{ duration:2, repeat:Infinity }}
                style={{ position:'absolute', width:'100%', height:'100%', borderRadius:'100%', border:'2px solid #00ff88' }}/>
            )}
            <div style={{ position:'absolute', bottom:'-5px', right:'-5px', width:'14px', height:'14px', borderRadius:'100%', background:isBrainConnected?'#00ff88':'#ff4455', border:'2px solid #020617' }}/>
          </motion.div>
        </div>
      </div>
    </>
  )
}
