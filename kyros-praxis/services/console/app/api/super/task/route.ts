import { NextRequest, NextResponse } from 'next/server';
import { appendAudit, appendHistory, hashPayload } from '@/lib/server/devlogs';
import { SuperConsoleFormSchema } from '@/lib/validation';

async function handleSend(req: NextRequest, action: 'send' | 'escalate') {
  try {
    const body = await req.json();
    
    // Validate and sanitize input using schema
    const validation = SuperConsoleFormSchema.safeParse(body);
    if (!validation.success) {
      const errorMessages = validation.error.errors.map(e => e.message).join(', ');
      return NextResponse.json({ 
        error: `Input validation failed: ${errorMessages}` 
      }, { status: 400 });
    }

    const { target, mode, packet: sanitizedPacket } = validation.data;
    
    // Parse the sanitized JSON packet
    let packet;
    try {
      packet = JSON.parse(sanitizedPacket);
    } catch {
      packet = sanitizedPacket; // Use as string if not valid JSON
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
    return NextResponse.json({ error: err?.message || 'Invalid request' }, { status: 400 });
  }
}

export async function POST(req: NextRequest) {
  return handleSend(req, 'send');
}
