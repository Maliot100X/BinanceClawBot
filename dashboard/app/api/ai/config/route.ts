import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { provider, api_key } = body

    // Proxy to local FastAPI or direct provider if needed
    // For now, we proxy to the local backend which handles persistence
    const response = await fetch('http://localhost:8000/ai/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, api_key })
    })

    if (!response.ok) {
      throw new Error('Failed to configure AI backend')
    }

    return NextResponse.json({ success: true })
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 })
  }
}
