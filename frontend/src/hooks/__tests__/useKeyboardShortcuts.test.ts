import { renderHook } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { useKeyboardShortcuts } from '../useKeyboardShortcuts'

describe('useKeyboardShortcuts', () => {
  it('registers keydown event listener', () => {
    const addEventListener = vi.spyOn(window, 'addEventListener')
    const removeEventListener = vi.spyOn(window, 'removeEventListener')

    const { unmount } = renderHook(() => useKeyboardShortcuts())

    expect(addEventListener).toHaveBeenCalledWith('keydown', expect.any(Function))

    unmount()
    expect(removeEventListener).toHaveBeenCalledWith('keydown', expect.any(Function))
  })

  it('triggers action on matching key', () => {
    const action = vi.fn()
    renderHook(() =>
      useKeyboardShortcuts([
        { key: 'k', metaKey: true, action },
      ]),
    )

    const event = new KeyboardEvent('keydown', { key: 'k', metaKey: true })
    window.dispatchEvent(event)

    expect(action).toHaveBeenCalled()
  })

  it('does not trigger on non-matching key', () => {
    const action = vi.fn()
    renderHook(() =>
      useKeyboardShortcuts([
        { key: 'k', metaKey: true, action },
      ]),
    )

    const event = new KeyboardEvent('keydown', { key: 'x', metaKey: true })
    window.dispatchEvent(event)

    expect(action).not.toHaveBeenCalled()
  })

  it('does not trigger when modifier does not match', () => {
    const action = vi.fn()
    renderHook(() =>
      useKeyboardShortcuts([
        { key: 'k', metaKey: true, action },
      ]),
    )

    const event = new KeyboardEvent('keydown', { key: 'k', metaKey: false })
    window.dispatchEvent(event)

    expect(action).not.toHaveBeenCalled()
  })

  it('handles Escape key', () => {
    const action = vi.fn()
    renderHook(() =>
      useKeyboardShortcuts([
        { key: 'Escape', action },
      ]),
    )

    const event = new KeyboardEvent('keydown', { key: 'Escape' })
    window.dispatchEvent(event)

    expect(action).toHaveBeenCalled()
  })

  it('handles multiple shortcuts', () => {
    const action1 = vi.fn()
    const action2 = vi.fn()

    renderHook(() =>
      useKeyboardShortcuts([
        { key: 'a', action: action1 },
        { key: 'b', action: action2 },
      ]),
    )

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'a' }))
    expect(action1).toHaveBeenCalled()

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'b' }))
    expect(action2).toHaveBeenCalled()
  })

  it('case insensitive key matching', () => {
    const action = vi.fn()
    renderHook(() =>
      useKeyboardShortcuts([
        { key: 'K', action },
      ]),
    )

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k' }))
    expect(action).toHaveBeenCalled()
  })
})
