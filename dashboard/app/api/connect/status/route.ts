import { NextResponse } from 'next/server'

export async function GET() {
  const session = (global as any).openaiSession
  
  return NextResponse.json({
    connected: !!(session && session.access_token)
  })
}
