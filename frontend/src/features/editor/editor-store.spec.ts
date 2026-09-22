import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as editorApi from './editor-api'
import { EditorApiError } from './editor-api'
import { useEditorStore } from './editor-store'
import type { ProjectDocument, ProjectEditorState, ProjectSummary, UmlClass } from './types'

vi.mock('./editor-api', () => ({
  createProject: vi.fn(),
  getProject: vi.fn(),
  listProjects: vi.fn(),
  executeProjectCommand: vi.fn(),
  undoProject: vi.fn(),
  redoProject: vi.fn(),
  EditorApiError: class EditorApiError extends Error {
    constructor(
      message: string,
      readonly status: number,
      readonly code?: string,
    ) {
      super(message)
    }
  },
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
  effectiveRole: 'EDITOR',
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  vi.mocked(editorApi.listProjects).mockResolvedValue([summary])
})

describe('editor store', () => {
  it('lista, crea y abre proyectos reemplazando la proyección', async () => {
    vi.mocked(editorApi.createProject).mockResolvedValue(document)
    vi.mocked(editorApi.getProject).mockResolvedValue(document)
    const store = useEditorStore()

    await store.loadProjects()
    await store.createProject('Ventas')
    await store.openProject(document.id)

    expect(editorApi.createProject).toHaveBeenCalledWith({ name: 'Ventas' })
    expect(editorApi.getProject).toHaveBeenCalledWith(document.id)
    expect(store.projects).toEqual([summary])
    expect(store.projectId).toBe(document.id)
    expect(store.document).toEqual(document)
    expect(store.canUndo).toBe(false)
    expect(store.canRedo).toBe(false)
  })

  it('cambia entre proyectos sin conservar la proyección anterior', async () => {
    const otherDocument: ProjectDocument = {
      ...document,
      id: '44444444-4444-4444-4444-444444444444',
      metadata: { name: 'Inventario' },
      revision: 3,
    }
    vi.mocked(editorApi.getProject)
      .mockResolvedValueOnce(document)
      .mockResolvedValueOnce(otherDocument)
    const store = useEditorStore()

    await store.openProject(document.id)
    await store.openProject(otherDocument.id)

    expect(store.projectId).toBe(otherDocument.id)
    expect(store.document).toEqual(otherDocument)
    expect(store.canUndo).toBe(false)
    expect(store.canRedo).toBe(false)
  })

  it('envía la revision actual y reemplaza con la respuesta autoritativa', async () => {
    const umlClass: UmlClass = {
      id: '33333333-3333-3333-3333-333333333333',
      kind: 'class',
      name: 'Cliente',
      visibility: 'public',
      attributes: [],
      operations: [],
    }
    const nextState: ProjectEditorState = {
      document: { ...document, revision: 1, umlModel: { elements: [umlClass] } },
      canUndo: true,
      canRedo: false,
    }
    vi.mocked(editorApi.getProject).mockResolvedValue(document)
    vi.mocked(editorApi.executeProjectCommand).mockResolvedValue(nextState)
    const store = useEditorStore()
    await store.openProject(document.id)

    await store.execute({ commandType: 'addElement', element: umlClass })

    expect(editorApi.executeProjectCommand).toHaveBeenCalledWith(document.id, 0, {
      commandType: 'addElement',
      element: umlClass,
    })
    expect(store.document).toEqual(nextState.document)
    expect(store.canUndo).toBe(true)
  })

  it('usa la revision actual para Undo y Redo', async () => {
    const state: ProjectEditorState = {
      document: { ...document, revision: 2 },
      canUndo: false,
      canRedo: true,
    }
    vi.mocked(editorApi.getProject).mockResolvedValue(document)
    vi.mocked(editorApi.undoProject).mockResolvedValue(state)
    vi.mocked(editorApi.redoProject).mockResolvedValue(state)
    const store = useEditorStore()
    await store.openProject(document.id)

    await store.undo()
    await store.redo()

    expect(editorApi.undoProject).toHaveBeenCalledWith(document.id, 0)
    expect(editorApi.redoProject).toHaveBeenCalledWith(document.id, 2)
  })

  it('recarga el documento autoritativo sólo ante conflicto de revision', async () => {
    const refreshed = { ...document, revision: 4 }
    vi.mocked(editorApi.getProject)
      .mockResolvedValueOnce(document)
      .mockResolvedValueOnce(refreshed)
    vi.mocked(editorApi.executeProjectCommand).mockRejectedValue(
      new EditorApiError('conflict', 409, 'PROJECT_REVISION_CONFLICT'),
    )
    const store = useEditorStore()
    await store.openProject(document.id)

    await expect(store.execute({ commandType: 'removeElement', elementId: document.id })).rejects.toThrow(
      'conflict',
    )

    expect(editorApi.getProject).toHaveBeenCalledTimes(2)
    expect(store.document).toEqual(refreshed)
    expect(store.canUndo).toBe(false)
    expect(store.canRedo).toBe(false)
    expect(store.error).toContain('recargó')
  })

  it('no recarga el documento para un error UML', async () => {
    vi.mocked(editorApi.getProject).mockResolvedValue(document)
    vi.mocked(editorApi.executeProjectCommand).mockRejectedValue(
      new EditorApiError('UML element already exists', 409, 'ELEMENT_ALREADY_EXISTS'),
    )
    const store = useEditorStore()
    await store.openProject(document.id)

    await expect(store.execute({ commandType: 'removeElement', elementId: document.id })).rejects.toThrow(
      'UML element already exists',
    )

    expect(editorApi.getProject).toHaveBeenCalledOnce()
    expect(store.document).toEqual(document)
  })

  it('expone el rechazo autoritativo de un ciclo de generalization', async () => {
    vi.mocked(editorApi.getProject).mockResolvedValue(document)
    vi.mocked(editorApi.executeProjectCommand).mockRejectedValue(
      new EditorApiError('Inheritance cycle detected', 409, 'GENERALIZATION_CYCLE'),
    )
    const store = useEditorStore()
    await store.openProject(document.id)

    await expect(store.execute({ commandType: 'removeElement', elementId: document.id })).rejects.toThrow(
      'Inheritance cycle detected',
    )

    expect(store.error).toBe('Inheritance cycle detected')
    expect(editorApi.getProject).toHaveBeenCalledOnce()
  })
})
