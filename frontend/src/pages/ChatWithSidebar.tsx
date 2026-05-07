import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { ConversationSidebar } from '../components/Chat/ConversationSidebar'
import { chatService } from '../services/api'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
}

interface Conversation {
  id: string
  title: string
  message_count: number
  updated_at: string
}

export default function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>()
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(conversationId || null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [currentResponse, setCurrentResponse] = useState('')
  const [useRag, setUseRag] = useState(true)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    fetchConversations()
  }, [])

  useEffect(() => {
    if (activeConversationId) {
      fetchMessages(activeConversationId)
    } else {
      setMessages([])
    }
  }, [activeConversationId])

  const fetchConversations = async () => {
    try {
      const response = await fetch('/api/conversations/')
      if (response.ok) {
        setConversations(await response.json())
      }
    } catch {
      console.error('Failed to fetch conversations')
    }
  }

  const fetchMessages = async (convId: string) => {
    setIsLoading(true)
    try {
      const response = await fetch(`/api/conversations/${convId}/messages`)
      if (response.ok) {
        setMessages(await response.json())
      }
    } catch {
      console.error('Failed to fetch messages')
    } finally {
      setIsLoading(false)
    }
  }

  const createNewConversation = async () => {
    try {
      const response = await fetch('/api/conversations/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      if (response.ok) {
        const conv = await response.json()
        setActiveConversationId(conv.id)
        setMessages([])
        await fetchConversations()
      }
    } catch {
      console.error('Failed to create conversation')
    }
  }

  const deleteConversation = async (convId: string) => {
    try {
      const response = await fetch(`/api/conversations/${convId}`, { method: 'DELETE' })
      if (response.ok) {
        if (activeConversationId === convId) {
          setActiveConversationId(null)
          setMessages([])
        }
        await fetchConversations()
      }
    } catch {
      console.error('Failed to delete conversation')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isStreaming) return

    const userMessage = input.trim()
    setInput('')
    setIsStreaming(true)
    setCurrentResponse('')

    let convId = activeConversationId

    if (!convId) {
      try {
        const response = await fetch('/api/conversations/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: userMessage.slice(0, 50) }),
        })
        if (response.ok) {
          const conv = await response.json()
          convId = conv.id
          setActiveConversationId(convId)
          await fetchConversations()
        }
      } catch {
        console.error('Failed to create conversation')
        setIsStreaming(false)
        return
      }
    }

    if (!convId) {
      setIsStreaming(false)
      return
    }

    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])

    try {
      await fetch(`/api/conversations/${convId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: 'user', content: userMessage }),
      })

      let assistantContent = ''

      await chatService.streamMessage(
        { message: userMessage, conversation_id: convId, use_rag: useRag },
        (chunk) => {
          assistantContent += chunk
          setCurrentResponse(assistantContent)
        },
      )

      const assistantMsg: Message = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: assistantContent,
        created_at: new Date().toISOString(),
      }
      setMessages(prev => [...prev, assistantMsg])
      setCurrentResponse('')

      await fetch(`/api/conversations/${convId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: 'assistant', content: assistantContent }),
      })

      await fetchConversations()
    } catch (error) {
      console.error('Chat error:', error)
      setCurrentResponse('Error: Failed to get response')
    } finally {
      setIsStreaming(false)
    }
  }

  const messagesEndRef = useCallback((node: HTMLDivElement | null) => {
    if (node) node.scrollIntoView({ behavior: 'smooth' })
  }, [])

  return (
    <div className="flex h-[calc(100vh-3rem)]">
      <ConversationSidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onCreateNew={createNewConversation}
        onSelect={setActiveConversationId}
        onDelete={deleteConversation}
      />

      <div className="flex-1 flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b border-titanium-800">
          <h2 className="text-sm font-medium text-titanium-300">
            {activeConversationId
              ? conversations.find(c => c.id === activeConversationId)?.title || 'Chat'
              : 'New Chat'}
          </h2>
          <label className="flex items-center gap-2 text-xs text-titanium-500">
            <input
              type="checkbox"
              checked={useRag}
              onChange={(e) => setUseRag(e.target.checked)}
              className="rounded bg-titanium-700 border-titanium-600"
            />
            RAG
          </label>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-full text-titanium-500">
              Loading...
            </div>
          ) : messages.length === 0 && !currentResponse ? (
            <div className="flex items-center justify-center h-full text-titanium-500">
              <div className="text-center">
                <div className="text-4xl mb-4">💬</div>
                <p>Start a new conversation</p>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`p-4 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-accent-500/10 border border-accent-500/20 ml-12'
                      : msg.role === 'system'
                      ? 'bg-red-500/10 border border-red-500/20'
                      : 'bg-titanium-800 border border-titanium-700 mr-12'
                  }`}
                >
                  <div className="text-sm font-medium text-titanium-300 mb-2 capitalize">
                    {msg.role === 'user' ? 'You' : 'Titanium'}
                  </div>
                  <div className="text-titanium-100 whitespace-pre-wrap">{msg.content}</div>
                </div>
              ))}

              {currentResponse && (
                <div className="p-4 rounded-lg bg-titanium-800 border border-titanium-700 mr-12">
                  <div className="text-sm font-medium text-titanium-300 mb-2">Titanium</div>
                  <div className="text-titanium-100 whitespace-pre-wrap">
                    {currentResponse}
                    <span className="inline-block w-2 h-4 bg-accent-400 ml-1 animate-pulse" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        <form onSubmit={handleSubmit} className="p-4 border-t border-titanium-800 flex gap-3">
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
            {isStreaming ? '...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  )
}
