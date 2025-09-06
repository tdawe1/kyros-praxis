import { NextRequest, NextResponse } from "next/server";
export async function POST(req: NextRequest) {
  const body = await req.json();
  const adkUrl = process.env.NEXT_PUBLIC_ADK_URL || "http://localhost:8080";
  const r = await fetch(`${adkUrl}/v1/runs/plan`, { method:"POST", headers:{ "content-type":"application/json" }, body: JSON.stringify(body) });
  const data = await r.json();
  return NextResponse.json(data, { status: r.status });
}