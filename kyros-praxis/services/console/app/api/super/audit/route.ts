import { NextRequest, NextResponse } from 'next/server';
import { getAudit } from '@/lib/server/devlogs';

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const limit = Number(searchParams.get('limit') || '50');
  const mode = searchParams.get('mode') || undefined;
  const from = searchParams.get('from') || undefined;
  const to = searchParams.get('to') || undefined;
  const items = getAudit({ limit, mode, from, to });
  return NextResponse.json({ items });
}
