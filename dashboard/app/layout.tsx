'use client'
import { SessionProvider } from 'next-auth/react'
import './globals.css'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <title>BinanceClawBot — Autonomous Crypto Trading</title>
        <meta name="description" content="26 Binance Skills · OpenAI + Gemini OAuth · 24/7 Telegram AI Brain"/>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🤖</text></svg>"/>
      </head>
      <body className={inter.className} style={{ margin: 0, background: '#020408' }}>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  )
}
