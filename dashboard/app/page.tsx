'use client'
import Link from 'next/link'

export default function Home() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '70vh',
      textAlign: 'center',
      padding: '0 20px'
    }}>
      <div style={{
        fontSize: '64px',
        marginBottom: '24px',
        animation: 'float 3s ease-in-out infinite'
      }}>🦾</div>
      
      <h1 style={{
        fontSize: '3.5rem',
        fontWeight: 900,
        marginBottom: '16px',
        background: 'linear-gradient(135deg, #00ff88, #00d4ff)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        letterSpacing: '-1px'
      }}>
        KaiNova BinanceClawBot
      </h1>
      
      <p style={{
        fontSize: '1.25rem',
        color: '#94a3b8',
        maxWidth: '600px',
        lineHeight: '1.6',
        marginBottom: '40px'
      }}>
        The ultimate autonomous AI crypto trading platform. 
        26 Binance Skills. 24/7 AI Brain. Institutional-grade execution.
      </p>
      
      <div style={{ display: 'flex', gap: '20px' }}>
        <Link href="/dashboard" style={{
          padding: '16px 32px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #00ff88, #00d4ff)',
          color: '#020617',
          textDecoration: 'none',
          fontWeight: 700,
          fontSize: '1.1rem',
          boxShadow: '0 10px 20px rgba(0,255,136,0.2)',
          transition: 'transform 0.2s'
        }}>
          Launch Dashboard
        </Link>
        <Link href="/login" style={{
          padding: '16px 32px',
          borderRadius: '12px',
          background: 'rgba(255,255,255,0.05)',
          border: '1px solid rgba(255,255,255,0.1)',
          color: 'white',
          textDecoration: 'none',
          fontWeight: 600,
          fontSize: '1.1rem'
        }}>
          Connect Brain
        </Link>
      </div>
      
      <style jsx global>{`
        @keyframes float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
      `}</style>
    </div>
  )
}
