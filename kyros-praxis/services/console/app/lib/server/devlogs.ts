import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { devlogsDir } from './repoRoot';
import { validateFilename } from './pathSecurity';

export interface PacketEntry {
  id: string;
  ts: string; // ISO timestamp
  target: string;
  mode: string; // e.g., send | escalate
  packet: unknown;
}

export interface AuditEntry {
  ts: string; // ISO timestamp
  action: 'send' | 'escalate' | 'retry' | 'replay';
  targets: string[];
  mode: string;
  summary: string;
  run_ids?: string[];
  payload_hash?: string;
}

function filePath(name: string): string {
  const safeName = validateFilename(name);
  return path.join(devlogsDir(), safeName);
}

function ensureFile(file: string, initial: string): void {
  const dir = path.dirname(file);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  if (!fs.existsSync(file)) fs.writeFileSync(file, initial, 'utf8');
}

function readJsonArray<T>(file: string): T[] {
  ensureFile(file, '[]');
  try {
    const raw = fs.readFileSync(file, 'utf8');
    const data = JSON.parse(raw);
    return Array.isArray(data) ? (data as T[]) : [];
  } catch (err) {
    // If corrupted, archive and reset
    const backup = `${file}.${Date.now()}.bak`;
    try { fs.copyFileSync(file, backup); } catch {}
    fs.writeFileSync(file, '[]', 'utf8');
    return [];
  }
}

function writeJsonArray<T>(file: string, data: T[]): void {
  const tmp = `${file}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(data, null, 2), 'utf8');
  fs.renameSync(tmp, file);
}

export function hashPayload(obj: unknown): string {
  const str = typeof obj === 'string' ? obj : JSON.stringify(obj);
  return crypto.createHash('sha256').update(str || '').digest('hex').slice(0, 16);
}

// History API
const HISTORY_FILE = filePath('super-history.json');

export function getHistory(limit = 50): PacketEntry[] {
  const all = readJsonArray<PacketEntry>(HISTORY_FILE);
  return all.slice(-limit).reverse();
}

export function appendHistory(entry: Omit<PacketEntry, 'id' | 'ts'>): PacketEntry {
  const now = new Date().toISOString();
  const id = crypto.randomBytes(8).toString('hex');
  const payload: PacketEntry = { id, ts: now, ...entry };
  const all = readJsonArray<PacketEntry>(HISTORY_FILE);
  const updated = [...all, payload].slice(-50); // keep last 50
  writeJsonArray(HISTORY_FILE, updated);
  return payload;
}

export function deleteHistory(id: string): boolean {
  const all = readJsonArray<PacketEntry>(HISTORY_FILE);
  const updated = all.filter((e) => e.id !== id);
  const changed = updated.length !== all.length;
  if (changed) writeJsonArray(HISTORY_FILE, updated);
  return changed;
}

// Audit API
const AUDIT_FILE = filePath('super-audit.json');

export interface AuditQuery {
  limit?: number;
  mode?: string;
  from?: string; // ISO
  to?: string; // ISO
}

export function getAudit(query: AuditQuery = {}): AuditEntry[] {
  let items = readJsonArray<AuditEntry>(AUDIT_FILE);
  if (query.mode) items = items.filter((a) => a.mode === query.mode);
  if (query.from) {
    const fromTs = Date.parse(query.from);
    if (!Number.isNaN(fromTs)) items = items.filter((a) => Date.parse(a.ts) >= fromTs);
  }
  if (query.to) {
    const toTs = Date.parse(query.to);
    if (!Number.isNaN(toTs)) items = items.filter((a) => Date.parse(a.ts) <= toTs);
  }
  items = items.reverse();
  if (query.limit && query.limit > 0) items = items.slice(0, query.limit);
  return items;
}

export function appendAudit(entry: AuditEntry): void {
  const items = readJsonArray<AuditEntry>(AUDIT_FILE);
  const updated = [...items, entry];
  writeJsonArray(AUDIT_FILE, updated);
}

