"use client";

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  Button,
  TextInput,
  TextArea,
  Dropdown,
  InlineNotification,
  Loading,
} from '@carbon/react';

type HistoryItem = {
  id: string;
  ts: string;
  target: string;
  mode: string;
  packet: unknown;
};

type AuditItem = {
  ts: string;
  action: string;
  targets: string[];
  mode: string;
  summary: string;
  payload_hash?: string;
};

export default function SuperPage() {
  const [target, setTarget] = useState('default');
  const [mode, setMode] = useState('send');
  const [packet, setPacket] = useState('');
  const [lastSent, setLastSent] = useState<HistoryItem | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [audit, setAudit] = useState<AuditItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const hist = await fetch('/api/super/history?limit=50').then((r) => r.json());
    setHistory(hist.items || []);
    const aud = await fetch('/api/super/audit?limit=50').then((r) => r.json());
    setAudit(aud.items || []);
  }

  useEffect(() => {
    refresh();
  }, []);

  const canSend = useMemo(() => target.trim().length > 0 && mode.trim().length > 0, [target, mode]);

  function buildCurl(escalate = false): string {
    const body = {
      target,
      mode,
      packet: safeParseJson(packet),
    };
    const data = JSON.stringify(body).replace(/"/g, '\\"');
    const url = escalate ? '/api/super/task/escalate' : '/api/super/task';
    return `curl -s -X POST '${url}' -H 'Content-Type: application/json' -d "${data}"`;
  }

  function safeParseJson(text: string): any {
    if (!text) return {};
    try { return JSON.parse(text); } catch { return text; }
  }

  async function send(escalate = false) {
    setBusy(true); setError(null); setToast(null);
    try {
      const res = await fetch(escalate ? '/api/super/task/escalate' : '/api/super/task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target, mode, packet: safeParseJson(packet) }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json?.error || 'Request failed');
      setLastSent(json.saved);
      setToast(escalate ? 'Sent + escalated' : 'Sent');
      await refresh();
    } catch (e: any) {
      setError(e?.message || 'Failed to send');
    } finally {
      setBusy(false);
    }
  }

  async function copyCurl(escalate = false) {
    const cmd = buildCurl(escalate);
    await navigator.clipboard.writeText(cmd);
    setToast('cURL copied to clipboard');
  }

  function onSelectRecent(item: HistoryItem) {
    setTarget(item.target);
    setMode(item.mode);
    setPacket(JSON.stringify(item.packet, null, 2));
  }

  return (
    <div className="cds--grid">
      <div className="cds--row">
        <div className="cds--col-lg-12">
          <h2 style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            Super Console
            <Link href="/review-plan" className="cds--link">Review Plan</Link>
          </h2>
          <p>Send packets to targets, escalate when needed, and inspect history/audit.</p>
        </div>
      </div>

      {toast && (
        <InlineNotification
          kind="success"
          title={toast}
          onClose={() => setToast(null)}
          lowContrast
        />
      )}
      {error && (
        <InlineNotification
          kind="error"
          title="Error"
          subtitle={error}
          onClose={() => setError(null)}
          lowContrast
        />
      )}

      <div className="cds--row" style={{ marginTop: 12 }}>
        <div className="cds--col-lg-8">
          <div style={{ display: 'grid', gap: 12 }}>
            <TextInput id="target" labelText="Target" value={target} onChange={(e) => setTarget(e.target.value)} />
            <Dropdown
              id="mode"
              titleText="Mode"
              label="Select mode"
              items={["send", "analyze", "plan", "execute"]}
              selectedItem={mode}
              onChange={({ selectedItem }) => setMode(String(selectedItem))}
            />
            <TextArea id="packet" labelText="Packet (JSON)" rows={12} value={packet} onChange={(e) => setPacket(e.target.value)} />
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <Button kind="primary" disabled={!canSend || busy} onClick={() => send(false)}>Send</Button>
              <Button kind="danger" disabled={!canSend || busy} onClick={() => send(true)}>Send + Escalate</Button>
              <Button kind="tertiary" disabled={!canSend} onClick={() => copyCurl(false)}>Copy cURL</Button>
              <Button kind="tertiary" disabled={!canSend} onClick={() => copyCurl(true)}>Copy cURL + Escalate</Button>
              {busy && <Loading withOverlay={false} description="Sending" />}
            </div>
          </div>
        </div>
        <div className="cds--col-lg-4">
          <h4>Recent Packets</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 420, overflow: 'auto' }}>
            {history.map((h) => (
              <button
                key={h.id}
                className="cds--btn cds--btn--ghost"
                style={{ justifyContent: 'flex-start' }}
                onClick={() => onSelectRecent(h)}
                title={h.id}
              >
                [{new Date(h.ts).toLocaleTimeString()}] {h.mode} → {h.target}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="cds--row" style={{ marginTop: 24 }}>
        <div className="cds--col-lg-12">
          <h4>Audit</h4>
          <div className="cds--data-table-container">
            <table className="cds--data-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Action</th>
                  <th>Target(s)</th>
                  <th>Mode</th>
                  <th>Summary</th>
                  <th>Hash</th>
                </tr>
              </thead>
              <tbody>
                {audit.map((a, idx) => (
                  <tr key={idx}>
                    <td>{new Date(a.ts).toLocaleString()}</td>
                    <td>{a.action}</td>
                    <td>{a.targets.join(', ')}</td>
                    <td>{a.mode}</td>
                    <td>{a.summary}</td>
                    <td><code>{a.payload_hash}</code></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="cds--row" style={{ marginTop: 24 }}>
        <div className="cds--col-lg-12">
          <h4>Run Timeline (segmented)</h4>
          <SegmentedBar segments={[
            { label: 'packet', color: '#8a3ffc', width: 20 },
            { label: 'exec', color: '#0f62fe', width: 60 },
            { label: 'done', color: '#24a148', width: 20 },
          ]} />
        </div>
      </div>
    </div>
  );
}

function SegmentedBar({ segments }: { segments: { label: string; color: string; width: number }[] }) {
  return (
    <div style={{ display: 'flex', width: '100%', height: 18, borderRadius: 4, overflow: 'hidden', border: '1px solid var(--cds-border-subtle-01)' }}>
      {segments.map((s, i) => (
        <div key={i} style={{ width: `${s.width}%`, background: s.color, position: 'relative' }} title={s.label}>
          <span style={{ position: 'absolute', left: 4, top: -18, fontSize: 12 }}>{s.label}</span>
        </div>
      ))}
    </div>
  );
}

