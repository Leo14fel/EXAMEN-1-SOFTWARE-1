import { createPinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App.vue'
import * as editorApi from './features/editor/editor-api'
import type { EditorSessionState } from './features/editor/types'

vi.mock('./features/editor/editor-api', () => ({
  createEditorSession: vi.fn(),
  getEditorSession: vi.fn(),
  executeEditorCommand: vi.fn(),
  undoEditorSession: vi.fn(),
  redoEditorSession: vi.fn(),
}))

const emptySession: EditorSessionState = {
  sessionId: '11111111-1111-1111-1111-111111111111',
  document: {
    id: '22222222-2222-2222-2222-222222222222',
    metadata: {},
    ownerId: '33333333-3333-3333-3333-333333333333',
    revision: 0,
    createdAt: '2026-09-15T12:00:00Z',
    updatedAt: '2026-09-15T12:00:00Z',
    umlModel: { elements: [] },
    diagramLayout: { nodes: {} },
  },
  canUndo: false,
  canRedo: false,
}

function mountApp() {
  return mount(App, {
    global: {
      plugins: [createPinia()],
      stubs: {
        UmlCanvas: {
          props: ['document', 'selectedElementId', 'busy'],
          template: '<div class="uml-canvas-stub">Canvas UML</div>',
        },
        RelationshipDialog: true,
      },
    },
  })
}

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(editorApi.createEditorSession).mockResolvedValue(emptySession)
  })

  it('inicia el editor y muestra el workspace UML', async () => {
    const wrapper = mountApp()
    await flushPromises()

    expect(editorApi.createEditorSession).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('Editor UML')
    expect(wrapper.text()).toContain('Revisión 0')
    expect(wrapper.text()).toContain('Nueva clase')
    expect(wrapper.text()).toContain('Canvas UML')
  })

  it('crea una clase mediante addElement y actualiza la revision', async () => {
    vi.mocked(editorApi.executeEditorCommand).mockImplementation(async (sessionId, command) => {
      expect(sessionId).toBe(emptySession.sessionId)
      if (command.commandType !== 'addElement' || command.element.kind !== 'class') {
        throw new Error('Comando inesperado')
      }
      return {
        ...emptySession,
        document: {
          ...emptySession.document,
          revision: 1,
          umlModel: { elements: [command.element] },
        },
        canUndo: true,
      }
    })

    const wrapper = mountApp()
    await flushPromises()

    const button = wrapper.findAll('button').find((item) => item.text().includes('Nueva clase'))
    expect(button).toBeDefined()
    await button!.trigger('click')
    await flushPromises()

    expect(editorApi.executeEditorCommand).toHaveBeenCalledOnce()
    expect(vi.mocked(editorApi.executeEditorCommand).mock.calls[0][1]).toMatchObject({
      commandType: 'addElement',
      element: {
        kind: 'class',
        name: 'Clase1',
        visibility: 'public',
      },
    })
    expect(wrapper.text()).toContain('Revisión 1')
  })
})