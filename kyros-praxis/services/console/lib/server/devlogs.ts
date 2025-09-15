import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

export type PacketEntry = {
  id: string;
  ts: number;
  target: string;
  mode: string;
  packet: any;
  action?: string;
};

type HistoryFile = { items: PacketEntry[] };

function logsDir() {
  const dir = path.resolve(process.cwd(), '.devlogs');
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function readJson<T>(file: string, fallback: T): T {
  try {
    const txt = fs.readFileSync(file, 'utf8');
    return JSON.parse(txt) as T;
  } catch {
    return fallback;
  }
}

function writeJson(file: string, data: any) {
  fs.writeFileSync(file, JSON.stringify(data, null, 2), 'utf8');
}

export function getHistory(limit = 50): PacketEntry[] {
  const file = path.resolve(logsDir(), 'super-history.json');
  const data = readJson<HistoryFile>(file, { items: [] });
  return (data.items || []).slice(0, limit);
}

export function appendHistory(entry: { target: string; mode: string; packet: any; action?: string }): PacketEntry {
  const file = path.resolve(logsDir(), 'super-history.json');
  const data = readJson<HistoryFile>(file, { items: [] });
  const saved: PacketEntry = {
    id: crypto.randomUUID(),
    ts: Date.now(),
    target: entry.target,
    mode: entry.mode,
    packet: entry.packet,
    action: entry.action,
  };
  data.items = [saved, ...(data.items || [])].slice(0, 50);
  writeJson(file, data);
  return saved;
}

export function deleteHistory(id: string): boolean {
  const file = path.resolve(logsDir(), 'super-history.json');
  const data = readJson<HistoryFile>(file, { items: [] });
  const before = data.items.length;
  data.items = (data.items || []).filter((x) => x.id !== id);
  writeJson(file, data);
  return data.items.length < before;
}

type AuditItem = {
  id: string;
  ts: number;
  action: string;
  targets?: string[];
  target?: string;
  from?: string;
  mode?: string;
  run_ids?: string[];
  summary?: string;
  payload_hash?: string;
  ok?: boolean;
  error?: string;
};

type AuditFile = { items: AuditItem[] };

export function appendAudit(item: Omit<AuditItem, 'id' | 'ts'>) {
  const file = path.resolve(logsDir(), 'super-audit.json');
  const data = readJson<AuditFile>(file, { items: [] });
  const saved: AuditItem = {
    id: crypto.randomUUID(),
    ts: Date.now(),
    ...item,
  };
  data.items = [saved, ...(data.items || [])].slice(0, 1000);
  writeJson(file, data);
}

export function getAudit(opts: { limit?: number; mode?: string; from?: string; to?: string }): AuditItem[] {
  const file = path.resolve(logsDir(), 'super-audit.json');
  const data = readJson<AuditFile>(file, { items: [] });
  let items = data.items || [];
  const limit = Math.max(10, Math.min(1000, Number(opts.limit || 200)));
  if (opts.mode) items = items.filter((x) => x.mode === opts.mode);
  if (opts.from) items = items.filter((x) => x.ts >= Number(opts.from));
  if (opts.to) items = items.filter((x) => x.ts <= Number(opts.to));
  return items.slice(0, limit);
}

export function hashPayload(obj: any): string {
  const json = JSON.stringify(obj ?? {});
  return crypto.createHash('sha256').update(json).digest('hex');
}

