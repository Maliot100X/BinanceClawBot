import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { provider, api_key } = body
    console.log(`[Proxy] Connecting ${provider} AI Brain...`)

    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/ai/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, api_key })
    }).catch(err => {
      console.error(`[Proxy] Connection failed: ${err.message}`)
      throw new Error(`Local Backend Offline (${backendUrl}). Run start_all.py.`)
    })

    const data = await response.json()
    return NextResponse.json({ success: response.ok, ...data })
  } catch (error: any) {
    console.error(`[Proxy] Internal Error: ${error.message}`)
    return NextResponse.json({ success: false, error: error.message }, { status: 500 })
  }
}
