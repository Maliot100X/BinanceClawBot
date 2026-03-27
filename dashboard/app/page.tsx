'use client'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Stars, Text, Float, MeshDistortMaterial } from '@react-three/drei'
import { useRef, useState, useEffect, Suspense } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import * as THREE from 'three'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

// ── 3D Globe ─────────────────────────────────────────────────────────────────
function GlobeCore() {
  const mesh = useRef<THREE.Mesh>(null!)
  useFrame((s) => { mesh.current.rotation.y += 0.003; mesh.current.rotation.x = Math.sin(s.clock.elapsedTime * 0.2) * 0.1 })
  return (
    <Float speed={1.4} rotationIntensity={0.4} floatIntensity={0.6}>
      <mesh ref={mesh}>
        <sphereGeometry args={[1.5, 64, 64]} />
        <MeshDistortMaterial color="#00ff88" wireframe distort={0.15} speed={2} transparent opacity={0.25} />
      </mesh>
      <mesh>
        <sphereGeometry args={[1.52, 64, 64]} />
        <meshBasicMaterial color="#00ff88" wireframe transparent opacity={0.07} />
      </mesh>
    </Float>
  )
}

function Particles() {
  const pts = useRef<THREE.Points>(null!)
  const count = 800
  const positions = new Float32Array(count * 3).map(() => (Math.random() - 0.5) * 20)
  useFrame(() => { if (pts.current) pts.current.rotation.y += 0.0004 })
  return (
    <points ref={pts}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.04} color="#00d4ff" transparent opacity={0.6} />
    </points>
  )
}

function Scene3D() {
  return (
    <>
      <ambientLight intensity={0.3} />
      <pointLight position={[5,5,5]} intensity={1} color="#00ff88" />
      <pointLight position={[-5,-5,-5]} intensity={0.5} color="#00d4ff" />
      <Stars radius={80} depth={40} count={3000} factor={3} fade speed={0.5} />
      <Particles />
      <GlobeCore />
      <OrbitControls enablePan={false} enableZoom={false} autoRotate autoRotateSpeed={0.3} />
    </>
  )
}

// ── Mock data ─────────────────────────────────────────────────────────────────
const genPriceData = () => Array.from({length:20},(_,i)=>({t:i,v:60000+Math.random()*3000-1500}))

// ── Stat Card ─────────────────────────────────────────────────────────────────
function StatCard({label,value,sub,color='#00ff88',icon}:{label:string,value:string,sub?:string,color?:string,icon:string}) {
  return (
    <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{duration:0.5}}
      className="glass p-4 rounded-2xl border" style={{borderColor:`${color}22`,background:`${color}06`}}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{icon}</span>
        <span className="text-xs text-slate-400 uppercase tracking-widest">{label}</span>
      </div>
      <div className="text-2xl font-bold" style={{color}}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
    </motion.div>
  )
}

// ── Signal Row ────────────────────────────────────────────────────────────────
function SignalRow({symbol,signal,confidence,rsi,price}:{symbol:string,signal:string,confidence:number,rsi:number,price:number}) {
  const c = signal==='BUY'?'#00ff88':signal==='SELL'?'#ff4455':'#facc15'
  const bar = Math.round(confidence/10)
  return (
    <motion.div initial={{opacity:0,x:-20}} animate={{opacity:1,x:0}}
      className="flex items-center justify-between p-3 rounded-xl mb-2"
      style={{background:`${c}08`,border:`1px solid ${c}22`}}>
      <div className="flex items-center gap-3">
        <div className="w-2 h-2 rounded-full" style={{background:c,boxShadow:`0 0 8px ${c}`}}/>
        <span className="font-mono font-bold text-sm">{symbol}</span>
        <span className="text-xs px-2 py-0.5 rounded-full" style={{background:`${c}22`,color:c}}>{signal}</span>
      </div>
      <div className="flex items-center gap-4 text-xs text-slate-400">
        <span>RSI {rsi}</span>
        <span className="font-mono text-slate-300">${price.toLocaleString()}</span>
        <div className="flex gap-0.5">
          {Array.from({length:10},(_,i)=>(
            <div key={i} className="w-1 h-3 rounded-sm" style={{background:i<bar?c:'#1e293b'}}/>
          ))}
          <span className="ml-1" style={{color:c}}>{confidence.toFixed(0)}%</span>
        </div>
      </div>
    </motion.div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [priceData] = useState(genPriceData)
  const [active, setActive] = useState<'portfolio'|'signals'|'positions'|'skills'>('signals')
  const [botActive, setBotActive] = useState(true)
  const [signals] = useState([
    {symbol:'BTCUSDT',signal:'BUY',confidence:82,rsi:54,price:67420},
    {symbol:'ETHUSDT',signal:'BUY',confidence:76,rsi:51,price:3180},
    {symbol:'SOLUSDT',signal:'HOLD',confidence:48,rsi:62,price:172},
    {symbol:'BNBUSDT',signal:'SELL',confidence:71,rsi:74,price:598},
    {symbol:'XRPUSDT',signal:'BUY',confidence:69,rsi:46,price:0.52},
  ])
  const [skills] = useState([
    'algo','alpha','assets','convert','derivatives-coin-futures','derivatives-options',
    'derivatives-portfolio-margin','derivatives-portfolio-margin-pro','derivatives-usds-futures',
    'fiat','margin-trading','onchain-pay','p2p','simple-earn','spot','square-post',
    'sub-account','vip-loan','tokenized-securities','crypto-market-rank','meme-rush',
    'query-address-info','query-token-audit','query-token-info','trading-signal'
  ])

  return (
    <div style={{minHeight:'100vh',background:'#020408',fontFamily:'Inter,sans-serif'}}>

      {/* 3D Hero */}
      <div style={{height:'100vh',position:'relative'}}>
        <Canvas camera={{position:[0,0,5],fov:50}} style={{position:'absolute',inset:0}}>
          <Suspense fallback={null}><Scene3D/></Suspense>
        </Canvas>

        {/* Overlay */}
        <div style={{position:'absolute',inset:0,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',pointerEvents:'none'}}>
          <motion.div initial={{opacity:0,y:-30}} animate={{opacity:1,y:0}} transition={{duration:1}}>
            <div style={{textAlign:'center',pointerEvents:'none'}}>
              <div style={{fontSize:'0.75rem',letterSpacing:'0.4em',color:'#00ff88',marginBottom:'12px',opacity:0.8}}>KAANOVA TRADING SYSTEM</div>
              <h1 style={{fontSize:'clamp(2.5rem,7vw,5rem)',fontWeight:800,background:'linear-gradient(135deg,#00ff88,#00d4ff)',WebkitBackgroundClip:'text',WebkitTextFillColor:'transparent',lineHeight:1.1}}>
                Autonomous<br/>Crypto Brain
              </h1>
              <p style={{color:'#64748b',marginTop:'16px',fontSize:'1.1rem'}}>26 Binance Skills · OpenAI + Gemini OAuth · 24/7 Telegram Bot</p>
            </div>
          </motion.div>
          <motion.div initial={{opacity:0}} animate={{opacity:1}} transition={{delay:0.8}} style={{marginTop:'40px',pointerEvents:'all'}}>
            <button onClick={()=>document.getElementById('dashboard')?.scrollIntoView({behavior:'smooth'})}
              style={{background:'linear-gradient(135deg,#00ff8833,#00d4ff22)',border:'1px solid #00ff8855',color:'#00ff88',padding:'14px 40px',borderRadius:'50px',cursor:'pointer',fontSize:'1rem',fontWeight:600,backdropFilter:'blur(12px)',boxShadow:'0 0 30px #00ff8822'}}>
              Launch Dashboard ↓
            </button>
          </motion.div>
        </div>

        {/* Status pill */}
        <div style={{position:'absolute',top:'24px',right:'24px'}}>
          <div style={{display:'flex',alignItems:'center',gap:'8px',background:'rgba(0,0,0,0.6)',border:'1px solid #00ff8833',borderRadius:'50px',padding:'8px 16px',backdropFilter:'blur(12px)'}}>
            <div style={{width:'8px',height:'8px',borderRadius:'50%',background:botActive?'#00ff88':'#ff4455',boxShadow:`0 0 10px ${botActive?'#00ff88':'#ff4455'}`}}/>
            <span style={{color:botActive?'#00ff88':'#ff4455',fontSize:'0.8rem',fontWeight:600}}>{botActive?'BOT ACTIVE':'BOT PAUSED'}</span>
          </div>
        </div>
      </div>

      {/* Dashboard */}
      <div id="dashboard" style={{maxWidth:'1400px',margin:'0 auto',padding:'40px 24px'}}>

        {/* Stats row */}
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(180px,1fr))',gap:'16px',marginBottom:'32px'}}>
          <StatCard label="Portfolio" value="$24,830" sub="+$840 today" icon="💰" color="#00ff88"/>
          <StatCard label="Daily PnL" value="+3.51%" sub="$840.22" icon="📈" color="#00d4ff"/>
          <StatCard label="Open Positions" value="3" sub="BTCUSDT · ETHUSDT · SOL" icon="📋" color="#a855f7"/>
          <StatCard label="Active Skills" value="26" sub="All skills loaded" icon="🔧" color="#f59e0b"/>
          <StatCard label="OAuth" value="OpenAI ✓" sub="Gemini ✓ · Antigravity ✓" icon="🔑" color="#ec4899"/>
          <StatCard label="Mode" value="LIVE 🟢" sub="30s scan interval" icon="⚡" color="#00ff88"/>
        </div>

        {/* Nav tabs */}
        <div style={{display:'flex',gap:'8px',marginBottom:'24px',background:'rgba(0,255,136,0.04)',border:'1px solid rgba(0,255,136,0.1)',borderRadius:'12px',padding:'6px'}}>
          {(['signals','portfolio','positions','skills'] as const).map(t=>(
            <button key={t} onClick={()=>setActive(t)}
              style={{flex:1,padding:'10px',borderRadius:'8px',border:'none',cursor:'pointer',fontWeight:600,fontSize:'0.85rem',
                background:active===t?'linear-gradient(135deg,#00ff8822,#00d4ff11)':'transparent',
                color:active===t?'#00ff88':'#475569',
                boxShadow:active===t?'0 0 20px #00ff8811':'none',transition:'all 0.2s'}}>
              {t.charAt(0).toUpperCase()+t.slice(1)}
            </button>
          ))}
        </div>

        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'24px'}}>
          {/* Left panel */}
          <div>
            <AnimatePresence mode="wait">
              {active==='signals' && (
                <motion.div key="sig" initial={{opacity:0,y:12}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-12}}>
                  <div className="glass" style={{padding:'24px',borderRadius:'20px',border:'1px solid rgba(0,255,136,0.12)'}}>
                    <h2 style={{color:'#00ff88',marginBottom:'16px',fontSize:'1.1rem',fontWeight:700}}>📡 Live Signals</h2>
                    {signals.map(s=><SignalRow key={s.symbol} {...s}/>)}
                  </div>
                </motion.div>
              )}
              {active==='portfolio' && (
                <motion.div key="port" initial={{opacity:0,y:12}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-12}}>
                  <div className="glass" style={{padding:'24px',borderRadius:'20px',border:'1px solid rgba(0,212,255,0.12)'}}>
                    <h2 style={{color:'#00d4ff',marginBottom:'16px',fontSize:'1.1rem',fontWeight:700}}>💼 Portfolio</h2>
                    {[['BTC','0.3824','$25,782'],['ETH','4.12','$13,090'],['USDT','8,420.00','$8,420']].map(([a,bal,val])=>(
                      <div key={a} style={{display:'flex',justifyContent:'space-between',padding:'12px 0',borderBottom:'1px solid rgba(255,255,255,0.05)'}}>
                        <span style={{color:'#94a3b8',fontWeight:600}}>{a}</span>
                        <span style={{color:'white',fontMono:'monospace'}}>{bal}</span>
                        <span style={{color:'#00d4ff'}}>{val}</span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
              {active==='positions' && (
                <motion.div key="pos" initial={{opacity:0,y:12}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-12}}>
                  <div className="glass" style={{padding:'24px',borderRadius:'20px',border:'1px solid rgba(168,85,247,0.12)'}}>
                    <h2 style={{color:'#a855f7',marginBottom:'16px',fontSize:'1.1rem',fontWeight:700}}>📋 Positions</h2>
                    {[['BTCUSDT','BUY','0.001','$67,420','$65,800','$70,000'],['ETHUSDT','BUY','0.1','$3,180','$3,050','$3,400']].map(([sym,side,qty,entry,sl,tp])=>(
                      <div key={sym} style={{padding:'12px',marginBottom:'8px',background:'rgba(168,85,247,0.06)',borderRadius:'12px',border:'1px solid rgba(168,85,247,0.15)'}}>
                        <div style={{display:'flex',justifyContent:'space-between',marginBottom:'4px'}}>
                          <span style={{color:'white',fontWeight:700}}>{sym}</span>
                          <span style={{color:side==='BUY'?'#00ff88':'#ff4455',fontSize:'0.8rem',fontWeight:600}}>{side}</span>
                        </div>
                        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:'4px',fontSize:'0.75rem',color:'#64748b'}}>
                          <span>Qty: {qty}</span><span>Entry: {entry}</span><span>SL: {sl}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
              {active==='skills' && (
                <motion.div key="sk" initial={{opacity:0,y:12}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-12}}>
                  <div className="glass" style={{padding:'24px',borderRadius:'20px',border:'1px solid rgba(245,158,11,0.12)'}}>
                    <h2 style={{color:'#f59e0b',marginBottom:'16px',fontSize:'1.1rem',fontWeight:700}}>🔧 Binance Skills (26)</h2>
                    <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'6px'}}>
                      {skills.map(s=>(
                        <div key={s} style={{padding:'6px 10px',borderRadius:'8px',background:'rgba(245,158,11,0.06)',border:'1px solid rgba(245,158,11,0.15)',fontSize:'0.72rem',color:'#94a3b8',display:'flex',alignItems:'center',gap:'6px'}}>
                          <span style={{color:'#f59e0b',fontSize:'8px'}}>●</span>{s}
                        </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Right panel — Price Chart */}
          <div>
            <div className="glass" style={{padding:'24px',borderRadius:'20px',border:'1px solid rgba(0,255,136,0.1)'}}>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'16px'}}>
                <h2 style={{color:'#00ff88',fontSize:'1.1rem',fontWeight:700}}>📈 BTC/USDT</h2>
                <span style={{color:'#00d4ff',fontSize:'0.8rem'}}>Live · 1h</span>
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={priceData}>
                  <defs>
                    <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00ff88" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#00ff88" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="t" hide/>
                  <YAxis domain={['dataMin-500','dataMax+500']} hide/>
                  <Tooltip contentStyle={{background:'#0f172a',border:'1px solid #00ff8833',borderRadius:'8px',color:'#00ff88'}} formatter={(v:number)=>`$${v.toFixed(0)}`}/>
                  <Area type="monotone" dataKey="v" stroke="#00ff88" fill="url(#priceGrad)" strokeWidth={2}/>
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Bot Controls */}
            <div className="glass" style={{padding:'20px',borderRadius:'20px',border:'1px solid rgba(0,255,136,0.1)',marginTop:'16px'}}>
              <h2 style={{color:'#e2e8f0',fontSize:'1rem',fontWeight:700,marginBottom:'16px'}}>⚡ Bot Controls</h2>
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'10px'}}>
                {[
                  {label:'▶ Start Bot',action:()=>setBotActive(true),color:'#00ff88'},
                  {label:'⏹ Stop Bot',action:()=>setBotActive(false),color:'#ff4455'},
                  {label:'🔍 Scan Now',action:()=>alert('Scan triggered via Telegram /scan'),color:'#00d4ff'},
                  {label:'📊 Portfolio',action:()=>setActive('portfolio'),color:'#a855f7'},
                ].map(({label,action,color})=>(
                  <button key={label} onClick={action}
                    style={{padding:'12px',borderRadius:'10px',border:`1px solid ${color}33`,background:`${color}11`,color,cursor:'pointer',fontWeight:600,fontSize:'0.85rem',transition:'all 0.2s',boxShadow:'none'}}
                    onMouseEnter={e=>(e.currentTarget.style.boxShadow=`0 0 20px ${color}33`)}
                    onMouseLeave={e=>(e.currentTarget.style.boxShadow='none')}>
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Auth Status */}
            <div className="glass" style={{padding:'20px',borderRadius:'20px',border:'1px solid rgba(236,72,153,0.12)',marginTop:'16px'}}>
              <h2 style={{color:'#ec4899',fontSize:'1rem',fontWeight:700,marginBottom:'12px'}}>🔑 OAuth Status</h2>
              {[['OpenAI','✓ Authenticated','#00ff88'],['Gemini CLI','✓ Authenticated','#00ff88'],['Antigravity','⟳ Connect','#facc15']].map(([name,status,color])=>(
                <div key={name} style={{display:'flex',justifyContent:'space-between',padding:'8px 0',borderBottom:'1px solid rgba(255,255,255,0.04)'}}>
                  <span style={{color:'#94a3b8',fontSize:'0.85rem'}}>{name}</span>
                  <span style={{color,fontSize:'0.85rem',fontWeight:600}}>{status}</span>
                </div>
              ))}
              <button style={{width:'100%',marginTop:'12px',padding:'10px',borderRadius:'10px',border:'1px solid rgba(236,72,153,0.3)',background:'rgba(236,72,153,0.08)',color:'#ec4899',cursor:'pointer',fontWeight:600,fontSize:'0.85rem'}}>
                🔗 Connect OAuth
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div style={{textAlign:'center',marginTop:'60px',padding:'20px',color:'#334155',fontSize:'0.8rem'}}>
          <p>KaiNova · 26 Binance Skills · OpenAI + Gemini + Antigravity OAuth · Telegram @KaiNovaBot · 24/7</p>
        </div>
      </div>
    </div>
  )
}
