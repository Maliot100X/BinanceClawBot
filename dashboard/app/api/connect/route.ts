import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  try {
    // We no longer rely on frontend session.json writes. 
    // The backend purely acts as a read-only bridge to the FastAPI Python engine.
    console.log("✅ Connection ping received (No-op pass-through)")
    return NextResponse.json({ success: true, mode: 'api-proxy' })
  } catch (e: any) {
    console.error("[Connect API Error]", e.message)
    return NextResponse.json({ error: "failed" }, { status: 500 })
  }
}
