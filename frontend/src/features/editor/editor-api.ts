import { authenticatedFetch } from '../../services/api'
import type { ProjectDocument, ProjectEditorState, ProjectSummary, UmlCommand } from './types'

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

async function editorRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await authenticatedFetch(path, init)
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
  return response.json() as Promise<T>
}

export function createProject(metadata: Record<string, string>): Promise<ProjectDocument> {
  return editorRequest('/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ metadata }),
  })
}

export function listProjects(): Promise<ProjectSummary[]> {
  return editorRequest('/projects')
}

export function getProject(projectId: string): Promise<ProjectDocument> {
  return editorRequest(`/projects/${projectId}`)
}

export function executeProjectCommand(
  projectId: string,
  baseRevision: number,
  command: UmlCommand,
): Promise<ProjectEditorState> {
  return editorRequest(`/projects/${projectId}/commands`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ baseRevision, command }),
  })
}

export function undoProject(projectId: string, baseRevision: number): Promise<ProjectEditorState> {
  return editorRequest(`/projects/${projectId}/undo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ baseRevision }),
  })
}

export function redoProject(projectId: string, baseRevision: number): Promise<ProjectEditorState> {
  return editorRequest(`/projects/${projectId}/redo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ baseRevision }),
  })
}
