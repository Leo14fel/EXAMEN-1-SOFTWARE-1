import { afterEach, describe, expect, it, vi } from 'vitest'
import { getHealth } from './api'

describe('getHealth', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('solicita el health del backend', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: 'ok', service: 'backend' }), { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(getHealth()).resolves.toEqual({ status: 'ok', service: 'backend' })
    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/health')
  })
})
