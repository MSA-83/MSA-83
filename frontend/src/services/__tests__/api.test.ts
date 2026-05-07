import { describe, it, expect, vi, beforeEach } from 'vitest'
import { exportService } from '../api'

const mockFetch = vi.fn()
globalThis.fetch = mockFetch

beforeEach(() => {
  mockFetch.mockReset()
  localStorage.setItem('accessToken', 'test-token')
})

describe('exportService', () => {
  it('export conversation sends correct request', async () => {
    mockFetch.mockResolvedValue({
      blob: () => Promise.resolve(new Blob(['test'])),
    })

    await exportService.conversation('conv-1', 'md', true)

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/export/conversation',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
        }),
        body: JSON.stringify({
          conversation_id: 'conv-1',
          format: 'md',
          include_metadata: true,
        }),
      }),
    )
  })

  it('export usage sends correct request', async () => {
    mockFetch.mockResolvedValue({
      blob: () => Promise.resolve(new Blob(['test'])),
    })

    await exportService.usage('user-1', 7)

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/export/usage/user-1?days=7',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
        }),
      }),
    )
  })

  it('export memory sends correct request with query', async () => {
    mockFetch.mockResolvedValue({
      blob: () => Promise.resolve(new Blob(['test'])),
    })

    await exportService.memory('test query', 'json')

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/export/memory?query=test+query&format=json',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
        }),
      }),
    )
  })

  it('export memory sends correct request without query', async () => {
    mockFetch.mockResolvedValue({
      blob: () => Promise.resolve(new Blob(['test'])),
    })

    await exportService.memory(undefined, 'md')

    const callUrl = mockFetch.mock.calls[0][0]
    expect(callUrl).toContain('format=md')
    expect(callUrl).not.toContain('query=')
  })
})
