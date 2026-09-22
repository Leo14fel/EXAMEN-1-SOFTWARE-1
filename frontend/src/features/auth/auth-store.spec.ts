import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { authenticatedFetch, setAccessToken, setUnauthorizedHandler } from '../../services/api'
import * as authApi from './auth-api'
import { useAuthStore } from './auth-store'

vi.mock('./auth-api', () => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
}))

const session = {
  accessToken: 'jwt-token',
  tokenType: 'bearer',
  user: { id: '11111111-1111-1111-1111-111111111111', email: 'user@example.com' },
}

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    setAccessToken(null)
    setUnauthorizedHandler(null)
    vi.clearAllMocks()
  })

  afterEach(() => vi.unstubAllGlobals())

  it('guarda la sesión al iniciar y la limpia al salir', async () => {
    vi.mocked(authApi.login).mockResolvedValue(session)
    const store = useAuthStore()

    await store.signIn('user@example.com', 'correct-password')
    expect(store.user).toEqual(session.user)
    expect(localStorage.getItem('examen-sw1.access-token')).toBe('jwt-token')

    store.logout()
    expect(store.user).toBeNull()
    expect(localStorage.getItem('examen-sw1.access-token')).toBeNull()
  })

  it('restaura /auth/me y descarta un token inválido', async () => {
    localStorage.setItem('examen-sw1.access-token', 'stored-token')
    vi.mocked(authApi.getCurrentUser).mockResolvedValue(session.user)
    const store = useAuthStore()
    await store.bootstrap()
    expect(store.isAuthenticated).toBe(true)

    vi.mocked(authApi.getCurrentUser).mockRejectedValueOnce(new Error('unauthorized'))
    const secondPinia = createPinia()
    setActivePinia(secondPinia)
    const restored = useAuthStore()
    await restored.bootstrap()
    expect(restored.isAuthenticated).toBe(false)
  })

  it('adjunta Authorization y limpia la sesión cuando una request recibe 401', async () => {
    vi.mocked(authApi.login).mockResolvedValue(session)
    const store = useAuthStore()
    await store.signIn('user@example.com', 'correct-password')
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 401 }))
    vi.stubGlobal('fetch', fetchMock)

    await authenticatedFetch('/projects')
    const headers = fetchMock.mock.calls[0]?.[1]?.headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer jwt-token')
    expect(store.isAuthenticated).toBe(false)
  })
})
