'use client'
import { useSession } from 'next-auth/react'
import Link from 'next/link'
import { useState, useEffect } from 'react'

export function Navbar() {
  const { data: session } = useSession()
  const [cliConnected, setCliConnected] = useState(false)

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch('/api/connect/status')
        const data = await res.json()
        setCliConnected(data.connected)
      } catch (e) {}
    }
    checkStatus()
    const intv = setInterval(checkStatus, 5000)
    return () => clearInterval(intv)
  }, [])

  return (
    <nav style={{ 
      height:'64px', borderBottom:'1px solid rgba(255,255,255,0.1)', 
      display:'flex', alignItems:'center', justifyContent:'space-between', 
      padding:'0 24px', backdropFilter:'blur(10px)', position:'sticky', top:0, zIndex:100 
    }}>
      <div style={{ display:'flex', alignItems:'center', gap:'20px' }}>
        <div style={{ display:'flex', alignItems:'center', gap:'12px' }}>
          <div style={{ fontSize:'24px' }}>🦾</div>
          <div style={{ fontWeight:800, fontSize:'1.2rem', background:'linear-gradient(135deg,#00ff88,#00d4ff)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent' }}>
            BinanceClawBot
          </div>
        </div>
        
        {/* CLI Connection Status */}
        <div style={{ 
          fontSize: '0.75rem', fontWeight: 900, letterSpacing: '1.5px',
          padding: '6px 14px', borderRadius: '6px',
          background: cliConnected ? 'rgba(0,255,136,0.15)' : 'rgba(255,68,68,0.15)',
          color: cliConnected ? '#00ff88' : '#ff4444',
          border: `1px solid ${cliConnected ? '#00ff88' : '#ff4444'}`,
          boxShadow: cliConnected ? '0 0 15px rgba(0,255,136,0.2)' : 'none',
          transition: 'all 0.3s ease'
        }}>
          OPENAI CONNECTED: {cliConnected ? 'YES' : 'NO'}
        </div>
      </div>
      
      <div style={{ display:'flex', gap:'24px', alignItems:'center' }}>
        <Link href="/dashboard" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>Dashboard</Link>
        <Link href="/signals" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>Signals</Link>
        <Link href="/skills" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>Skills Hub</Link>
        
        {!session ? (
          <Link href="/login" style={{ 
            padding:'8px 16px', borderRadius:'10px', 
            background:'rgba(0,255,136,0.1)', border:'1px solid rgba(0,255,136,0.3)', 
            color:'#00ff88', textDecoration:'none', fontWeight:600, fontSize:'0.85rem' 
          }}>
            Connect Brain 🧠
          </Link>
        ) : (
          <div style={{ display:'flex', alignItems:'center', gap:'10px', padding:'6px 14px', borderRadius:'10px', background:'rgba(0,255,136,0.05)', border:'1px solid rgba(0,255,136,0.1)' }}>
            <div style={{ width:'8px', height:'8px', borderRadius:'50%', background:'#00ff88', boxShadow:'0 0 10px #00ff88' }}></div>
            <span style={{ fontSize:'0.85rem', color:'#00ff88', fontWeight:600 }}>Brain Connected</span>
          </div>
        )}
      </div>
    </nav>
  )
}
