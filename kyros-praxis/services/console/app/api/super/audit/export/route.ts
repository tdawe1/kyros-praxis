import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { devlogsDir } from '../../../../lib/server/repoRoot';

export async function POST() {
  const file = path.join(devlogsDir(), 'super-audit.json');
  if (!fs.existsSync(file)) {
    return NextResponse.json({ error: 'No audit log found' }, { status: 404 });
  }
  const data = fs.readFileSync(file);
  const res = new NextResponse(data, {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Content-Disposition': `attachment; filename="super-audit.json"`,
      'Cache-Control': 'no-store',
    },
  });
  return res;
}
