import { useKeyboardShortcuts } from './useKeyboardShortcuts'
import { useState } from 'react'

export function useToast() {
  const [toasts, setToasts] = useState<Array<{ id: string; message: string; type: 'success' | 'error' | 'info' }>>([])

  const addToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = `toast-${Date.now()}`
    setToasts(prev => [...prev, { id, message, type }])

    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 3000)
  }

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }

  useKeyboardShortcuts([
    {
      key: 't',
      metaKey: true,
      shiftKey: true,
      action: () => {
        setToasts([])
      },
    },
  ])

  return { toasts, addToast, removeToast }
}
