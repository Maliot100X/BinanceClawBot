import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/status', {
        headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        },
        cache: 'no-store'
    });
    
    if (res.ok) {
        const data = await res.json();
        // Correct path: data.brain.status
        const statusObj = data.brain?.status || data.oauth || {};
        const isConnected = Object.values(statusObj).some(v => v === true);
        return NextResponse.json({ connected: isConnected });
    }
  } catch (e: any) {
    console.error("[Python Sync Error] Failed to reach FastAPI backend:", e.message);
  }

  return NextResponse.json({ connected: false });
}
