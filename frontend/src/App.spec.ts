import { createPinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App.vue'
import * as editorApi from './features/editor/editor-api'
import type { ProjectDocument, ProjectSummary } from './features/editor/types'

vi.mock('./features/editor/editor-api', () => ({
  createProject: vi.fn(),
  getProject: vi.fn(),
  listProjects: vi.fn(),
  executeProjectCommand: vi.fn(),
  undoProject: vi.fn(),
  redoProject: vi.fn(),
}))

const document: ProjectDocument = {
  id: '11111111-1111-1111-1111-111111111111',
  metadata: { name: 'Ventas' },
  ownerId: '22222222-2222-2222-2222-222222222222',
  revision: 0,
  createdAt: '2026-09-15T12:00:00Z',
  updatedAt: '2026-09-15T12:00:00Z',
  umlModel: { elements: [] },
  diagramLayout: { nodes: {} },
}

const summary: ProjectSummary = {
  id: document.id,
  ownerId: document.ownerId,
  metadata: document.metadata,
  revision: document.revision,
  createdAt: document.createdAt,
  updatedAt: document.updatedAt,
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
    vi.mocked(editorApi.listProjects).mockResolvedValue([summary])
  })

  it('carga proyectos persistentes sin crear una sesión temporal', async () => {
    const wrapper = mountApp()
    await flushPromises()

    expect(editorApi.listProjects).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('Proyectos')
    expect(wrapper.text()).toContain('Nuevo proyecto')
    expect(wrapper.text()).toContain('Abra o cree un proyecto para comenzar.')
  })
})
