'use client';

import { ReactNode, useCallback, useState, useRef, useEffect } from 'react';

export interface SplitPaneProps {
  left: ReactNode;
  right: ReactNode;
  defaultSplit?: number; // 0-100, percentage for left pane
  minLeftWidth?: number;
  minRightWidth?: number;
}

export function SplitPane({
  left,
  right,
  defaultSplit = 60,
  minLeftWidth = 300,
  minRightWidth = 300,
}: SplitPaneProps) {
  const [split, setSplit] = useState(defaultSplit);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = useCallback(() => {
    setIsDragging(true);
  }, []);

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return;

      const container = containerRef.current;
      const containerRect = container.getBoundingClientRect();
      const x = e.clientX - containerRect.left;
      const percentage = (x / containerRect.width) * 100;

      // Enforce minimum widths
      const minLeftPercent = (minLeftWidth / containerRect.width) * 100;
      const maxLeftPercent = 100 - (minRightWidth / containerRect.width) * 100;

      const newSplit = Math.max(minLeftPercent, Math.min(maxLeftPercent, percentage));
      setSplit(newSplit);
    },
    [isDragging, minLeftWidth, minRightWidth]
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';

      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  return (
    <div
      ref={containerRef}
      style={{
        display: 'flex',
        height: '100%',
        width: '100%',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          width: `${split}%`,
          height: '100%',
          overflow: 'hidden',
        }}
      >
        {left}
      </div>

      <div
        onMouseDown={handleMouseDown}
        style={{
          width: '4px',
          height: '100%',
          cursor: 'col-resize',
          backgroundColor: isDragging ? '#0066cc' : '#333',
          transition: isDragging ? 'none' : 'background-color 0.2s',
        }}
        onMouseEnter={(e) => {
          if (!isDragging) {
            e.currentTarget.style.backgroundColor = '#0066cc';
          }
        }}
        onMouseLeave={(e) => {
          if (!isDragging) {
            e.currentTarget.style.backgroundColor = '#333';
          }
        }}
      />

      <div
        style={{
          width: `${100 - split}%`,
          height: '100%',
          overflow: 'auto',
        }}
      >
        {right}
      </div>
    </div>
  );
}
