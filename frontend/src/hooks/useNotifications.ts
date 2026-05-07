import { useState, useCallback } from 'react'

export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: string
  read: boolean
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: `notif-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      timestamp: new Date().toISOString(),
      read: false,
    }

    setNotifications(prev => [newNotification, ...prev].slice(0, 50))
    setUnreadCount(prev => prev + 1)
  }, [])

  const markAsRead = useCallback((id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    )
    setUnreadCount(prev => Math.max(0, prev - 1))
  }, [])

  const markAllAsRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
    setUnreadCount(0)
  }, [])

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }, [])

  const clearAll = useCallback(() => {
    setNotifications([])
    setUnreadCount(0)
  }, [])

  const info = useCallback((title: string, message: string) => {
    addNotification({ type: 'info', title, message })
  }, [addNotification])

  const success = useCallback((title: string, message: string) => {
    addNotification({ type: 'success', title, message })
  }, [addNotification])

  const warning = useCallback((title: string, message: string) => {
    addNotification({ type: 'warning', title, message })
  }, [addNotification])

  const error = useCallback((title: string, message: string) => {
    addNotification({ type: 'error', title, message })
  }, [addNotification])

  return {
    notifications,
    unreadCount,
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAll,
    info,
    success,
    warning,
    error,
  }
}
