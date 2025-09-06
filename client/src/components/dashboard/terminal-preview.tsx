import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useLocation } from "wouter";
import { useState, useEffect } from "react";

export function TerminalPreview() {
  const [, navigate] = useLocation();
  const [terminalLines, setTerminalLines] = useState([
    "$ ./run-dev.sh",
    "== Kyros dev ==",
    "Console:      http://localhost:3001",
    "Orchestrator: http://localhost:8080/healthz",
    "Daemon (WS):  ws://localhost:8787/term",
    "",
    "[kyros-daemon] ws://localhost:8787/term",
    "[orchestrator] Starting on port 8080",
    "[console] Ready on http://localhost:3001",
  ]);
  const [showCursor, setShowCursor] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setShowCursor(prev => !prev);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const handleExpandTerminal = () => {
    navigate('/terminal');
  };

  return (
    <Card data-testid="card-terminal-preview">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Terminal</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleExpandTerminal}
            className="text-xs text-primary hover:underline"
            data-testid="button-expand-terminal"
          >
            Expand
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="bg-slate-800 text-green-400 p-4 rounded-b-lg h-48 overflow-auto font-mono text-sm">
          {terminalLines.map((line, index) => (
            <div
              key={index}
              className={index === 0 || line.startsWith('$') ? 'text-green-400' : 'text-gray-300'}
              data-testid={`terminal-line-${index}`}
            >
              {line}
            </div>
          ))}
          <div className="text-green-400 mt-2">
            $ <span className={showCursor ? 'opacity-100' : 'opacity-0'}>_</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
