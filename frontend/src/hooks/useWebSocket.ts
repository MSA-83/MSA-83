import { useState, useEffect, useRef, useCallback } from 'react'

interface UseWebSocketOptions {
  onMessage?: (data: any) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  onClose?: () => void
  autoReconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

export function useWebSocket(
  url: string,
  options: UseWebSocketOptions = {},
) {
  const {
    onMessage,
    onError,
    onOpen,
    onClose,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<any>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttempts = useRef(0)
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(url)

    ws.onopen = () => {
      setIsConnected(true)
      reconnectAttempts.current = 0
      onOpen?.()
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setLastMessage(data)
        onMessage?.(data)
      } catch {
        setLastMessage({ raw: event.data })
        onMessage?.({ raw: event.data })
      }
    }

    ws.onerror = (error) => {
      onError?.(error)
    }

    ws.onclose = () => {
      setIsConnected(false)
      onClose?.()

      if (autoReconnect && reconnectAttempts.current < maxReconnectAttempts) {
        reconnectTimeout.current = setTimeout(() => {
          reconnectAttempts.current++
          connect()
        }, reconnectInterval)
      }
    }

    wsRef.current = ws
  }, [url, autoReconnect, reconnectInterval, maxReconnectAttempts, onMessage, onError, onOpen, onClose])

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const sendMessage = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    isConnected,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
  }
}

export function useChatWebSocket(clientId: string) {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([])
  const [isThinking, setIsThinking] = useState(false)
  const [currentResponse, setCurrentResponse] = useState('')

  const wsUrl = `ws://${window.location.host}/ws/chat/${clientId}`

  const { isConnected, sendMessage } = useWebSocket(wsUrl, {
    onMessage: (data) => {
      switch (data.type) {
        case 'status':
          setIsThinking(true)
          break
        case 'chunk':
          setCurrentResponse(prev => prev + data.content)
          break
        case 'done':
          setIsThinking(false)
          setMessages(prev => [
            ...prev,
            { role: 'assistant', content: data.content },
          ])
          setCurrentResponse('')
          break
        case 'error':
          setIsThinking(false)
          setMessages(prev => [
            ...prev,
            { role: 'system', content: `Error: ${data.content}` },
          ])
          break
      }
    },
  })

  const sendChatMessage = useCallback((content: string) => {
    setMessages(prev => [...prev, { role: 'user', content }])
    setCurrentResponse('')
    sendMessage({
      message: content,
      use_rag: true,
    })
  }, [sendMessage])

  return {
    messages,
    currentResponse,
    isThinking,
    isConnected,
    sendMessage: sendChatMessage,
  }
}
