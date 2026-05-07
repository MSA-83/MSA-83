import { useState, useEffect, useRef } from 'react'
import { useChatWebSocket } from '../hooks/useWebSocket'

function generateConversationId() {
  return `conv-${Math.random().toString(36).substring(2, 10)}`
}

export default function ChatWebSocketPage() {
  const [input, setInput] = useState('')
  const [conversationId] = useState(generateConversationId())
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const {
    messages,
    currentResponse,
    isThinking,
    isConnected,
    error,
    latency,
    sendMessage,
    clearMessages,
  } = useChatWebSocket(conversationId)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, currentResponse])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !isConnected) return
    sendMessage(input)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-titanium-100">Live Chat</h2>
          <p className="text-titanium-400 mt-1">WebSocket real-time streaming</p>
        </div>
        <div className="flex items-center gap-4">
          {latency !== null && (
            <span className="text-xs text-titanium-500">{latency}ms</span>
          )}
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} ${isConnected ? '' : 'animate-pulse'}`} />
            <span className="text-sm text-titanium-400">{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
          <button
            onClick={clearMessages}
            className="text-xs text-titanium-500 hover:text-titanium-300 transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-3 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-red-400">
          {error}
        </div>
      )}

      <div className="flex-1 overflow-y-auto mb-4 space-y-4 pr-2">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`p-4 rounded-lg transition-all ${
              msg.role === 'user'
                ? 'bg-accent-500/10 border border-accent-500/20 ml-12'
                : msg.role === 'system'
                  ? 'bg-red-500/10 border border-red-500/20'
                  : 'bg-titanium-800 border border-titanium-700 mr-12'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-titanium-300 capitalize">
                {msg.role === 'user' ? 'You' : msg.role === 'system' ? 'System' : 'Titanium'}
              </span>
              <span className="text-xs text-titanium-600">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <div className="text-titanium-100 whitespace-pre-wrap">{msg.content}</div>
          </div>
        ))}

        {currentResponse && (
          <div className="p-4 rounded-lg bg-titanium-800 border border-titanium-700 mr-12">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-titanium-300">Titanium</span>
              <span className="text-xs text-titanium-600">Streaming...</span>
            </div>
            <div className="text-titanium-100 whitespace-pre-wrap">
              {currentResponse}
              <span className="inline-block w-2 h-4 bg-accent-400 ml-1 animate-pulse" />
            </div>
          </div>
        )}

        {isThinking && !currentResponse && (
          <div className="p-4 rounded-lg bg-titanium-800 border border-titanium-700 mr-12">
            <div className="flex items-center gap-2 text-titanium-400">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-titanium-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-titanium-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-titanium-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-sm">Thinking...</span>
            </div>
          </div>
        )}

        {messages.length === 0 && !currentResponse && !isThinking && (
          <div className="flex items-center justify-center h-full text-titanium-500">
            <div className="text-center">
              <div className="text-4xl mb-4">⚡</div>
              <p>Real-time WebSocket chat</p>
              <p className="text-sm mt-1">Messages stream token by token</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          className="input-primary flex-1 resize-none h-12 py-2"
          disabled={!isConnected || isThinking}
          rows={1}
        />
        <button
          type="submit"
          className="btn-primary disabled:opacity-50"
          disabled={!isConnected || !input.trim() || isThinking}
        >
          {isThinking ? '...' : 'Send'}
        </button>
      </form>
    </div>
  )
}
