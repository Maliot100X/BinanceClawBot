import { NextResponse } from 'next/server'

// Interface for the global session object
interface OpenAISession {
  access_token: string
  refresh_token: string
  expires_at: number
}

// Ensure global type safety
declare global {
  var openaiSession: OpenAISession | undefined
}

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { access_token, refresh_token, expires_at } = body

    // Store in global for local testing as requested by user
    // Note: This persists in local development but not in serverless prod
    global.openaiSession = {
      access_token,
      refresh_token,
      expires_at
    }

    console.log("✅ OpenAPI Session bridged from CLI")
    return NextResponse.json({ success: true })
  } catch (e: any) {
    console.error("[Connect API Error]", e.message)
    return NextResponse.json({ error: "failed" }, { status: 500 })
  }
}
