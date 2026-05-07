import { createContext, useContext, ReactNode } from 'react'
import { useNotifications, Notification } from '../hooks/useNotifications'

interface NotificationsContextValue {
  notifications: Notification[]
  unreadCount: number
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  removeNotification: (id: string) => void
  clearAll: () => void
  info: (title: string, message: string) => void
  success: (title: string, message: string) => void
  warning: (title: string, message: string) => void
  error: (title: string, message: string) => void
}

const NotificationsContext = createContext<NotificationsContextValue | null>(null)

export function NotificationsProvider({ children }: { children: ReactNode }) {
  const notifications = useNotifications()

  return (
    <NotificationsContext.Provider value={notifications}>
      {children}
    </NotificationsContext.Provider>
  )
}

export function useNotificationsContext() {
  const context = useContext(NotificationsContext)
  if (!context) {
    throw new Error('useNotificationsContext must be used within NotificationsProvider')
  }
  return context
}
