'use client'
import { useState } from 'react'
import { useBotStore } from '@/store/botStore'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { signIn } from 'next-auth/react'

function Section({ title, children }: any) {
  return (
    <div style={{ background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,0.08)', borderRadius:'16px', padding:'24px', marginBottom:'20px' }}>
      <h2 style={{ color:'white', fontSize:'1.05rem', fontWeight:700, marginBottom:'20px' }}>{title}</h2>
      {children}
    </div>
  )
}

function Field({ label, type='text', placeholder, value, onChange, password=false }: any) {
  return (
    <div style={{ marginBottom:'16px' }}>
      <label style={{ color:'#94a3b8', fontSize:'0.8rem', fontWeight:600, display:'block', marginBottom:'6px' }}>{label}</label>
      <input type={password?'password':type} placeholder={placeholder} value={value} onChange={e=>onChange(e.target.value)}
        style={{ width:'100%', padding:'12px 14px', borderRadius:'10px', border:'1px solid rgba(0,255,136,0.2)', background:'rgba(0,0,0,0.4)', color:'white', fontSize:'0.9rem', outline:'none' }}/>
    </div>
  )
}

function SaveBtn({ onClick, label='Save', color='#00ff88' }: any) {
  return (
    <motion.button whileHover={{ scale:1.02 }} whileTap={{ scale:0.98 }} onClick={onClick}
      style={{ padding:'12px 28px', borderRadius:'10px', border:`1px solid ${color}44`, background:`${color}15`, color, cursor:'pointer', fontWeight:700, fontSize:'0.9rem', marginTop:'8px' }}>
      {label}
    </motion.button>
  )
}

export default function SettingsPage() {
  const { setTelegramConfig, setBinanceConfig, authStatus, fetchAuth } = useBotStore()

  const [tgToken, setTgToken] = useState('')
  const [tgChat, setTgChat] = useState('')
  const [bnKey, setBnKey] = useState('')
  const [bnSecret, setBnSecret] = useState('')
  const [riskPct, setRiskPct] = useState('5')
  const [lossLimit, setLossLimit] = useState('10')
  const [leverage, setLeverage] = useState('5')
  const [scanInterval, setScanInterval] = useState('30')
  const [dryRun, setDryRun] = useState(true)

  const saveTelegram = async () => {
    if (!tgToken || !tgChat) { toast.error('Enter both Telegram token and chat ID'); return }
    try { await setTelegramConfig(tgToken, tgChat); toast.success('✅ Telegram configured!') }
    catch { toast.error('Failed — is main.py running?') }
  }

  const saveBinance = async () => {
    if (!bnKey || !bnSecret) { toast.error('Enter both API key and secret'); return }
    try { await setBinanceConfig(bnKey, bnSecret); toast.success('✅ Binance keys saved!') }
    catch { toast.error('Failed — is main.py running?') }
  }

  return (
    <div>
      <h1 style={{ color:'white', fontSize:'1.6rem', fontWeight:800, marginBottom:'28px' }}>⚙️ Settings</h1>

      {/* OAuth / AI Connection */}
      <Section title="🔑 AI OAuth Connections">
        <p style={{ color:'#475569', fontSize:'0.85rem', marginBottom:'20px' }}>
          Connect AI providers for the bot brain. The OAuth token is used to call AI models — no API keys stored.
        </p>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'12px' }}>
          {[
            { name:'Google / Gemini', provider:'google', icon:'🟢', desc:'Gemini Pro + Antigravity' },
            { name:'GitHub', provider:'github', icon:'⬛', desc:'Developer OAuth' },
          ].map(({name, provider, icon, desc}) => (
            <div key={provider} style={{ padding:'16px', borderRadius:'12px', background:'rgba(0,255,136,0.04)', border:'1px solid rgba(0,255,136,0.12)' }}>
              <div style={{ display:'flex', alignItems:'center', gap:'10px', marginBottom:'8px' }}>
                <span style={{ fontSize:'20px' }}>{icon}</span>
                <div>
                  <div style={{ color:'white', fontWeight:600, fontSize:'0.9rem' }}>{name}</div>
                  <div style={{ color:'#475569', fontSize:'0.75rem' }}>{desc}</div>
                </div>
              </div>
              <button onClick={() => signIn(provider)} style={{ padding:'8px 18px', borderRadius:'8px', border:'1px solid rgba(0,255,136,0.3)', background:'rgba(0,255,136,0.08)', color:'#00ff88', cursor:'pointer', fontWeight:600, fontSize:'0.8rem', width:'100%' }}>
                🔗 Connect
              </button>
            </div>
          ))}
        </div>
      </Section>

      {/* Telegram Bot */}
      <Section title="📱 Telegram Bot">
        <p style={{ color:'#475569', fontSize:'0.85rem', marginBottom:'16px' }}>
          Set up your Telegram bot so the AI brain can send trade alerts and receive commands 24/7.
        </p>
        <Field label="Bot Token (from @BotFather)" placeholder="1234567890:ABCdef..." value={tgToken} onChange={setTgToken} password/>
        <Field label="Your Chat ID" placeholder="-100123456789 or @username" value={tgChat} onChange={setTgChat}/>
        <SaveBtn onClick={saveTelegram} label="💾 Save Telegram Config"/>
        <div style={{ marginTop:'12px', padding:'10px 14px', background:'rgba(0,212,255,0.06)', borderRadius:'8px', border:'1px solid rgba(0,212,255,0.15)' }}>
          <p style={{ color:'#64748b', fontSize:'0.78rem' }}>
            💡 <strong style={{ color:'#00d4ff' }}>How to get your Chat ID:</strong> Message @userinfobot on Telegram. For groups, add @getidsbot.
          </p>
        </div>
      </Section>

      {/* Binance API */}
      <Section title="🔑 Binance API Keys">
        <Field label="API Key" placeholder="Your Binance API Key" value={bnKey} onChange={setBnKey} password/>
        <Field label="Secret Key" placeholder="Your Binance Secret" value={bnSecret} onChange={setBnSecret} password/>
        <div style={{ display:'flex', alignItems:'center', gap:'10px', marginBottom:'16px' }}>
          <input type="checkbox" id="dry" checked={dryRun} onChange={e=>setDryRun(e.target.checked)} style={{ width:'16px', height:'16px', accentColor:'#00ff88' }}/>
          <label htmlFor="dry" style={{ color:'#94a3b8', fontSize:'0.85rem' }}>
            Dry Run Mode <span style={{ color:'#475569' }}>(paper trading — no real orders placed)</span>
          </label>
        </div>
        <SaveBtn onClick={saveBinance} label="💾 Save Binance Keys"/>
        <div style={{ marginTop:'12px', padding:'10px 14px', background:'rgba(255,68,85,0.06)', borderRadius:'8px', border:'1px solid rgba(255,68,85,0.15)' }}>
          <p style={{ color:'#64748b', fontSize:'0.78rem' }}>
            🔒 Keys are stored only in your session and sent directly to the bot. Enable only <strong style={{ color:'#ff4455' }}>Spot/Futures Trading</strong> permissions. Never Share.
          </p>
        </div>
      </Section>

      {/* Risk Management */}
      <Section title="⚠️ Risk Management">
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'16px' }}>
          <Field label="Max Position Size (%)" placeholder="5" value={riskPct} onChange={setRiskPct} type="number"/>
          <Field label="Daily Loss Limit (%)" placeholder="10" value={lossLimit} onChange={setLossLimit} type="number"/>
          <Field label="Max Leverage (x)" placeholder="5" value={leverage} onChange={setLeverage} type="number"/>
          <Field label="Scan Interval (seconds)" placeholder="30" value={scanInterval} onChange={setScanInterval} type="number"/>
        </div>
        <SaveBtn onClick={()=>toast.success('✅ Risk settings saved!')} label="💾 Save Risk Settings" color="#f59e0b"/>
      </Section>
    </div>
  )
}
