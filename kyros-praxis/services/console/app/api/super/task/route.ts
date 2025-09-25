import { NextRequest, NextResponse } from 'next/server';
import { appendAudit, appendHistory, hashPayload } from '@/lib/server/devlogs';

async function handleSend(req: NextRequest, action: 'send' | 'escalate') {
  try {
    const body = await req.json();
    const { target, mode, packet } = body || {};
    if (typeof target !== 'string' || typeof mode !== 'string') {
      return NextResponse.json({ error: 'target and mode are required' }, { status: 400 });
    }
    const saved = appendHistory({ target, mode, packet });
    const payloadHash = hashPayload(packet);
    appendAudit({
      ts: new Date().toISOString(),
      action,
      targets: [target],
      mode,
      summary: `${action.toUpperCase()} ${target} (${mode})`,
      run_ids: [],
      payload_hash: payloadHash,
    });

    // Optionally forward to orchestrator here in the future
    return NextResponse.json({ ok: true, saved });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message || 'Invalid JSON' }, { status: 400 });
  }
}

export async function POST(req: NextRequest) {
  return handleSend(req, 'send');
}
