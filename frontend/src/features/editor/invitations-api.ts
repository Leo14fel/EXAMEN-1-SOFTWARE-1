import { authenticatedFetch } from '../../services/api'
import type { ProjectRole } from './types'

export interface Invitation { id: string; email: string; role: ProjectRole; expiresAt: string; createdAt: string }
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await authenticatedFetch(path, init)
  if (!response.ok) {
    const messages: Record<number, string> = {
      404: 'La invitación no está disponible para esta cuenta. Revisa el código y el correo con el que ingresaste.',
      409: 'La invitación ya no está disponible o ya tienes acceso. Actualiza tus proyectos.',
      410: 'La invitación venció. Pide un código nuevo al propietario.',
      422: 'Revisa el correo, rol, duración o código de invitación.',
    }
    throw new Error(messages[response.status] ?? 'No se pudo procesar la invitación.')
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>
}
export function listInvitations(projectId: string): Promise<Invitation[]> { return request(`/projects/${projectId}/invitations`) }
export function createInvitation(projectId: string, email: string, role: ProjectRole, expiresHours: number): Promise<Invitation & { token: string }> {
  return request(`/projects/${projectId}/invitations`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, role, expiresHours }) })
}
export function cancelInvitation(projectId: string, id: string): Promise<void> { return request(`/projects/${projectId}/invitations/${id}`, { method: 'DELETE' }) }
export function acceptInvitation(token: string): Promise<{ projectId: string; effectiveRole: ProjectRole }> {
  return request('/project-invitations/accept', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token }) })
}
