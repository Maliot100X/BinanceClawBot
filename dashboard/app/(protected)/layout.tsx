'use client'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import Sidebar from '@/components/Sidebar'
import FloatingBot from '@/components/FloatingBot'
import { Toaster } from 'react-hot-toast'

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (status === 'unauthenticated') router.push('/login')
  }, [status])

  if (status === 'loading') {
    return (
      <div style={{ minHeight:'100vh', background:'#020408', display:'flex', alignItems:'center', justifyContent:'center' }}>
        <div style={{ textAlign:'center' }}>
          <div style={{ fontSize:'48px', marginBottom:'16px' }}>🤖</div>
          <div style={{ color:'#00ff88', fontSize:'1rem' }}>Loading KaiNova...</div>
        </div>
      </div>
    )
  }

  if (!session) return null

  return (
    <div style={{ display:'flex', minHeight:'100vh', background:'#020408' }}>
      <Sidebar />
      <main style={{ flex:1, marginLeft:'220px', padding:'32px', minHeight:'100vh' }}>
        {children}
      </main>
      <FloatingBot />
      <Toaster position="top-right" toastOptions={{ style:{ background:'#0f172a', color:'#e2e8f0', border:'1px solid rgba(0,255,136,0.2)' } }} />
    </div>
  )
}
