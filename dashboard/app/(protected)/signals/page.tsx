'use client'
import { useEffect } from 'react'
import { useBotStore } from '@/store/botStore'
import { motion } from 'framer-motion'

const SIG_COLOR = (s:string) => s==='BUY'?'#00ff88':s==='SELL'?'#ff4455':'#facc15'

export default function SignalsPage() {
  const { signals, fetchSignals } = useBotStore()
  useEffect(() => { fetchSignals(); setInterval(fetchSignals, 30000) }, [])

  return (
    <div>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'28px' }}>
        <h1 style={{ color:'white', fontSize:'1.6rem', fontWeight:800 }}>📡 Trading Signals</h1>
        <button onClick={fetchSignals} style={{ padding:'10px 20px', borderRadius:'10px', border:'1px solid rgba(0,212,255,0.3)', background:'rgba(0,212,255,0.1)', color:'#00d4ff', cursor:'pointer', fontWeight:600, fontSize:'0.85rem' }}>
          🔄 Refresh
        </button>
      </div>

      {signals.length === 0 ? (
        <div style={{ textAlign:'center', padding:'80px 0', color:'#475569' }}>
          <div style={{ fontSize:'48px', marginBottom:'16px' }}>📡</div>
          <p>No signals yet. Start the bot to begin scanning markets every 30 seconds.</p>
        </div>
      ) : (
        <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(300px,1fr))', gap:'16px' }}>
          {signals.map((s:any, i:number) => {
            const c = SIG_COLOR(s.signal)
            const bars = Math.round((s.confidence||0)/10)
            return (
              <motion.div key={i} initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:i*0.05}}
                style={{ background:`${c}06`, border:`1px solid ${c}22`, borderRadius:'16px', padding:'20px' }}>
                <div style={{ display:'flex', justifyContent:'space-between', marginBottom:'12px' }}>
                  <span style={{ color:'white', fontSize:'1.1rem', fontWeight:800 }}>{s.symbol}</span>
                  <span style={{ padding:'4px 12px', borderRadius:'20px', background:`${c}22`, color:c, fontWeight:700, fontSize:'0.85rem' }}>{s.signal}</span>
                </div>
                <div style={{ color:'#64748b', fontSize:'0.82rem', marginBottom:'12px' }}>${parseFloat(s.price||0).toLocaleString()}</div>
                <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'8px', fontSize:'0.8rem' }}>
                  <div><span style={{ color:'#475569' }}>RSI: </span><span style={{ color:'#e2e8f0', fontWeight:600 }}>{s.rsi?.toFixed(1)||'—'}</span></div>
                  <div><span style={{ color:'#475569' }}>Trend: </span><span style={{ color:'#e2e8f0', fontWeight:600 }}>{s.trend||'—'}</span></div>
                </div>
                <div style={{ marginTop:'12px' }}>
                  <div style={{ display:'flex', justifyContent:'space-between', marginBottom:'4px' }}>
                    <span style={{ color:'#475569', fontSize:'0.75rem' }}>Confidence</span>
                    <span style={{ color:c, fontSize:'0.75rem', fontWeight:700 }}>{(s.confidence||0).toFixed(0)}%</span>
                  </div>
                  <div style={{ display:'flex', gap:'3px' }}>
                    {Array.from({length:10},(_,j)=>(
                      <div key={j} style={{ flex:1, height:'6px', borderRadius:'3px', background: j<bars?c:'#1e293b' }}/>
                    ))}
                  </div>
                </div>
                {s.reason && <div style={{ marginTop:'10px', color:'#64748b', fontSize:'0.75rem', fontStyle:'italic' }}>{s.reason}</div>}
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}
