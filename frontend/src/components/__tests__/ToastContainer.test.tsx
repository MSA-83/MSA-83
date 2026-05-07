import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ToastContainer } from '../ToastContainer'

const mockUseToast = vi.hoisted(() => vi.fn())
vi.mock('../../hooks/useToast', () => ({
  useToast: () => mockUseToast(),
}))

describe('ToastContainer', () => {
  it('renders nothing when no toasts', () => {
    mockUseToast.mockReturnValue({ toasts: [], addToast: vi.fn(), removeToast: vi.fn() })
    const { container } = render(<ToastContainer />)
    expect(container.firstChild).toBeNull()
  })

  it('renders toasts', () => {
    mockUseToast.mockReturnValue({
      toasts: [{ id: '1', message: 'Success!', type: 'success' }],
      addToast: vi.fn(),
      removeToast: vi.fn(),
    })
    render(<ToastContainer />)
    expect(screen.getByText('Success!')).toBeInTheDocument()
  })

  it('renders different toast types', () => {
    mockUseToast.mockReturnValue({
      toasts: [
        { id: '1', message: 'Info', type: 'info' },
        { id: '2', message: 'Error', type: 'error' },
        { id: '3', message: 'Success', type: 'success' },
      ],
      addToast: vi.fn(),
      removeToast: vi.fn(),
    })
    render(<ToastContainer />)
    expect(screen.getByText('Info')).toBeInTheDocument()
    expect(screen.getByText('Error')).toBeInTheDocument()
    expect(screen.getByText('Success')).toBeInTheDocument()
  })

  it('calls removeToast on dismiss', () => {
    const removeToast = vi.fn()
    mockUseToast.mockReturnValue({
      toasts: [{ id: '1', message: 'Dismiss me', type: 'info' }],
      addToast: vi.fn(),
      removeToast,
    })
    render(<ToastContainer />)
    const dismissBtn = screen.getByText('×')
    fireEvent.click(dismissBtn)
    expect(removeToast).toHaveBeenCalledWith('1')
  })
})
