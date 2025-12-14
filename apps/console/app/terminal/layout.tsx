import { ReactNode } from 'react';

export default function TerminalLayout({ children }: { children: ReactNode }) {
  return (
    <div style={{ height: '100vh', overflow: 'hidden', margin: 0, padding: 0 }}>
      {children}
    </div>
  );
}
