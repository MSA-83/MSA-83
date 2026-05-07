import { useEffect } from 'react'

interface ShortcutHandler {
  key: string
  ctrlKey?: boolean
  metaKey?: boolean
  shiftKey?: boolean
  altKey?: boolean
  action: () => void
  preventDefault?: boolean
}

const shortcuts: ShortcutHandler[] = [
  {
    key: 'k',
    metaKey: true,
    action: () => {
      const input = document.querySelector('input[type="text"]') as HTMLInputElement
      if (input) input.focus()
    },
    preventDefault: true,
  },
  {
    key: 'n',
    metaKey: true,
    shiftKey: true,
    action: () => {
      window.location.href = '/chat'
    },
    preventDefault: true,
  },
  {
    key: 'Escape',
    action: () => {
      const active = document.activeElement as HTMLElement
      if (active) active.blur()
    },
  },
  {
    key: '/',
    action: () => {
      const input = document.querySelector('input[type="text"]') as HTMLInputElement
      if (input && document.activeElement !== input) {
        input.focus()
      }
    },
    preventDefault: true,
  },
  {
    key: 'Enter',
    ctrlKey: true,
    action: () => {
      const form = document.querySelector('form')
      if (form) form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }))
    },
  },
]

export function useKeyboardShortcuts(customShortcuts: ShortcutHandler[] = []) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const allShortcuts = [...customShortcuts, ...shortcuts]

      for (const shortcut of allShortcuts) {
        if (
          e.key.toLowerCase() === shortcut.key.toLowerCase() &&
          (shortcut.ctrlKey === undefined || e.ctrlKey === shortcut.ctrlKey) &&
          (shortcut.metaKey === undefined || e.metaKey === shortcut.metaKey) &&
          (shortcut.shiftKey === undefined || e.shiftKey === shortcut.shiftKey) &&
          (shortcut.altKey === undefined || e.altKey === shortcut.altKey)
        ) {
          if (shortcut.preventDefault) {
            e.preventDefault()
          }
          shortcut.action()
          break
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [customShortcuts])
}
