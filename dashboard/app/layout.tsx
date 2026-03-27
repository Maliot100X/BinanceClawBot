import type { Metadata } from 'next'
import './globals.css'
import { Providers } from './providers'

export const metadata: Metadata = {
  title: 'BinanceClawBot — Autonomous Crypto Trading',
  description: '26 Binance Skills · OpenAI + Gemini OAuth · 24/7 Telegram AI Brain',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
      </head>
      <body style={{ margin: 0, background: '#020408', fontFamily: 'Inter, sans-serif' }}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
