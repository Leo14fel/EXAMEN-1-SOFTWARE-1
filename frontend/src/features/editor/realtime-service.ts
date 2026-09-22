import { API_BASE_URL } from '../../services/api'
import type { ProjectDocument } from './types'

export type RealtimeStatus = 'disconnected' | 'connecting' | 'connected' | 'reconnecting'

interface ProjectUpdatedMessage {
  type: 'project.updated'
  document: ProjectDocument
}

export class ProjectRealtimeService {
  private socket: WebSocket | null = null
  private retryTimer: number | null = null
  private stopped = true
  private retries = 0
  private onStatus: ((status: RealtimeStatus) => void) | null = null

  connect(
    projectId: string,
    token: string,
    onStatus: (status: RealtimeStatus) => void,
    onDocument: (document: ProjectDocument) => void,
  ): void {
    this.close()
    this.onStatus = onStatus
    this.stopped = false
    const open = () => {
      if (this.stopped) return
      onStatus(this.retries === 0 ? 'connecting' : 'reconnecting')
      const url = new URL(`${API_BASE_URL}/projects/${projectId}/realtime`)
      url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
      url.searchParams.set('token', token)
      const socket = new WebSocket(url)
      this.socket = socket
      socket.onopen = () => {
        if (this.socket !== socket) return
        this.retries = 0
        onStatus('connected')
      }
      socket.onmessage = (event) => {
        if (this.socket !== socket || typeof event.data !== 'string') return
        const message = JSON.parse(event.data) as ProjectUpdatedMessage
        if (message.type === 'project.updated') onDocument(message.document)
      }
      socket.onclose = (event) => {
        if (this.socket !== socket) return
        this.socket = null
        if (this.stopped || event.code === 1008) {
          this.stopped = true
          onStatus('disconnected')
          return
        }
        this.retries += 1
        this.retryTimer = window.setTimeout(open, Math.min(1000 * this.retries, 5000))
      }
      socket.onerror = () => socket.close()
    }
    open()
  }

  close(): void {
    this.stopped = true
    if (this.retryTimer !== null) window.clearTimeout(this.retryTimer)
    this.retryTimer = null
    const socket = this.socket
    this.socket = null
    socket?.close()
    this.onStatus?.('disconnected')
    this.onStatus = null
  }
}
