import { authenticatedFetch } from '../../services/api'
import type { SessionEvent } from './group-session-api'

export interface AiStatus { configured: boolean; modelCandidate: string; mode: 'proposalOnly' }
export interface AiRequest { id: string; baseRevision: number; text: string }
export interface AiResult { request: SessionEvent; result: SessionEvent | null; pending: boolean }

export class AiApiError extends Error {
  constructor(public status: number, public code: string) {
    super(code === 'AI_NOT_CONFIGURED' ? 'Falta configurar la clave de IA.'
      : code === 'PROJECT_REVISION_CONFLICT' ? 'El diagrama cambió. Espera a que se sincronice.'
      : code === 'AI_BUSY_OR_PROJECT_CHANGED' ? 'Hay otra solicitud pendiente o el diagrama cambió.'
      : 'No se pudo confirmar la solicitud. Consulta el resultado antes de volver a enviarla.')
  }
}
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await authenticatedFetch(path, init)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new AiApiError(response.status, body?.detail?.code ?? 'AI_REQUEST_ERROR')
  }
  return response.json() as Promise<T>
}
export function getAiStatus(projectId: string): Promise<AiStatus> {
  return request(`/projects/${projectId}/ai/status`)
}
export function evaluateAi(projectId: string, body: AiRequest): Promise<AiResult> {
  return request(`/projects/${projectId}/ai/requests`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  })
}
export function getAiResult(projectId: string, id: string): Promise<AiResult> {
  return request(`/projects/${projectId}/ai/requests/${id}`)
}
