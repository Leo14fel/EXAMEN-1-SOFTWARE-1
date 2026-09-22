import { config } from '@vue/test-utils'
import { vuetify } from '../plugins/vuetify'

// Register the same plugin as the application for every Vue component test.
config.global.plugins = [vuetify]
class ResizeObserverMock implements ResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}

Object.defineProperty(globalThis, 'ResizeObserver', {
  configurable: true,
  writable: true,
  value: ResizeObserverMock,
})

Object.defineProperty(globalThis, 'visualViewport', {
  configurable: true,
  value: {
    addEventListener(): void {},
    removeEventListener(): void {},
  },
})
