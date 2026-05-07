import { useState } from 'react'
import { useNotificationsContext } from '../contexts/NotificationsContext'

interface NotificationsPanelProps {
  isOpen: boolean
  onClose: () => void
}

export default function NotificationsPanel({ isOpen }: NotificationsPanelProps) {
  const { notifications, unreadCount, markAsRead, markAllAsRead, removeNotification, clearAll } = useNotificationsContext()
  const [filter, setFilter] = useState<'all' | 'unread'>('all')

  const filteredNotifications = filter === 'unread'
    ? notifications.filter(n => !n.read)
    : notifications

  if (!isOpen) return null

  const typeColors = {
    info: 'text-blue-400 border-blue-500/20 bg-blue-500/5',
    success: 'text-green-400 border-green-500/20 bg-green-500/5',
    warning: 'text-yellow-400 border-yellow-500/20 bg-yellow-500/5',
    error: 'text-red-400 border-red-500/20 bg-red-500/5',
  }

  const typeIcons = {
    info: 'ℹ',
    success: '✓',
    warning: '⚠',
    error: '✕',
  }

  return (
    <div className="absolute right-0 top-full mt-2 w-96 bg-titanium-900 border border-titanium-700 rounded-lg shadow-xl z-50 max-h-[32rem] flex flex-col">
      <div className="p-4 border-b border-titanium-700">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-titanium-100">
            Notifications
            {unreadCount > 0 && (
              <span className="ml-2 px-2 py-0.5 text-xs bg-accent-500 text-white rounded-full">
                {unreadCount}
              </span>
            )}
          </h3>
          <div className="flex gap-2">
            <button
              onClick={() => setFilter(filter === 'all' ? 'unread' : 'all')}
              className="text-xs text-titanium-400 hover:text-titanium-200 transition-colors"
            >
              {filter === 'all' ? 'Show unread' : 'Show all'}
            </button>
            <button
              onClick={markAllAsRead}
              className="text-xs text-titanium-400 hover:text-titanium-200 transition-colors"
            >
              Mark all read
            </button>
            <button
              onClick={clearAll}
              className="text-xs text-red-400 hover:text-red-300 transition-colors"
            >
              Clear all
            </button>
          </div>
        </div>
      </div>

      <div className="overflow-y-auto flex-1">
        {filteredNotifications.length === 0 ? (
          <div className="p-8 text-center text-titanium-500">
            <p className="text-2xl mb-2">🔔</p>
            <p>No notifications</p>
          </div>
        ) : (
          <div className="divide-y divide-titanium-800">
            {filteredNotifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-4 border-l-2 ${typeColors[notification.type]} ${
                  !notification.read ? 'bg-titanium-800/50' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  <span className="text-lg">{typeIcons[notification.type]}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-titanium-200 truncate">
                        {notification.title}
                      </p>
                      <button
                        onClick={() => removeNotification(notification.id)}
                        className="text-titanium-500 hover:text-titanium-300 ml-2 flex-shrink-0"
                      >
                        ×
                      </button>
                    </div>
                    <p className="text-xs text-titanium-400 mt-1 line-clamp-2">
                      {notification.message}
                    </p>
                    <p className="text-xs text-titanium-600 mt-1">
                      {new Date(notification.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
                {!notification.read && (
                  <button
                    onClick={() => markAsRead(notification.id)}
                    className="mt-2 text-xs text-accent-400 hover:text-accent-300 transition-colors"
                  >
                    Mark as read
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
