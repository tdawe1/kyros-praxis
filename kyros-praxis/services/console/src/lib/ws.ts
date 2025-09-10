import { useCallback, useEffect, useRef, useState } from 'react'

export function useWebSocket(url: string) {
  const ws = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const reconnectDelay = useRef(1000)  // Start with 1s, double on failure

  const connect = useCallback(() => {
    ws.current = new WebSocket(url)

    ws.current.onopen = () => {
      setIsConnected(true)
      reconnectDelay.current = 1000  // Reset on success
    }

    ws.current.onclose = () => {
      setIsConnected(false)
      setTimeout(() => connect(), reconnectDelay.current)
      reconnectDelay.current = Math.min(reconnectDelay.current * 2, 30000)  // Max 30s
    }

    ws.current.onerror = () => {
      setIsConnected(false)
    }

    return ws.current
  }, [url])

  useEffect(() => {
    connect()

    return () => {
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [connect])

  return { isConnected, sendMessage: (message: any) => ws.current?.send(JSON.stringify(message)) }
}