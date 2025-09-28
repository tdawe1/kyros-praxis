import { NextRequest, NextResponse } from 'next/server';
import { appendHistory, deleteHistory, getHistory, PacketEntry } from '@/lib/server/devlogs';

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const limit = Number(searchParams.get('limit') || '50');
  const items = getHistory(Number.isFinite(limit) ? limit : 50);
  return NextResponse.json({ items });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { target, mode, packet } = body || {};
    if (typeof target !== 'string' || typeof mode !== 'string') {
      return NextResponse.json({ error: 'target and mode are required' }, { status: 400 });
    }
    const saved: PacketEntry = appendHistory({ target, mode, packet });
    return NextResponse.json(saved, { status: 201 });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message || 'Invalid JSON' }, { status: 400 });
  }
}

export async function DELETE(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const id = searchParams.get('id');
  if (!id) return NextResponse.json({ error: 'id is required' }, { status: 400 });
  const ok = deleteHistory(id);
  return NextResponse.json({ ok });
}
