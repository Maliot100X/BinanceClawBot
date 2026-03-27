import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'KaiNova — Autonomous Crypto Trading Bot',
  description: '26 Binance Skills · OpenAI + Gemini OAuth · 24/7 Telegram Brain',
  keywords: ['crypto', 'trading bot', 'binance', 'AI', 'autonomous', 'DeFi'],
  openGraph: {
    title: 'KaiNova Trading Bot Dashboard',
    description: 'The world\'s most intelligent autonomous crypto trading platform',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
      </head>
      <body>{children}</body>
    </html>
  )
}
