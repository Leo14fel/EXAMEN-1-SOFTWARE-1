import { authenticatedFetch } from '../../services/api'

export interface SessionEvent {
  id: string
  sequence: number
  kind: 'message' | 'activity' | 'aiRequest' | 'aiResult'
  actorId: string
  actorName: string
  createdAt: string
  text?: string
  action?: string
  projectRevision?: number
  elementId?: string | null
  requestId?: string
  baseRevision?: number
  status?: 'proposed' | 'clarify' | 'unsupported' | 'failed' | 'stale'
  canApply?: false
  code?: string
}
export interface SessionPage {
  projectId: string
  events: SessionEvent[]
  participants: { userId: string; name: string; joinedAt: string }[]
  cursor: number
  version: number
  hasEarlier: boolean
  hasMore: boolean
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await authenticatedFetch(path, init)
  if (!response.ok) throw new Error(`No se pudo guardar o consultar la sesión (${response.status}).`)
  return response.json() as Promise<T>
}
export function sendSessionMessage(projectId: string, id: string, text: string): Promise<SessionEvent> {
  return request(`/projects/${projectId}/session/messages`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id, text }),
  })
}
export function getEarlierSession(projectId: string, before: number): Promise<SessionPage> {
  return request(`/projects/${projectId}/session?before=${before}`)
}

const activityLabels: Record<string, string> = {
  addElement: 'agregó un elemento', updateElement: 'editó un elemento', removeElement: 'eliminó un elemento',
  setNodeLayout: 'movió una clase', removeNodeLayout: 'quitó una posición', undo: 'deshizo una operación', redo: 'rehizo una operación',
}
export function sessionActivityLabel(event: SessionEvent): string {
  return activityLabels[event.action ?? ''] ?? 'actualizó el diagrama'
}
