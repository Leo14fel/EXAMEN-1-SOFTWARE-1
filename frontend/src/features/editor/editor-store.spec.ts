import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as editorApi from './editor-api'
import { useEditorStore } from './editor-store'
import type { EditorSessionState, UmlClass } from './types'

vi.mock('./editor-api', () => ({
  createEditorSession: vi.fn(),
  getEditorSession: vi.fn(),
  executeEditorCommand: vi.fn(),
  undoEditorSession: vi.fn(),
  redoEditorSession: vi.fn(),
}))

const baseState: EditorSessionState = {
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

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('editor store', () => {
  it('inicia la sesión reemplazando su proyección local con el estado del backend', async () => {
    vi.mocked(editorApi.createEditorSession).mockResolvedValue(baseState)
    const store = useEditorStore()

    await store.startSession()

    expect(store.sessionId).toBe(baseState.sessionId)
    expect(store.document).toEqual(baseState.document)
    expect(store.document).not.toBe(baseState.document)
    expect(store.canUndo).toBe(false)
    expect(store.error).toBeNull()
  })

  it('ejecuta comandos mediante la API y no muta el UML localmente', async () => {
    const umlClass: UmlClass = {
      id: '44444444-4444-4444-4444-444444444444',
      kind: 'class',
      name: 'Cliente',
      visibility: 'public',
      attributes: [],
      operations: [],
    }
    const nextState: EditorSessionState = {
      ...baseState,
      document: {
        ...baseState.document,
        revision: 1,
        umlModel: { elements: [umlClass] },
      },
      canUndo: true,
    }
    vi.mocked(editorApi.createEditorSession).mockResolvedValue(baseState)
    vi.mocked(editorApi.executeEditorCommand).mockResolvedValue(nextState)
    const store = useEditorStore()
    await store.startSession()

    await store.execute({ commandType: 'addElement', element: umlClass })

    expect(editorApi.executeEditorCommand).toHaveBeenCalledWith(baseState.sessionId, {
      commandType: 'addElement',
      element: umlClass,
    })
    expect(store.document?.revision).toBe(1)
    expect(store.document?.umlModel.elements).toEqual([umlClass])
    expect(store.canUndo).toBe(true)
  })
})