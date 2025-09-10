'use client'

import { useEffect, useRef, useState, useCallback } from 'react'

export interface WebSocketHookReturn {
  isConnected: boolean
  sendMessage: ((message: any) => void) | null
  lastMessage: MessageEvent | null
  connectionState: string
}

export function useWebSocket(url: string): WebSocketHookReturn {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null)
  const [connectionState, setConnectionState] = useState('CONNECTING')
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url)
      
      ws.current.onopen = () => {
        setIsConnected(true)
        setConnectionState('OPEN')
        console.log(`WebSocket connected to ${url}`)
      }

      ws.current.onclose = (event) => {
        setIsConnected(false)
        setConnectionState('CLOSED')
        console.log(`WebSocket disconnected from ${url}`, event.code, event.reason)
        
        // Auto-reconnect after 3 seconds
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current)
        }
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log(`Attempting to reconnect to ${url}`)
          connect()
        }, 3000)
      }

      ws.current.onerror = (error) => {
        console.error(`WebSocket error for ${url}:`, error)
        setConnectionState('ERROR')
      }

      ws.current.onmessage = (event) => {
        setLastMessage(event)
        console.log(`WebSocket message from ${url}:`, event.data)
      }
    } catch (error) {
      console.error(`Failed to create WebSocket connection to ${url}:`, error)
      setConnectionState('ERROR')
    }
  }, [url])

  const sendMessage = useCallback((message: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(JSON.stringify(message))
      } catch (error) {
        console.error('Failed to send WebSocket message:', error)
      }
    } else {
      console.warn('WebSocket is not connected. Cannot send message.')
    }
  }, [])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [connect])

  return {
    isConnected,
    sendMessage: isConnected ? sendMessage : null,
    lastMessage,
    connectionState
  }
}