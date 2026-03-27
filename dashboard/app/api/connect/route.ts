import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

const SESSION_FILE = path.join(process.cwd(), '..', 'session.json')

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { access_token, refresh_token, expires_at } = body

    const session = {
      access_token,
      refresh_token,
      expires_at
    }

    // Save to file for persistence across requests/reloads
    fs.writeFileSync(SESSION_FILE, JSON.stringify(session, null, 2))

    console.log("✅ OpenAI Session saved to session.json via CLI bridge")
    return NextResponse.json({ success: true })
  } catch (e: any) {
    console.error("[Connect API Error]", e.message)
    return NextResponse.json({ error: "failed" }, { status: 500 })
  }
}
