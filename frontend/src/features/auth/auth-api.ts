import { API_BASE_URL, authenticatedFetch } from '../../services/api'

export interface AuthUser {
  id: string
  email: string
}

export interface AuthSession {
  accessToken: string
  tokenType: string
  user: AuthUser
}

interface ApiErrorPayload {
  detail?: { code?: string; message?: string }
}

export class AuthApiError extends Error {
  constructor(readonly status: number, readonly code?: string, message?: string) {
    super(message ?? `Backend respondió ${status}`)
    this.name = 'AuthApiError'
  }
}

async function request<T>(path: string, init?: RequestInit, authenticated = false): Promise<T> {
  const response = authenticated
    ? await authenticatedFetch(path, init)
    : await fetch(`${API_BASE_URL}${path}`, init)
  if (!response.ok) {
    let payload: ApiErrorPayload | undefined
    try {
      payload = (await response.json()) as ApiErrorPayload
    } catch {
      payload = undefined
    }
    throw new AuthApiError(response.status, payload?.detail?.code, payload?.detail?.message)
  }
  return response.json() as Promise<T>
}

function credentials(email: string, password: string): RequestInit {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  }
}

export function register(email: string, password: string): Promise<AuthSession> {
  return request('/auth/register', credentials(email, password))
}

export function login(email: string, password: string): Promise<AuthSession> {
  return request('/auth/login', credentials(email, password))
}

export function getCurrentUser(): Promise<AuthUser> {
  return request('/auth/me', undefined, true)
}
