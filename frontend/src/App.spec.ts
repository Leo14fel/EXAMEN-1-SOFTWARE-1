import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App.vue'

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('backend unavailable'))))
  })

  it('muestra la fundación del proyecto', () => {
    const wrapper = mount(App)

    expect(wrapper.text()).toContain('Fundación del proyecto lista')
    expect(wrapper.text()).toContain('Backend: comprobando...')
  })
})
