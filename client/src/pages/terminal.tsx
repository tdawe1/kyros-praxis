import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useState, useEffect, useRef } from "react";

export default function Terminal() {
  const [isConnected, setIsConnected] = useState(false);
  const [output, setOutput] = useState<string[]>([
    "Kyros Terminal - Ready to connect",
    "Use the 'Connect' button to start a terminal session",
  ]);
  const [input, setInput] = useState("");
  const [ws, setWs] = useState<WebSocket | null>(null);
  const terminalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [output]);

  const connect = () => {
    try {
      // In a real implementation, this would connect to the terminal daemon
      // For now, we'll simulate a connection
      setIsConnected(true);
      setOutput(prev => [
        ...prev,
        "",
        "$ Connected to Kyros Terminal Daemon",
        "$ ws://localhost:8787/term",
        "$ Type 'help' for available commands",
        "$ ",
      ]);
    } catch (error) {
      setOutput(prev => [
        ...prev,
        "",
        "Error: Failed to connect to terminal daemon",
        "Make sure the daemon is running on port 8787",
      ]);
    }
  };

  const disconnect = () => {
    if (ws) {
      ws.close();
      setWs(null);
    }
    setIsConnected(false);
    setOutput(prev => [
      ...prev,
      "",
      "$ Connection closed",
    ]);
  };

  const handleInputSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const command = input.trim();
    setOutput(prev => [...prev, `$ ${command}`]);

    // Simulate some basic command responses
    switch (command.toLowerCase()) {
      case 'help':
        setOutput(prev => [
          ...prev,
          "Available commands:",
          "  help     - Show this help message",
          "  clear    - Clear the terminal",
          "  status   - Show system status",
          "  exit     - Disconnect from terminal",
        ]);
        break;
      case 'clear':
        setOutput(["$ Connected to Kyros Terminal Daemon"]);
        break;
      case 'status':
        setOutput(prev => [
          ...prev,
          "System Status:",
          "  Console:      Running on port 3001",
          "  Orchestrator: Running on port 8080",
          "  Terminal:     Connected",
        ]);
        break;
      case 'exit':
        disconnect();
        return;
      default:
        setOutput(prev => [
          ...prev,
          `Command not found: ${command}`,
          "Type 'help' for available commands",
        ]);
    }

    setOutput(prev => [...prev, "$ "]);
    setInput("");
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <Header
        title="Terminal"
        description="Interactive terminal session with the Kyros daemon"
      />
      
      <div className="flex-1 overflow-auto p-6">
        <Card className="h-full" data-testid="card-terminal">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Terminal Session</CardTitle>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`} />
                <span className="text-sm text-muted-foreground">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
                {!isConnected ? (
                  <Button
                    size="sm"
                    onClick={connect}
                    data-testid="button-connect-terminal"
                  >
                    Connect
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={disconnect}
                    data-testid="button-disconnect-terminal"
                  >
                    Disconnect
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col h-0">
            <div
              ref={terminalRef}
              className="flex-1 bg-slate-800 text-green-400 p-4 rounded-lg font-mono text-sm overflow-auto"
              data-testid="terminal-output"
            >
              {output.map((line, index) => (
                <div key={index} className={line.startsWith('$') ? 'text-green-400' : 'text-gray-300'}>
                  {line}
                </div>
              ))}
              {isConnected && (
                <form onSubmit={handleInputSubmit} className="flex items-center">
                  <span className="text-green-400 mr-1">$</span>
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    className="flex-1 bg-transparent text-green-400 outline-none"
                    placeholder="Type a command..."
                    autoComplete="off"
                    data-testid="input-terminal-command"
                  />
                </form>
              )}
            </div>
            {!isConnected && (
              <div className="mt-4 p-4 bg-muted/30 rounded-lg">
                <p className="text-sm text-muted-foreground">
                  The terminal is currently disconnected. Click "Connect" to start a new session with the Kyros terminal daemon.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
