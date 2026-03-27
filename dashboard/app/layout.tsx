'use client'
import { useSession } from 'next-auth/react'
import { Toaster } from 'react-hot-toast'
import Link from 'next/link'
import { Providers } from './providers'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession()

  return (
    <html lang="en">
      <body style={{ margin: 0, background: '#020408', fontFamily: 'system-ui, -apple-system, sans-serif', color: 'white' }}>
        <Providers>
          {/* Top Navbar */}
          <nav style={{ 
            height:'64px', borderBottom:'1px solid rgba(255,255,255,0.1)', 
            display:'flex', alignItems:'center', justifyContent:'space-between', 
            padding:'0 24px', backdropFilter:'blur(10px)', position:'sticky', top:0, zIndex:100 
          }}>
            <div style={{ display:'flex', alignItems:'center', gap:'12px' }}>
              <div style={{ fontSize:'24px' }}>🦾</div>
              <div style={{ fontWeight:800, fontSize:'1.2rem', background:'linear-gradient(135deg,#00ff88,#00d4ff)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent' }}>
                BinanceClawBot
              </div>
            </div>
            
            <div style={{ display:'flex', gap:'24px', alignItems:'center' }}>
              <Link href="/dashboard" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>Dashboard</Link>
              <Link href="/signals" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>Signals</Link>
              <Link href="/skills" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>Skills</Link>
              
              {!session ? (
                <Link href="/login" style={{ 
                  padding:'8px 16px', borderRadius:'10px', 
                  background:'rgba(0,255,136,0.1)', border:'1px solid rgba(0,255,136,0.3)', 
                  color:'#00ff88', textDecoration:'none', fontWeight:600, fontSize:'0.85rem' 
                }}>
                  Connect Brain 🧠
                </Link>
              ) : (
                <div style={{ display:'flex', alignItems:'center', gap:'10px' }}>
                  <div style={{ width:'8px', height:'8px', borderRadius:'50%', background:'#00ff88' }}></div>
                  <span style={{ fontSize:'0.85rem', color:'#00ff88', fontWeight:600 }}>Brain Connected</span>
                </div>
              )}
            </div>
          </nav>
          
          <main style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }}>
            {children}
          </main>
          
          <Toaster position="top-right" toastOptions={{ 
            style: { background: '#0f172a', color: '#e2e8f0', border: '1px solid rgba(0,255,136,0.2)' } 
          }} />
        </Providers>
      </body>
    </html>
  )
}
