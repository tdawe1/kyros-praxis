'use client'

import { useEffect, useRef, useState } from 'react'
import { useSession } from 'next-auth/react'

interface WebSocketMessage {
  type: string
  payload: any
}

export function useWebSocket(url: string) {
  const { data: session, status } = useSession()
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (status !== 'authenticated' || !session?.accessToken) {
      setIsConnected(false)
      return
    }

    const token = session.accessToken
    const ws = new WebSocket(url, [token]) // Use token as subprotocol

    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
    }

    ws.onclose = () => {
      setIsConnected(false)
      // Attempt reconnect after delay
      reconnectTimeoutRef.current = setTimeout(() => {
        if (status === 'authenticated' && session?.accessToken) {
          // Recreate connection
        }
      }, 3000)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsConnected(false)
    }

    ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data)
      // Handle message, e.g., dispatch to state or callback
      console.log('Received WS message:', message)
    }

    return () => {
      ws.close()
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [status, session?.accessToken, url])

  const sendMessage = (message: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }

  return { isConnected, sendMessage }
}