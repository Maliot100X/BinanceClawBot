'use client'
import { useEffect } from 'react'
import { useBotStore } from '@/store/botStore'
import { motion } from 'framer-motion'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const COLORS = ['#00ff88','#00d4ff','#a855f7','#f59e0b','#ff4455','#10b981']

export default function PortfolioPage() {
  const { portfolio, fetchPortfolio } = useBotStore()
  useEffect(() => { fetchPortfolio() }, [])

  const balances = portfolio?.balances?.filter((b:any) => parseFloat(b.free) > 0) || []
  const total = portfolio?.total_usdt || 0

  const pieData = balances.slice(0,6).map((b:any) => ({ name:b.asset, value:parseFloat(b.free) }))

  return (
    <div>
      <h1 style={{ color:'white', fontSize:'1.6rem', fontWeight:800, marginBottom:'28px' }}>💼 Portfolio</h1>

      {balances.length === 0 ? (
        <div style={{ textAlign:'center', padding:'80px', color:'#475569' }}>
          <div style={{ fontSize:'48px', marginBottom:'16px' }}>💼</div>
          <p>No portfolio data — configure Binance API keys in Settings first</p>
        </div>
      ) : (
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'24px' }}>
          {/* Chart */}
          <div style={{ background:'rgba(0,255,136,0.04)', border:'1px solid rgba(0,255,136,0.1)', borderRadius:'16px', padding:'24px' }}>
            <h2 style={{ color:'#00ff88', fontWeight:700, marginBottom:'16px' }}>Asset Allocation</h2>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:'20px' }}>
              <ResponsiveContainer width={200} height={200}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value">
                    {pieData.map((_:any, i:number) => <Cell key={i} fill={COLORS[i%COLORS.length]}/>)}
                  </Pie>
                  <Tooltip contentStyle={{ background:'#0f172a', border:'1px solid #00ff8833', borderRadius:'8px' }}/>
                </PieChart>
              </ResponsiveContainer>
              <div>
                {pieData.map((d:any, i:number) => (
                  <div key={i} style={{ display:'flex', alignItems:'center', gap:'8px', marginBottom:'8px' }}>
                    <div style={{ width:'10px', height:'10px', borderRadius:'50%', background:COLORS[i%COLORS.length] }}/>
                    <span style={{ color:'#94a3b8', fontSize:'0.82rem' }}>{d.name}</span>
                  </div>
                ))}
              </div>
            </div>
            <div style={{ textAlign:'center', marginTop:'16px' }}>
              <div style={{ color:'#475569', fontSize:'0.8rem' }}>Total Value</div>
              <div style={{ color:'#00ff88', fontSize:'2rem', fontWeight:800 }}>${parseFloat(total).toLocaleString('en',{maximumFractionDigits:2})}</div>
            </div>
          </div>

          {/* Balance Table */}
          <div style={{ background:'rgba(0,0,0,0.3)', border:'1px solid rgba(255,255,255,0.06)', borderRadius:'16px', padding:'24px' }}>
            <h2 style={{ color:'white', fontWeight:700, marginBottom:'16px' }}>Asset Balances</h2>
            {balances.map((b:any, i:number) => (
              <motion.div key={i} initial={{opacity:0,x:-10}} animate={{opacity:1,x:0}} transition={{delay:i*0.05}}
                style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'12px 0', borderBottom:'1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ display:'flex', alignItems:'center', gap:'10px' }}>
                  <div style={{ width:'32px', height:'32px', borderRadius:'50%', background:`${COLORS[i%COLORS.length]}22`, border:`1px solid ${COLORS[i%COLORS.length]}44`, display:'flex', alignItems:'center', justifyContent:'center', fontSize:'0.75rem', color:COLORS[i%COLORS.length], fontWeight:700 }}>
                    {b.asset.slice(0,3)}
                  </div>
                  <div>
                    <div style={{ color:'white', fontWeight:600, fontSize:'0.9rem' }}>{b.asset}</div>
                    <div style={{ color:'#475569', fontSize:'0.75rem' }}>Free: {parseFloat(b.free).toFixed(4)}</div>
                  </div>
                </div>
                <div style={{ textAlign:'right' }}>
                  <div style={{ color:'#00ff88', fontWeight:600 }}>${(parseFloat(b.usdt_value||0)).toLocaleString('en',{maximumFractionDigits:2})}</div>
                  <div style={{ color:'#475569', fontSize:'0.75rem' }}>Locked: {parseFloat(b.locked||0).toFixed(4)}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
