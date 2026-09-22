import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import * as authApi from './auth-api'
import AuthScreen from './AuthScreen.vue'

vi.mock('./auth-api', () => ({ login: vi.fn(), register: vi.fn(), getCurrentUser: vi.fn() }))

describe('AuthScreen', () => {
  it('inicia sesión desde el formulario', async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      accessToken: 'token', tokenType: 'bearer', user: { id: 'user-id', email: 'user@example.com' },
    })
    const wrapper = mount(AuthScreen, { global: { plugins: [createPinia()] } })
    const inputs = wrapper.findAll('input')
    await inputs[0]?.setValue('user@example.com')
    await inputs[1]?.setValue('correct-password')
    await wrapper.find('form').trigger('submit')
    expect(authApi.login).toHaveBeenCalledWith('user@example.com', 'correct-password')
  })

  it('muestra el formulario de registro y reporta fallo', async () => {
    vi.mocked(authApi.register).mockRejectedValue(new Error('Email is already registered'))
    const wrapper = mount(AuthScreen, { global: { plugins: [createPinia()] } })
    await wrapper.findAll('button').find((button) => button.text().includes('Crear una cuenta'))?.trigger('click')
    const inputs = wrapper.findAll('input')
    await inputs[0]?.setValue('user@example.com')
    await inputs[1]?.setValue('correct-password')
    await wrapper.find('form').trigger('submit')
    await wrapper.vm.$nextTick()
    expect(authApi.register).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Email is already registered')
  })
})
