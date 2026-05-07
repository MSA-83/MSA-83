import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { useToast } from '../useToast'

vi.useFakeTimers()

vi.mock('../useKeyboardShortcuts', () => ({
  useKeyboardShortcuts: vi.fn(),
}))

describe('useToast', () => {
  it('starts with empty toasts', () => {
    const { result } = renderHook(() => useToast())
    expect(result.current.toasts).toEqual([])
  })

  it('adds a toast', () => {
    const { result } = renderHook(() => useToast())

    act(() => {
      result.current.addToast('Hello', 'success')
    })

    expect(result.current.toasts).toHaveLength(1)
    expect(result.current.toasts[0].message).toBe('Hello')
    expect(result.current.toasts[0].type).toBe('success')
  })

  it('removes a toast', () => {
    const { result } = renderHook(() => useToast())

    act(() => {
      result.current.addToast('Test', 'info')
    })

    const id = result.current.toasts[0].id

    act(() => {
      result.current.removeToast(id)
    })

    expect(result.current.toasts).toEqual([])
  })

  it('auto-removes toast after timeout', () => {
    const { result } = renderHook(() => useToast())

    act(() => {
      result.current.addToast('Auto remove', 'info')
    })

    expect(result.current.toasts).toHaveLength(1)

    act(() => {
      vi.advanceTimersByTime(3000)
    })

    expect(result.current.toasts).toEqual([])
  })

  it('handles multiple toasts', () => {
    const { result } = renderHook(() => useToast())

    act(() => {
      result.current.addToast('First', 'info')
      result.current.addToast('Second', 'success')
      result.current.addToast('Third', 'error')
    })

    expect(result.current.toasts).toHaveLength(3)
  })

  it('defaults to info type', () => {
    const { result } = renderHook(() => useToast())

    act(() => {
      result.current.addToast('Default type')
    })

    expect(result.current.toasts[0].type).toBe('info')
  })
})
