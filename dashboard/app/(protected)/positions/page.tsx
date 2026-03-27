'use client'
import { useEffect, useState } from 'react'
import { useBotStore } from '@/store/botStore'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'

export default function PositionsPage() {
  const { positions, fetchPositions, closePosition } = useBotStore()
  useEffect(() => { fetchPositions() }, [])

  const close = async (sym: string) => {
    try { await closePosition(sym); toast.success(`✅ Closed ${sym}`); fetchPositions() }
    catch { toast.error(`Failed to close ${sym}`) }
  }

  return (
    <div>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'28px' }}>
        <h1 style={{ color:'white', fontSize:'1.6rem', fontWeight:800 }}>📋 Open Positions</h1>
        <button onClick={fetchPositions} style={{ padding:'10px 20px', borderRadius:'10px', border:'1px solid rgba(0,255,136,0.3)', background:'rgba(0,255,136,0.1)', color:'#00ff88', cursor:'pointer', fontWeight:600, fontSize:'0.85rem' }}>
          🔄 Refresh
        </button>
      </div>

      {positions.length === 0 ? (
        <div style={{ textAlign:'center', padding:'80px', color:'#475569' }}>
          <div style={{ fontSize:'48px', marginBottom:'16px' }}>📋</div>
          <p>No open positions. The bot will open positions when it finds a high-confidence signal.</p>
        </div>
      ) : positions.map((p:any, i:number) => {
        const pnl = p.unrealized_pnl || 0
        const pnlColor = pnl >= 0 ? '#00ff88' : '#ff4455'
        return (
          <motion.div key={i} initial={{opacity:0,x:-20}} animate={{opacity:1,x:0}} transition={{delay:i*0.08}}
            style={{ background:'rgba(168,85,247,0.04)', border:'1px solid rgba(168,85,247,0.15)', borderRadius:'16px', padding:'20px', marginBottom:'12px' }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
              <div>
                <div style={{ color:'white', fontSize:'1.1rem', fontWeight:800 }}>{p.symbol}</div>
                <div style={{ display:'flex', gap:'16px', marginTop:'8px', fontSize:'0.82rem', color:'#64748b' }}>
                  <span>Side: <strong style={{ color: p.side==='BUY'?'#00ff88':'#ff4455' }}>{p.side}</strong></span>
                  <span>Qty: <strong style={{ color:'#e2e8f0' }}>{p.qty}</strong></span>
                  <span>Entry: <strong style={{ color:'#e2e8f0' }}>${parseFloat(p.entry_price||0).toFixed(4)}</strong></span>
                  {p.sl && <span>SL: <strong style={{ color:'#ff4455' }}>${p.sl.toFixed(4)}</strong></span>}
                  {p.tp && <span>TP: <strong style={{ color:'#00ff88' }}>${p.tp.toFixed(4)}</strong></span>}
                </div>
              </div>
              <div style={{ textAlign:'right' }}>
                <div style={{ color:pnlColor, fontSize:'1.3rem', fontWeight:800 }}>
                  {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)} USDT
                </div>
                <button onClick={() => close(p.symbol)}
                  style={{ marginTop:'8px', padding:'8px 20px', borderRadius:'8px', border:'1px solid rgba(255,68,85,0.3)', background:'rgba(255,68,85,0.1)', color:'#ff4455', cursor:'pointer', fontWeight:600, fontSize:'0.8rem' }}>
                  Close Position
                </button>
              </div>
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
