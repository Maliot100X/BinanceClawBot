'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { signOut, useSession } from 'next-auth/react'
import { motion } from 'framer-motion'
import { useBotStore } from '@/store/botStore'
import { useEffect } from 'react'

const NAV = [
  { href:'/dashboard',  label:'Dashboard',  icon:'📊' },
  { href:'/portfolio',  label:'Portfolio',  icon:'💼' },
  { href:'/signals',    label:'Signals',    icon:'📡' },
  { href:'/positions',  label:'Positions',  icon:'📋' },
  { href:'/skills',     label:'Skills',     icon:'🔧' },
  { href:'/settings',   label:'Settings',   icon:'⚙️' },
]

export default function Sidebar() {
  const path = usePathname()
  const { data: session } = useSession()
  const { isRunning, fetchStatus } = useBotStore()

  useEffect(() => { fetchStatus() }, [])

  return (
    <aside style={{
      width:'220px', minHeight:'100vh', background:'rgba(0,0,0,0.6)',
      borderRight:'1px solid rgba(0,255,136,0.1)', backdropFilter:'blur(20px)',
      display:'flex', flexDirection:'column', padding:'24px 0', position:'fixed', top:0, left:0, zIndex:100
    }}>
      {/* Logo */}
      <div style={{ padding:'0 20px 24px', borderBottom:'1px solid rgba(0,255,136,0.1)' }}>
        <div style={{ display:'flex', alignItems:'center', gap:'10px' }}>
          <div style={{ fontSize:'28px' }}>🤖</div>
          <div>
            <div style={{ color:'#00ff88', fontWeight:800, fontSize:'1.1rem' }}>KaiNova</div>
            <div style={{ color:'#475569', fontSize:'0.7rem' }}>BinanceClawBot</div>
          </div>
        </div>
        {/* Bot status */}
        <div style={{ marginTop:'12px', display:'flex', alignItems:'center', gap:'6px', padding:'6px 10px', borderRadius:'8px', background: isRunning?'rgba(0,255,136,0.08)':'rgba(255,68,85,0.08)', border:`1px solid ${isRunning?'rgba(0,255,136,0.2)':'rgba(255,68,85,0.2)'}` }}>
          <motion.div style={{ width:'8px', height:'8px', borderRadius:'50%', background: isRunning?'#00ff88':'#ff4455' }}
            animate={{ opacity: isRunning?[1,0.4,1]:1 }} transition={{ repeat: isRunning?Infinity:0, duration:1.5 }}/>
          <span style={{ fontSize:'0.75rem', color: isRunning?'#00ff88':'#ff4455', fontWeight:600 }}>
            {isRunning ? 'TRADING LIVE' : 'BOT STOPPED'}
          </span>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex:1, padding:'16px 12px', display:'flex', flexDirection:'column', gap:'4px' }}>
        {NAV.map(({ href, label, icon }) => {
          const active = path === href || path.startsWith(href+'/') && href !== '/'
          return (
            <Link key={href} href={href} style={{ textDecoration:'none' }}>
              <motion.div whileHover={{ x:4 }}
                style={{
                  display:'flex', alignItems:'center', gap:'10px', padding:'10px 14px', borderRadius:'10px',
                  background: active?'rgba(0,255,136,0.1)':'transparent',
                  border: active?'1px solid rgba(0,255,136,0.2)':'1px solid transparent',
                  color: active?'#00ff88':'#64748b', fontWeight: active?600:400, fontSize:'0.9rem',
                  transition:'all 0.15s', cursor:'pointer'
                }}>
                <span>{icon}</span> {label}
                {active && <motion.div layoutId="active-pill" style={{ marginLeft:'auto', width:'4px', height:'4px', borderRadius:'50%', background:'#00ff88' }}/>}
              </motion.div>
            </Link>
          )
        })}
      </nav>

      {/* User */}
      <div style={{ padding:'16px 20px', borderTop:'1px solid rgba(0,255,136,0.1)' }}>
        {session?.user && (
          <div style={{ marginBottom:'12px' }}>
            <div style={{ color:'#e2e8f0', fontSize:'0.85rem', fontWeight:600, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
              {session.user.name}
            </div>
            <div style={{ color:'#475569', fontSize:'0.72rem', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
              {session.user.email}
            </div>
          </div>
        )}
        <button onClick={() => signOut({ callbackUrl: '/login' })}
          style={{ width:'100%', padding:'8px', borderRadius:'8px', border:'1px solid rgba(255,68,85,0.3)', background:'rgba(255,68,85,0.08)', color:'#ff4455', cursor:'pointer', fontSize:'0.8rem', fontWeight:600 }}>
          Sign Out
        </button>
      </div>
    </aside>
  )
}
