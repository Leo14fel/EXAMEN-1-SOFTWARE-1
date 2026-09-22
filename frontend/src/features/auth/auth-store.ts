import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { setAccessToken, setUnauthorizedHandler } from '../../services/api'
import { useEditorStore } from '../editor/editor-store'
import { getCurrentUser, login, register, type AuthSession, type AuthUser } from './auth-api'

const TOKEN_STORAGE_KEY = 'examen-sw1.access-token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_STORAGE_KEY))
  const user = ref<AuthUser | null>(null)
  const resolved = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const isAuthenticated = computed(() => token.value !== null && user.value !== null)

  function clearSession(): void {
    token.value = null
    user.value = null
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    setAccessToken(null)
    const editor = useEditorStore()
    editor.closeRealtime()
    editor.$reset()
  }

  function applySession(session: AuthSession): void {
    token.value = session.accessToken
    user.value = session.user
    localStorage.setItem(TOKEN_STORAGE_KEY, session.accessToken)
    setAccessToken(session.accessToken)
    setUnauthorizedHandler(clearSession)
  }

  async function bootstrap(): Promise<void> {
    setUnauthorizedHandler(clearSession)
    setAccessToken(token.value)
    if (!token.value) {
      resolved.value = true
      return
    }
    loading.value = true
    try {
      user.value = await getCurrentUser()
    } catch {
      clearSession()
    } finally {
      loading.value = false
      resolved.value = true
    }
  }

  async function signIn(email: string, password: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      applySession(await login(email, password))
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : 'No se pudo iniciar sesión'
      throw reason
    } finally {
      loading.value = false
      resolved.value = true
    }
  }

  async function signUp(email: string, password: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      applySession(await register(email, password))
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : 'No se pudo crear la cuenta'
      throw reason
    } finally {
      loading.value = false
      resolved.value = true
    }
  }

  function logout(): void {
    clearSession()
    resolved.value = true
  }

  return { token, user, resolved, loading, error, isAuthenticated, bootstrap, signIn, signUp, logout, clearSession }
})
