'use client';

import dynamic from 'next/dynamic';

// Import Terminal dynamically to avoid SSR issues
const Terminal = dynamic(
  () => import('../terminal/components/Terminal').then((mod) => ({ default: mod.Terminal })),
  { 
    ssr: false,
    loading: () => <div style={{ padding: '20px', color: '#ccc' }}>Loading terminal...</div> 
  }
);

export default function TerminalTestPage() {
  return (
    <div style={{ height: '100vh', width: '100vw', backgroundColor: '#0a0d13' }}>
      <Terminal />
    </div>
  );
}
