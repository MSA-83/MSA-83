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
  const onMessageRef = useRef(onMessage)
  const onErrorRef = useRef(onError)
  const onOpenRef = useRef(onOpen)
  const onCloseRef = useRef(onClose)

  useEffect(() => {
    onMessageRef.current = onMessage
    onErrorRef.current = onError
    onOpenRef.current = onOpen
    onCloseRef.current = onClose
  }, [onMessage, onError, onOpen, onClose])

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const fullUrl = url.startsWith('ws') ? url : `${protocol}//${window.location.host}${url.startsWith('/') ? '' : '/'}${url}`

    const ws = new WebSocket(fullUrl)

    ws.onopen = () => {
      setIsConnected(true)
      reconnectAttempts.current = 0
      onOpenRef.current?.()
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setLastMessage(data)
        onMessageRef.current?.(data)
      } catch {
        setLastMessage({ raw: event.data })
        onMessageRef.current?.({ raw: event.data })
      }
    }

    ws.onerror = (error) => {
      onErrorRef.current?.(error)
    }

    ws.onclose = () => {
      setIsConnected(false)
      onCloseRef.current?.()

      if (autoReconnect && reconnectAttempts.current < maxReconnectAttempts) {
        reconnectTimeout.current = setTimeout(() => {
          reconnectAttempts.current++
          connect()
        }, reconnectInterval)
      }
    }

    wsRef.current = ws
  }, [url, autoReconnect, reconnectInterval, maxReconnectAttempts])

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

interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
}

export function useChatWebSocket(conversationId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isThinking, setIsThinking] = useState(false)
  const [currentResponse, setCurrentResponse] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [latency, setLatency] = useState<number | null>(null)

  const wsUrl = `/api/chat/ws/${conversationId}`

  const { isConnected, sendMessage } = useWebSocket(wsUrl, {
    autoReconnect: true,
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
    onMessage: (data) => {
      switch (data.type) {
        case 'connected':
          setError(null)
          break

        case 'pong':
          break

        case 'typing_indicator':
          setIsThinking(data.status === 'thinking')
          break

        case 'typing_ack':
          break

        case 'message':
          setIsThinking(false)
          const msg: ChatMessage = {
            id: `msg-${Date.now()}`,
            role: data.role || 'assistant',
            content: data.content,
            timestamp: new Date().toISOString(),
          }
          setMessages(prev => [...prev, msg])
          setCurrentResponse('')
          break

        case 'stream_chunk':
          setCurrentResponse(prev => prev + data.content)
          break

        case 'stream_done':
          setIsThinking(false)
          if (currentResponse) {
            setMessages(prev => [...prev, {
              id: `msg-${Date.now()}`,
              role: 'assistant',
              content: currentResponse,
              timestamp: new Date().toISOString(),
            }])
          }
          setCurrentResponse('')
          break

        case 'error':
          setIsThinking(false)
          setError(data.message || 'An error occurred')
          setMessages(prev => [...prev, {
            id: `msg-${Date.now()}`,
            role: 'system',
            content: `Error: ${data.message}`,
            timestamp: new Date().toISOString(),
          }])
          break
      }
    },
    onOpen: () => {
      setError(null)
      const start = Date.now()
      sendMessage({ type: 'ping' })
      const end = Date.now()
      setLatency(end - start)
    },
  })

  const sendChatMessage = useCallback((content: string) => {
    if (!content.trim()) return
    setError(null)

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setCurrentResponse('')
    setIsThinking(true)

    sendMessage({
      type: 'message',
      content,
      model: 'llama3',
      temperature: 0.7,
    })
  }, [sendMessage])

  const clearMessages = useCallback(() => {
    setMessages([])
    setCurrentResponse('')
    setError(null)
  }, [])

  return {
    messages,
    currentResponse,
    isThinking,
    isConnected,
    error,
    latency,
    sendMessage: sendChatMessage,
    clearMessages,
  }
}
