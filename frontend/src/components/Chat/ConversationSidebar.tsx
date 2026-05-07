import { useState } from 'react'

interface Conversation {
  id: string
  title: string
  message_count: number
  updated_at: string
}

export function ConversationSidebar({
  conversations,
  activeConversationId,
  onCreateNew,
  onSelect,
  onDelete,
}: {
  conversations: Conversation[]
  activeConversationId: string | null
  onCreateNew: () => void
  onSelect: (id: string) => void
  onDelete: (id: string) => void
}) {
  const [showConfirmDelete, setShowConfirmDelete] = useState<string | null>(null)

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="w-64 bg-titanium-900 border-r border-titanium-800 flex flex-col">
      <div className="p-3 border-b border-titanium-800">
        <button
          onClick={onCreateNew}
          className="w-full btn-secondary text-sm flex items-center justify-center gap-2"
        >
          <span>+</span>
          <span>New Chat</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {conversations.length === 0 ? (
          <p className="text-sm text-titanium-600 text-center py-8">No conversations yet</p>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`group rounded-lg transition-colors ${
                conv.id === activeConversationId
                  ? 'bg-accent-500/10 border border-accent-500/20'
                  : 'hover:bg-titanium-800'
              }`}
            >
              <button
                onClick={() => onSelect(conv.id)}
                className="w-full text-left p-2.5"
              >
                <p className="text-sm text-titanium-200 truncate pr-4">
                  {conv.title}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-titanium-500">
                    {conv.message_count} msgs
                  </span>
                  <span className="text-xs text-titanium-600">
                    {formatTime(conv.updated_at)}
                  </span>
                </div>
              </button>

              {showConfirmDelete === conv.id ? (
                <div className="px-2 pb-2 flex gap-2">
                  <button
                    onClick={() => {
                      onDelete(conv.id)
                      setShowConfirmDelete(null)
                    }}
                    className="text-xs text-red-400 hover:text-red-300 px-2 py-1 rounded bg-red-500/10"
                  >
                    Confirm
                  </button>
                  <button
                    onClick={() => setShowConfirmDelete(null)}
                    className="text-xs text-titanium-400 hover:text-titanium-300 px-2 py-1 rounded bg-titanium-700"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setShowConfirmDelete(conv.id)
                  }}
                  className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 text-titanium-500 hover:text-red-400 transition-opacity p-1"
                >
                  ×
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
