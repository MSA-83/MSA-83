import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { chatService } from '../services/api'

interface ModelInfo {
  name: string
  provider: string
  context_window: number
  max_output_tokens: number
  supports_streaming: boolean
  is_free: boolean
  description: string
  available: boolean
}

export default function ChatPage() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Array<{ role: string; content: string; model?: string }>>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [useRag, setUseRag] = useState(true)
  const [selectedModel, setSelectedModel] = useState('')
  const [showModelPicker, setShowModelPicker] = useState(false)

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => fetch('/api/health').then(r => r.json()),
  })

  const { data: modelsData } = useQuery({
    queryKey: ['models'],
    queryFn: () => fetch('/api/chat/models').then(r => r.json()),
    refetchOnWindowFocus: false,
  })

  const availableModels: ModelInfo[] = (modelsData?.models || []).filter((m: ModelInfo) => m.available)

  const currentModel = selectedModel || modelsData?.default || 'llama3'
  const currentModelInfo = (modelsData?.models || []).find((m: ModelInfo) => m.name === currentModel)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isStreaming) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsStreaming(true)

    let assistantContent = ''
    setMessages(prev => [...prev, { role: 'assistant', content: '', model: currentModel }])

    try {
      await chatService.streamMessage(
        {
          message: input,
          use_rag: useRag,
          model: currentModel || undefined,
        },
        (chunk) => {
          assistantContent += chunk
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = { role: 'assistant', content: assistantContent, model: currentModel }
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

  const providerColors: Record<string, string> = {
    ollama: 'bg-blue-500/20 text-blue-400',
    groq: 'bg-green-500/20 text-green-400',
    openai: 'bg-purple-500/20 text-purple-400',
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-titanium-100">Chat</h2>
          <p className="text-titanium-400 mt-1">
            {health?.status === 'healthy' ? 'AI is ready' : 'Connecting...'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <button
              onClick={() => setShowModelPicker(!showModelPicker)}
              className="flex items-center gap-2 px-3 py-1.5 bg-titanium-800 border border-titanium-700 rounded-lg text-sm text-titanium-300 hover:border-titanium-600 transition-colors"
            >
              <span className={`px-1.5 py-0.5 rounded text-xs ${providerColors[currentModelInfo?.provider || ''] || 'bg-titanium-700 text-titanium-400'}`}>
                {currentModelInfo?.provider || 'local'}
              </span>
              <span className="max-w-32 truncate">{currentModel}</span>
              <svg className="w-4 h-4 text-titanium-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {showModelPicker && (
              <div className="absolute right-0 top-full mt-2 w-80 bg-titanium-900 border border-titanium-700 rounded-lg shadow-xl z-50 max-h-80 overflow-y-auto">
                <div className="p-3 border-b border-titanium-800">
                  <p className="text-xs text-titanium-500 font-medium">Select Model</p>
                </div>
                <div className="p-2">
                  {availableModels.length === 0 && (
                    <p className="p-3 text-sm text-titanium-500 text-center">No models available</p>
                  )}
                  {availableModels.map((model) => (
                    <button
                      key={model.name}
                      onClick={() => {
                        setSelectedModel(model.name)
                        setShowModelPicker(false)
                      }}
                      className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors ${
                        model.name === currentModel
                          ? 'bg-accent-500/10 border border-accent-500/20'
                          : 'hover:bg-titanium-800'
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className={`px-1.5 py-0.5 rounded text-xs ${providerColors[model.provider] || 'bg-titanium-700 text-titanium-400'}`}>
                            {model.provider}
                          </span>
                          <span className="text-sm text-titanium-200 truncate">{model.name}</span>
                          {!model.is_free && (
                            <span className="text-xs text-yellow-500">paid</span>
                          )}
                        </div>
                        <p className="text-xs text-titanium-500 mt-1 truncate">{model.description}</p>
                      </div>
                      {model.name === currentModel && (
                        <svg className="w-4 h-4 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
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
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-titanium-300">
                {msg.role === 'user' ? 'You' : 'Titanium'}
              </span>
              {msg.model && (
                <span className={`text-xs px-1.5 py-0.5 rounded ${providerColors[(modelsData?.models || []).find((m: ModelInfo) => m.name === msg.model)?.provider || ''] || 'bg-titanium-700 text-titanium-400'}`}>
                  {msg.model}
                </span>
              )}
            </div>
            <div className="text-titanium-100 whitespace-pre-wrap">{msg.content}</div>
          </div>
        ))}

        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-titanium-500">
            <div className="text-center">
              <div className="text-4xl mb-4">💬</div>
              <p>Send a message to start chatting</p>
              <div className="flex items-center justify-center gap-4 mt-4 text-sm">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={useRag}
                    onChange={(e) => setUseRag(e.target.checked)}
                    className="rounded bg-titanium-700 border-titanium-600"
                  />
                  Use RAG memory
                </label>
                {currentModelInfo && (
                  <span className="text-xs text-titanium-600">
                    {currentModelInfo.context_window.toLocaleString()} context · {currentModelInfo.provider}
                  </span>
                )}
              </div>
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
