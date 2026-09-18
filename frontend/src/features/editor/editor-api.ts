import { API_BASE_URL } from '../../services/api'
import type { EditorSessionState, UmlCommand } from './types'

interface ApiErrorPayload {
  detail?: {
    code?: string
    message?: string
  }
}

export class EditorApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
  ) {
    super(message)
    this.name = 'EditorApiError'
  }
}

async function editorRequest(path: string, init?: RequestInit): Promise<EditorSessionState> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)
  if (!response.ok) {
    let payload: ApiErrorPayload | null = null
    try {
      payload = (await response.json()) as ApiErrorPayload
    } catch {
      payload = null
    }
    throw new EditorApiError(
      payload?.detail?.message ?? `Backend respondió ${response.status}`,
      response.status,
      payload?.detail?.code,
    )
  }
  return response.json() as Promise<EditorSessionState>
}

export function createEditorSession(): Promise<EditorSessionState> {
  return editorRequest('/editor/sessions', { method: 'POST' })
}

export function getEditorSession(sessionId: string): Promise<EditorSessionState> {
  return editorRequest(`/editor/sessions/${sessionId}`)
}

export function executeEditorCommand(
  sessionId: string,
  command: UmlCommand,
): Promise<EditorSessionState> {
  return editorRequest(`/editor/sessions/${sessionId}/commands`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(command),
  })
}

export function undoEditorSession(sessionId: string): Promise<EditorSessionState> {
  return editorRequest(`/editor/sessions/${sessionId}/undo`, { method: 'POST' })
}

export function redoEditorSession(sessionId: string): Promise<EditorSessionState> {
  return editorRequest(`/editor/sessions/${sessionId}/redo`, { method: 'POST' })
}