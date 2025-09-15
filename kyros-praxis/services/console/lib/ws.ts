import { useState, useEffect, useRef } from "react";

// Type for message
interface Message {
  type: string;
  payload: any;
  timestamp: number;
}

// Type for WebSocket status
interface WebSocketStatus {
  connected: boolean;
  connecting: boolean;
  error: string | null;
}

export const useWebSocket = (url: string = "ws://localhost:8000/ws", token?: string) => {
  const [status, setStatus] = useState<WebSocketStatus>({
    connected: false,
    connecting: false,
    error: null,
  });
  const [messages, setMessages] = useState<Message[]>([]);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Build URL with token as query parameter for authentication
    const wsUrl = token ? `${url}?token=${token}` : url;
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    setStatus((prev) => ({ ...prev, connecting: true }));

    socket.onopen = () => {
      setStatus({ connected: true, connecting: false, error: null });
    };

    socket.onmessage = (event) => {
      try {
        const message: Message = JSON.parse(event.data);
        setMessages((prev) => [...prev, { ...message, timestamp: Date.now() }]);
      } catch (error) {
        console.error("Failed to parse message:", error);
      }
    };

    socket.onclose = () => {
      setStatus({ connected: false, connecting: false, error: null });
    };

    socket.onerror = (event) => {
      console.error("WebSocket error:", event);
      setStatus({ connected: false, connecting: false, error: "WebSocket connection failed" });
    };

    return () => {
      socket.close();
    };
  }, [url, token]);

  const sendMessage = (message: Omit<Message, "timestamp">) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      const fullMessage: Message = { ...message, timestamp: Date.now() };
      socketRef.current.send(JSON.stringify(fullMessage));
    }
  };

  return {
    status,
    messages,
    sendMessage,
  };
};
