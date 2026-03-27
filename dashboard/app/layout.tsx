import { Toaster } from 'react-hot-toast'
import { Providers } from './providers'
import { Navbar } from './components/Navbar'

export const metadata = {
  title: 'KaiNova BinanceClawBot',
  description: 'Autonomous AI Crypto Trading Platform',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, background: '#020408', fontFamily: 'system-ui, -apple-system, sans-serif', color: 'white' }}>
        <Providers>
          <Navbar />
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
