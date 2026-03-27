import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

const SESSION_FILE = path.join(process.cwd(), '..', 'session.json')

export async function GET() {
  try {
    if (fs.existsSync(SESSION_FILE)) {
      const data = fs.readFileSync(SESSION_FILE, 'utf8')
      const session = JSON.parse(data)
      return NextResponse.json({
        connected: !!(session && session.access_token)
      })
    }
  } catch (e) {}

  return NextResponse.json({ connected: false })
}
