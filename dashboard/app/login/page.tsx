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

          {/* OAuth Buttons */}
          {[
            { provider:'openai', label:'Continue with OpenAI Codex', icon:'🤖', sub:'Use your OpenAI / ChatGPT account', color:'#00ff88' },
            { provider:'google', label:'Continue with Google', icon:'🟢', sub:'Gemini · Antigravity OAuth', color:'#4285f4' },
            { provider:'github', label:'Continue with GitHub', icon:'⚫', sub:'Developer OAuth', color:'#e2e8f0' },
          ].map(({ provider, label, icon, sub, color }) => (
            <motion.button key={provider} whileHover={{ scale:1.02 }} whileTap={{ scale:0.98 }}
              onClick={() => signIn(provider, { callbackUrl: '/dashboard' })}
              style={{
                width:'100%', padding:'14px 20px', borderRadius:'12px', cursor:'pointer', marginBottom:'12px',
                background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.12)',
                display:'flex', alignItems:'center', gap:'14px', textAlign:'left'
              }}>
              <span style={{ fontSize:'22px' }}>{icon}</span>
              <div>
                <div style={{ color:'white', fontWeight:600, fontSize:'0.95rem' }}>{label}</div>
                <div style={{ color:'#475569', fontSize:'0.75rem' }}>{sub}</div>
              </div>
            </motion.button>
          ))}

          <div style={{ marginTop:'20px', padding:'12px', background:'rgba(0,255,136,0.05)', borderRadius:'10px', border:'1px solid rgba(0,255,136,0.1)' }}>
            <p style={{ color:'#64748b', fontSize:'0.75rem', lineHeight:1.6 }}>
              🔒 Your Binance API keys are stored only in your session, never on our servers.
              OAuth tokens are encrypted and auto-refreshed.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
