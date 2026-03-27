'use client'
import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useBotStore } from '@/store/botStore'
import toast from 'react-hot-toast'

const QUICK_CMDS = [
  { label: '📊 Status',    msg: 'What is the current bot status and portfolio?' },
  { label: '🔍 Scan',      msg: 'Scan top 10 markets for opportunities now' },
  { label: '📈 Signals',   msg: 'Show me the current trading signals with confidence' },
  { label: '💼 Portfolio', msg: 'Show my full portfolio balance and PnL' },
  { label: '⚡ Start Bot', msg: 'Start the autonomous trading bot' },
  { label: '⏹ Stop Bot',  msg: 'Stop the trading bot immediately' },
]

export default function FloatingBot() {
  const [open, setOpen] = useState(false)
  const [msgs, setMsgs] = useState<{role:'user'|'bot',text:string}[]>([
    { role:'bot', text:'👋 Hi! I\'m KaiNova, your AI trading brain. I\'m connected to all 26 Binance skills. Ask me anything or use a quick command below!' }
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const { chatWithAI, isRunning, startBot, stopBot } = useBotStore()
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs])

  const send = async (text: string) => {
    if (!text.trim() || busy) return
    setMsgs(p => [...p, { role: 'user', text }])
    setInput('')
    setBusy(true)

    // Check for quick actions
    const lower = text.toLowerCase()
    if (lower.includes('start bot')) {
      await startBot().catch(() => null)
      setMsgs(p => [...p, { role:'bot', text:'✅ Bot started! Auto-trading every 30 seconds on 10 pairs.' }])
      setBusy(false); return
    }
    if (lower.includes('stop bot')) {
      await stopBot().catch(() => null)
      setMsgs(p => [...p, { role:'bot', text:'⏹ Bot stopped. All positions preserved.' }])
      setBusy(false); return
    }

    const reply = await chatWithAI(text)
    setMsgs(p => [...p, { role:'bot', text: reply }])
    setBusy(false)
  }

  return (
    <>
      {/* Floating Button */}
      <motion.button
        onClick={() => setOpen(o => !o)}
        style={{
          position:'fixed', bottom:'28px', right:'28px', zIndex:9999,
          width:'64px', height:'64px', borderRadius:'50%',
          background:'linear-gradient(135deg,#00ff88,#00d4ff)',
          border:'none', cursor:'pointer', boxShadow:'0 0 30px rgba(0,255,136,0.5)',
          display:'flex', alignItems:'center', justifyContent:'center',
          fontSize:'28px'
        }}
        whileHover={{ scale:1.1 }}
        whileTap={{ scale:0.95 }}
        animate={{ boxShadow: isRunning
          ? ['0 0 20px rgba(0,255,136,0.4)','0 0 40px rgba(0,255,136,0.8)','0 0 20px rgba(0,255,136,0.4)']
          : '0 0 30px rgba(0,255,136,0.4)' }}
        transition={{ repeat: isRunning ? Infinity : 0, duration:2 }}
      >
        {open ? '✕' : '🤖'}
      </motion.button>

      {/* Chat Panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity:0, y:20, scale:0.95 }}
            animate={{ opacity:1, y:0, scale:1 }}
            exit={{ opacity:0, y:20, scale:0.95 }}
            style={{
              position:'fixed', bottom:'108px', right:'28px', zIndex:9998,
              width:'380px', maxHeight:'550px',
              background:'rgba(2,4,8,0.97)',
              border:'1px solid rgba(0,255,136,0.25)',
              borderRadius:'20px', overflow:'hidden',
              boxShadow:'0 20px 60px rgba(0,0,0,0.8)',
              display:'flex', flexDirection:'column'
            }}
          >
            {/* Header */}
            <div style={{ padding:'14px 18px', background:'linear-gradient(135deg,rgba(0,255,136,0.1),rgba(0,212,255,0.08))', borderBottom:'1px solid rgba(0,255,136,0.15)', display:'flex', alignItems:'center', gap:'10px' }}>
              <div style={{ fontSize:'22px' }}>🤖</div>
              <div>
                <div style={{ color:'#00ff88', fontWeight:700, fontSize:'0.95rem' }}>KaiNova AI Brain</div>
                <div style={{ fontSize:'0.7rem', display:'flex', alignItems:'center', gap:'5px' }}>
                  <div style={{ width:'6px', height:'6px', borderRadius:'50%', background: isRunning ? '#00ff88':'#ff4455', boxShadow:`0 0 6px ${isRunning?'#00ff88':'#ff4455'}` }}/>
                  <span style={{ color: isRunning?'#00ff88':'#ff4455' }}>{isRunning?'Bot Running':'Bot Stopped'}</span>
                  <span style={{ color:'#475569', marginLeft:'8px' }}>26 Skills Active</span>
                </div>
              </div>
            </div>

            {/* Messages */}
            <div style={{ flex:1, overflowY:'auto', padding:'16px', display:'flex', flexDirection:'column', gap:'10px', maxHeight:'280px' }}>
              {msgs.map((m, i) => (
                <div key={i} style={{ display:'flex', justifyContent: m.role==='user'?'flex-end':'flex-start' }}>
                  <div style={{
                    maxWidth:'85%', padding:'10px 14px', borderRadius: m.role==='user'?'16px 16px 4px 16px':'16px 16px 16px 4px',
                    background: m.role==='user'?'linear-gradient(135deg,#00ff8822,#00d4ff22)':'rgba(255,255,255,0.05)',
                    border:`1px solid ${m.role==='user'?'rgba(0,255,136,0.3)':'rgba(255,255,255,0.08)'}`,
                    color: m.role==='user'?'#00ff88':'#e2e8f0',
                    fontSize:'0.82rem', lineHeight:1.5, whiteSpace:'pre-wrap'
                  }}>
                    {m.text}
                  </div>
                </div>
              ))}
              {busy && (
                <div style={{ display:'flex', gap:'5px', padding:'10px' }}>
                  {[0,1,2].map(i=>(
                    <motion.div key={i} style={{ width:'6px', height:'6px', borderRadius:'50%', background:'#00ff88' }}
                      animate={{ y:[0,-6,0] }} transition={{ repeat:Infinity, duration:0.8, delay:i*0.15 }}/>
                  ))}
                </div>
              )}
              <div ref={bottom}/>
            </div>

            {/* Quick Commands */}
            <div style={{ padding:'8px 12px', borderTop:'1px solid rgba(255,255,255,0.06)', display:'flex', gap:'6px', flexWrap:'wrap' }}>
              {QUICK_CMDS.map(c => (
                <button key={c.label} onClick={()=>send(c.msg)}
                  style={{ padding:'5px 10px', borderRadius:'20px', border:'1px solid rgba(0,255,136,0.2)', background:'rgba(0,255,136,0.06)', color:'#94a3b8', fontSize:'0.72rem', cursor:'pointer', whiteSpace:'nowrap' }}>
                  {c.label}
                </button>
              ))}
            </div>

            {/* Input */}
            <div style={{ padding:'12px 14px', borderTop:'1px solid rgba(255,255,255,0.06)', display:'flex', gap:'8px' }}>
              <input
                value={input} onChange={e=>setInput(e.target.value)}
                onKeyDown={e=>e.key==='Enter'&&send(input)}
                placeholder="Ask anything or type a command..."
                style={{ flex:1, background:'rgba(255,255,255,0.05)', border:'1px solid rgba(0,255,136,0.2)', borderRadius:'10px', padding:'10px 14px', color:'white', fontSize:'0.85rem', outline:'none' }}
              />
              <button onClick={()=>send(input)} disabled={busy}
                style={{ background:'linear-gradient(135deg,#00ff88,#00d4ff)', border:'none', borderRadius:'10px', width:'40px', cursor:'pointer', fontSize:'16px' }}>
                ➤
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
