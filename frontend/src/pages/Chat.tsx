import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { chatService } from '../services/api'

export default function ChatPage() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [useRag, setUseRag] = useState(true)

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => fetch('/api/health').then(r => r.json()),
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isStreaming) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsStreaming(true)

    let assistantContent = ''
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    try {
      await chatService.streamMessage(
        {
          message: input,
          use_rag: useRag,
        },
        (chunk) => {
          assistantContent += chunk
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = { role: 'assistant', content: assistantContent }
            return updated
          })
        },
      )
    } catch (error) {
      assistantContent += '\n\nError: Failed to get response'
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = { role: 'assistant', content: assistantContent }
        return updated
      })
    } finally {
      setIsStreaming(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-titanium-100">Chat</h2>
        <p className="text-titanium-400 mt-1">
          {health?.status === 'healthy' ? 'AI is ready' : 'Connecting...'}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto mb-4 space-y-4 pr-2">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-4 rounded-lg ${
              msg.role === 'user'
                ? 'bg-accent-500/10 border border-accent-500/20 ml-12'
                : 'bg-titanium-800 border border-titanium-700 mr-12'
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-medium text-titanium-300">
                {msg.role === 'user' ? 'You' : 'Titanium'}
              </span>
            </div>
            <div className="text-titanium-100 whitespace-pre-wrap">{msg.content}</div>
          </div>
        ))}

        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-titanium-500">
            <div className="text-center">
              <div className="text-4xl mb-4">💬</div>
              <p>Send a message to start chatting</p>
              <label className="flex items-center justify-center gap-2 mt-4 text-sm">
                <input
                  type="checkbox"
                  checked={useRag}
                  onChange={(e) => setUseRag(e.target.checked)}
                  className="rounded bg-titanium-700 border-titanium-600"
                />
                Use RAG memory context
              </label>
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="input-primary flex-1"
          disabled={isStreaming}
        />
        <button
          type="submit"
          className="btn-primary disabled:opacity-50"
          disabled={isStreaming || !input.trim()}
        >
          {isStreaming ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  )
}
