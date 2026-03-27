'use client'
import { signIn, useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Canvas } from '@react-three/fiber'
import { Stars, OrbitControls } from '@react-three/drei'
import { Suspense } from 'react'
import { toast } from 'react-hot-toast'

function BG() {
  return (
    <>
      <Stars radius={80} depth={50} count={4000} factor={3} fade speed={0.5} />
      <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.2} />
    </>
  )
}

export default function LoginPage() {
  const { data: session } = useSession()
  const router = useRouter()
  const [provider, setProvider] = useState('openrouter')
  const [apiKey, setApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [systemStatus, setSystemStatus] = useState<'checking' | 'online' | 'offline'>('checking')

  useEffect(() => { if (session) router.push('/dashboard') }, [session])

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const res = await fetch(`${backendUrl}/health`)
        if (res.ok) setSystemStatus('online')
        else setSystemStatus('offline')
      } catch (e) {
        setSystemStatus('offline')
      }
    }
    checkStatus()
    const timer = setInterval(checkStatus, 5000)
    return () => clearInterval(timer)
  }, [])

  const connectApiKey = async () => {
    if (!apiKey) return toast.error('Please enter an API Key')
    if (loading) return
    setLoading(true)
    try {
      const res = await fetch('/api/ai/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, api_key: apiKey }),
      })
      const data = await res.json()
      if (data.success) {
        toast.success(`Successfully connected ${provider.toUpperCase()} Brain! 🧠`)
        router.push('/dashboard')
      } else {
        toast.error(data.error || 'Failed to connect')
      }
    } catch (e) {
      toast.error('Local API Server (port 8000) not reached. Please run py start_all.py first.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: '#020408', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
      <div style={{ position: 'absolute', inset: 0 }}>
        <Canvas camera={{ position: [0, 0, 5], fov: 60 }}>
          <Suspense fallback={null}><BG /></Suspense>
        </Canvas>
      </div>

      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}
        style={{ position: 'relative', zIndex: 10, textAlign: 'center', maxWidth: '440px', width: '95%' }}>

        {/* Logo */}
        <div style={{ fontSize: '64px', marginBottom: '16px' }}>🤖</div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, background: 'linear-gradient(135deg,#00ff88,#00d4ff)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', marginBottom: '8px' }}>
          BinanceClawBot
        </h1>
        <p style={{ color: '#64748b', marginBottom: '32px', fontSize: '1rem' }}>
          Autonomous crypto trading · 26 Binance Skills · 24/7 AI Brain
        </p>

        {/* System Status Indicator */}
        <div style={{ marginBottom: '20px', display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 12px', borderRadius: '20px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: systemStatus === 'online' ? '#00ff88' : systemStatus === 'offline' ? '#ff4444' : '#64748b' }} />
          <span style={{ color: '#64748b', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '1px' }}>
            AI BACKEND: {systemStatus.toUpperCase()}
          </span>
        </div>

        {/* Auth Card */}
        <div style={{ background: 'rgba(10, 22, 40, 0.8)', border: '1px solid rgba(0,255,136,0.2)', borderRadius: '24px', padding: '32px', backdropFilter: 'blur(24px)', boxShadow: '0 20px 50px rgba(0,0,0,0.5)' }}>
          <h2 style={{ color: 'white', fontSize: '1.25rem', fontWeight: 700, marginBottom: '8px' }}>Brain Connection Center</h2>
          <p style={{ color: '#475569', fontSize: '0.85rem', marginBottom: '28px' }}>
            Choose your AI reasoning engine to power the autonomous bot
          </p>

          {/* OAuth Providers */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {[
              { provider: 'openai', label: 'Continue with OpenAI Codex', icon: '🤖', sub: 'Use your OpenAI Account' },
              { provider: 'google', label: 'Continue with Google', icon: '🟢', sub: 'Gemini · Antigravity OAuth' },
              { provider: 'github', label: 'Continue with GitHub', icon: '⚫', sub: 'Developer OAuth' },
            ].map(({ provider, label, icon, sub }) => (
              <motion.button key={provider} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                onClick={() => signIn(provider, { callbackUrl: '/dashboard' })}
                style={{
                  width: '100%', padding: '12px 16px', borderRadius: '14px', cursor: 'pointer',
                  background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
                  display: 'flex', alignItems: 'center', gap: '12px', textAlign: 'left'
                }}>
                <span style={{ fontSize: '20px' }}>{icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ color: 'white', fontWeight: 600, fontSize: '0.9rem' }}>{label}</div>
                  <div style={{ color: '#64748b', fontSize: '0.7rem' }}>{sub}</div>
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
          <div style={{ textAlign: 'left', background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', color: '#64748b', fontSize: '0.7rem', fontWeight: 600, marginBottom: '6px' }}>SELECT PROVIDER</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                style={{ width: '100%', padding: '10px', borderRadius: '10px', background: '#1e293b', border: '1px solid #334155', color: 'white', fontSize: '0.85rem' }}>
                <option value="openrouter">OpenRouter (Claude/Llama/Grok)</option>
                <option value="groq">Groq (Ultra-Fast Llama 3)</option>
                <option value="openai">OpenAI (Direct API Key)</option>
                <option value="ollama">Ollama (Local Browser AI)</option>
                <option value="gemini">Google AI Studio (Gemini)</option>
              </select>
            </div>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', color: '#64748b', fontSize: '0.7rem', fontWeight: 600, marginBottom: '6px' }}>API KEY</label>
              <input
                type="password"
                placeholder="sk-..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                style={{ width: '100%', padding: '10px', borderRadius: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid #334155', color: '#00ff88', fontSize: '0.85rem' }}
              />
            </div>
            <button
              onClick={connectApiKey}
              disabled={loading}
              style={{
                width: '100%', padding: '12px', borderRadius: '10px',
                background: loading ? '#334155' : 'linear-gradient(135deg, #00ff88, #00d4ff)',
                color: '#020617', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', border: 'none',
                fontSize: '0.85rem', boxShadow: loading ? 'none' : '0 4px 12px rgba(0,255,136,0.3)',
                transition: 'all 0.2s'
              }}>
              {loading ? 'Connecting...' : 'Connect AI Brain 🧠'}
            </button>
          </div>

          <div style={{ marginTop: '20px', padding: '12px', background: 'rgba(0,255,136,0.03)', borderRadius: '12px', border: '1px solid rgba(0,255,136,0.1)' }}>
            <p style={{ color: '#64748b', fontSize: '0.75rem', lineHeight: 1.6 }}>
              🔒 Your API keys are stored only in your session.
              Auth tokens are encrypted locally and never leave your control.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
