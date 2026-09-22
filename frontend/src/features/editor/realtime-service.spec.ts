import { afterEach, describe, expect, it, vi } from 'vitest'
import { ProjectRealtimeService } from './realtime-service'

class FakeWebSocket {
  static instances: FakeWebSocket[] = []
  onopen: (() => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null
  closed = false

  constructor(readonly url: URL) {
    FakeWebSocket.instances.push(this)
  }

  close() {
    this.closed = true
    this.onclose?.()
  }
}

afterEach(() => {
  vi.unstubAllGlobals()
  FakeWebSocket.instances = []
})

describe('ProjectRealtimeService', () => {
  it('uses one authenticated socket and stops retries after close', () => {
    vi.stubGlobal('WebSocket', FakeWebSocket)
    const service = new ProjectRealtimeService()
    const status = vi.fn()

    service.connect('project-id', 'jwt token', status, vi.fn())
    const socket = FakeWebSocket.instances[0]
    socket.onopen?.()
    service.close()

    expect(socket.url.protocol).toBe('ws:')
    expect(socket.url.pathname).toBe('/projects/project-id/realtime')
    expect(socket.url.searchParams.get('token')).toBe('jwt token')
    expect(status).toHaveBeenLastCalledWith('disconnected')
    expect(FakeWebSocket.instances).toHaveLength(1)
  })

  it('forwards authoritative project.updated documents only', () => {
    vi.stubGlobal('WebSocket', FakeWebSocket)
    const service = new ProjectRealtimeService()
    const onDocument = vi.fn()

    service.connect('project-id', 'token', vi.fn(), onDocument)
    FakeWebSocket.instances[0].onmessage?.({
      data: JSON.stringify({ type: 'project.updated', document: { id: 'project-id', revision: 2 } }),
    } as MessageEvent)

    expect(onDocument).toHaveBeenCalledWith({ id: 'project-id', revision: 2 })
    service.close()
  })
})
