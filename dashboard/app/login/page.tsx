'use client'
import { signIn, useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { motion } from 'framer-motion'
import { Canvas } from '@react-three/fiber'
import { Stars, OrbitControls } from '@react-three/drei'
import { Suspense } from 'react'

function BG() {
  return <><Stars radius={80} depth={50} count={4000} factor={3} fade speed={0.5}/><OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.2}/></>
}

export default function LoginPage() {
  const { data: session } = useSession()
  const router = useRouter()
  useEffect(() => { if (session) router.push('/dashboard') }, [session])

  return (
    <div style={{ minHeight:'100vh', background:'#020408', display:'flex', alignItems:'center', justifyContent:'center', position:'relative' }}>
      <div style={{ position:'absolute', inset:0 }}>
        <Canvas camera={{ position:[0,0,5], fov:60 }}>
          <Suspense fallback={null}><BG/></Suspense>
        </Canvas>
      </div>

      <motion.div initial={{ opacity:0, y:30 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.8 }}
        style={{ position:'relative', zIndex:10, textAlign:'center', maxWidth:'420px', width:'90%' }}>

        {/* Logo */}
        <div style={{ fontSize:'64px', marginBottom:'16px' }}>🤖</div>
        <h1 style={{ fontSize:'2.5rem', fontWeight:800, background:'linear-gradient(135deg,#00ff88,#00d4ff)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent', marginBottom:'8px' }}>
          BinanceClawBot
        </h1>
        <p style={{ color:'#64748b', marginBottom:'40px', fontSize:'1rem' }}>
          Autonomous crypto trading · 26 Binance Skills · 24/7 AI Brain
        </p>

        {/* Auth Card */}
        <div style={{ background:'rgba(0,0,0,0.7)', border:'1px solid rgba(0,255,136,0.2)', borderRadius:'20px', padding:'32px', backdropFilter:'blur(20px)' }}>
          <h2 style={{ color:'white', fontSize:'1.2rem', fontWeight:700, marginBottom:'8px' }}>Sign in to continue</h2>
          <p style={{ color:'#475569', fontSize:'0.85rem', marginBottom:'28px' }}>
            Connect your account to control the bot, view portfolio, and run AI analysis
          </p>

          {/* OAuth Providers */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {[
              { provider:'openai', label:'Continue with OpenAI Codex', icon:'🤖', sub:'Use your OpenAI / ChatGPT account', color:'#10a37f' },
              { provider:'google', label:'Continue with Google', icon:'🟢', sub:'Gemini · Antigravity OAuth', color:'#4285f4' },
              { provider:'github', label:'Continue with GitHub', icon:'⚫', sub:'Developer OAuth', color:'#000000' },
            ].map(({ provider, label, icon, sub }) => (
              <motion.button key={provider} whileHover={{ scale:1.02 }} whileTap={{ scale:0.98 }}
                onClick={() => signIn(provider, { callbackUrl: '/dashboard' })}
                style={{
                  width:'100%', padding:'12px 16px', borderRadius:'12px', cursor:'pointer',
                  background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.1)',
                  display:'flex', alignItems:'center', gap:'12px', textAlign:'left'
                }}>
                <span style={{ fontSize:'20px' }}>{icon}</span>
                <div style={{ flex:1 }}>
                  <div style={{ color:'white', fontWeight:600, fontSize:'0.9rem' }}>{label}</div>
                  <div style={{ color:'#64748b', fontSize:'0.7rem' }}>{sub}</div>
                </div>
              </motion.button>
            ))}
          </div>

          {/* Divider */}
          <div style={{ margin: '24px 0', borderBottom: '1px solid rgba(255,255,255,0.1)', position: 'relative' }}>
            <span style={{ 
              position: 'absolute', top: '-10px', left: '50%', transform: 'translateX(-50%)', 
              background: '#0a1628', padding: '0 12px', color: '#475569', 
              fontSize: '0.7rem', fontWeight: 600, letterSpacing: '1px' 
            }}>OR USE API PROVIDER</span>
          </div>

          {/* Direct API Key Section */}
          <div style={{ textAlign:'left', background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <div style={{ marginBottom: '12px' }}>
              <select style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#1e293b', border: '1px solid #334155', color: 'white', fontSize: '0.85rem', marginBottom: '8px' }}>
                <option>OpenRouter (Recommended)</option>
                <option>Groq (Ultra-Fast)</option>
                <option>OpenAI (Direct Key)</option>
                <option>Ollama (Local AI)</option>
              </select>
              <input type="password" placeholder="Enter your API Key..." style={{ width: '100%', padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.02)', border: '1px solid #334155', color: 'white', fontSize: '0.85rem' }} />
            </div>
            <button style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#00ff88', color: '#020617', fontWeight: 700, cursor: 'pointer', border: 'none', fontSize: '0.85rem' }}>
              Connect via Key
            </button>
          </div>

          <div style={{ marginTop:'20px', padding:'12px', background:'rgba(0,255,136,0.03)', borderRadius:'10px', border:'1px solid rgba(0,255,136,0.1)' }}>
            <p style={{ color:'#64748b', fontSize:'0.7rem', lineHeight:1.5 }}>
              🔒 Your API keys are stored only in your session.
              Auth tokens are encrypted locally.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
