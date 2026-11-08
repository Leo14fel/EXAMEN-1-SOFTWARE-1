import { API_BASE_URL } from '../../services/api'
import type { JsonValue, ProjectDocument, ProjectEditorState, ProjectRole } from './types'
import type { SessionPage } from './group-session-api'

export type SyncStatus = 'connecting' | 'connected' | 'reconnecting' | 'unavailable'
export interface DocumentChange {
  op: 'set' | 'remove'
  path: (string | number)[]
  value?: JsonValue
}
export interface SnapshotEvent extends ProjectEditorState {
  type: 'snapshot'
  effectiveRole: ProjectRole
}
export interface PatchEvent {
  type: 'patch'
  projectId: string
  baseRevision: number
  revision: number
  changes: DocumentChange[]
  canUndo: boolean
  canRedo: boolean
  effectiveRole: ProjectRole
}
export type SyncEvent = SnapshotEvent | PatchEvent

export interface PresenceState {
  cursor: { x: number; y: number } | null
  selectedElementId: string | null
  editingElementId: string | null
}
export interface Participant extends PresenceState {
  sessionId: string
  userId: string
  name: string
  role: ProjectRole
  lastActivity: string
}
export interface PresenceEvent {
  type: 'presence'
  projectId: string
  sessionId: string
  participants: Participant[]
}
export type PresenceConnection = (() => void) & { updatePresence: (state: PresenceState) => void }

export function applyDocumentChanges(document: ProjectDocument, changes: DocumentChange[]): ProjectDocument {
  // Build an independent projection; never partially publish an invalid delta.
  const result = JSON.parse(JSON.stringify(document)) as Record<string, unknown>
  for (const change of changes) {
    if (!change.path.length || !['set', 'remove'].includes(change.op)) throw new Error('Delta inválido')
    let parent: Record<string | number, unknown> = result
    for (const segment of change.path.slice(0, -1)) {
      if (['__proto__', 'constructor', 'prototype'].includes(String(segment)) ||
          !Object.hasOwn(parent, segment)) throw new Error('Ruta inválida')
      const child = parent[segment]
      if (child === null || typeof child !== 'object') throw new Error('Ruta inválida')
      parent = child as Record<string | number, unknown>
    }
    const key = change.path.at(-1)!
    if (['__proto__', 'constructor', 'prototype'].includes(String(key))) throw new Error('Ruta inválida')
    if (Array.isArray(parent)) {
      if (typeof key !== 'number' || !Number.isInteger(key) || key < 0 ||
          key > parent.length || (change.op === 'remove' && key === parent.length)) {
        throw new Error('Índice inválido')
      }
      if (change.op === 'remove') parent.splice(key, 1)
      else parent[key] = change.value
    } else if (change.op === 'remove') {
      if (!Object.hasOwn(parent, key)) throw new Error('Ruta inválida')
      delete parent[key]
    } else {
      parent[key] = change.value
    }
  }
  return result as unknown as ProjectDocument
}

export function connectProjectSync(options: {
  projectId: string
  token: string
  onEvent: (event: SyncEvent) => boolean
  onStatus: (status: SyncStatus) => void
  onForbidden: (code: number) => void
  onPresence?: (event: PresenceEvent) => void
  onConversation?: (page: SessionPage) => void
}): PresenceConnection {
  let stopped = false
  let socket: WebSocket | null = null
  let retry: ReturnType<typeof setTimeout> | undefined
  let timeout: ReturnType<typeof setTimeout> | undefined
  let attempts = 0
  let resyncPending = false
  let ready = false
  let latestPresence: PresenceState | null = null
  let presenceDirty = false
  let presenceTimer: ReturnType<typeof setTimeout> | undefined
  function schedulePresence() {
    if (stopped || !ready || !presenceDirty || !latestPresence || !options.onPresence || presenceTimer) return
    presenceTimer = setTimeout(() => {
      presenceTimer = undefined
      if (!stopped && ready && latestPresence) {
        socket?.send(JSON.stringify({ type: 'presence', ...latestPresence }))
        presenceDirty = false
      }
    }, 500)
  }
  const url = new URL(`${API_BASE_URL}/projects/${encodeURIComponent(options.projectId)}/sync`)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'

  function connect() {
    if (stopped) return
    options.onStatus(attempts ? 'reconnecting' : 'connecting')
    const current = new WebSocket(url)
    socket = current
    resyncPending = false
    ready = false
    presenceDirty = latestPresence !== null
    timeout = setTimeout(() => current.close(), 15000)
    current.onopen = () => {
      if (stopped || socket !== current) return
      current.send(JSON.stringify({ type: 'authenticate', token: options.token,
        ...(options.onPresence ? { presence: true } : {}),
        ...(options.onConversation ? { conversation: true } : {}) }))
      // Conversation is negotiated independently of ephemeral presence.
    }
    current.onmessage = (message) => {
      if (stopped || socket !== current) return
      try {
        const event = JSON.parse(String(message.data)) as SyncEvent | PresenceEvent | (SessionPage & { type: 'conversation' })
        if (event.type === 'conversation') {
          if (event.projectId !== options.projectId || !Array.isArray(event.events)) throw new Error('Sesión inválida')
          options.onConversation?.(event)
          return
        }
        if (event.type === 'presence') {
          if (event.projectId !== options.projectId || !Array.isArray(event.participants)) throw new Error('Presencia inválida')
          options.onPresence?.(event)
          return
        }
        if (event.type !== 'snapshot' && event.type !== 'patch') throw new Error('Evento inválido')
        if (resyncPending && event.type !== 'snapshot') return
        if (!options.onEvent(event)) {
          if (!resyncPending) {
            resyncPending = true
            current.send(JSON.stringify({ type: 'resync' }))
            clearTimeout(timeout)
            timeout = setTimeout(() => current.close(), 15000)
          }
          options.onStatus('reconnecting')
          return
        }
        resyncPending = false
        clearTimeout(timeout)
        attempts = 0
        options.onStatus('connected')
        ready = true
        schedulePresence()
      } catch {
        // Reconnect obtains a validated authoritative snapshot after malformed data.
        current.close()
      }
    }
    current.onclose = (event) => {
      if (stopped || socket !== current) return
      clearTimeout(timeout)
      ready = false
      clearTimeout(presenceTimer)
      presenceTimer = undefined
      if ([4401, 4403, 4404].includes(event.code)) {
        stopped = true
        options.onStatus('unavailable')
        options.onForbidden(event.code)
        return
      }
      options.onStatus('reconnecting')
      retry = setTimeout(connect, Math.min(1000 * 2 ** attempts++, 10000))
    }
    current.onerror = () => current.close()
  }
  connect()
  const stop = () => {
    stopped = true
    clearTimeout(retry)
    clearTimeout(timeout)
    clearTimeout(presenceTimer)
    socket?.close()
  }
  stop.updatePresence = (state: PresenceState) => {
    latestPresence = JSON.parse(JSON.stringify(state)) as PresenceState
    presenceDirty = true
    schedulePresence()
  }
  return stop
}
