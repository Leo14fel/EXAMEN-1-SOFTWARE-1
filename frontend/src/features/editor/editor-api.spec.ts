import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  createProject,
  EditorApiError,
  executeProjectCommand,
  getProject,
  listProjects,
  redoProject,
  undoProject,
} from './editor-api'
import type { ProjectDocument, ProjectEditorState, UmlClass } from './types'

const document: ProjectDocument = {
  id: '11111111-1111-1111-1111-111111111111',
  metadata: { name: 'Ventas' },
  ownerId: '22222222-2222-2222-2222-222222222222',
  revision: 3,
  createdAt: '2026-09-15T12:00:00Z',
  updatedAt: '2026-09-15T12:01:00Z',
  umlModel: { elements: [] },
  diagramLayout: { nodes: {} },
}

const editorState: ProjectEditorState = { document, canUndo: true, canRedo: false }

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('editor api', () => {
  it('crea proyectos sin enviar ownerId', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(document), { status: 201 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(createProject({ name: 'Ventas' })).resolves.toEqual(document)

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/projects', {
      method: 'POST',
      headers: expect.any(Headers),
      body: JSON.stringify({ metadata: { name: 'Ventas' } }),
    })
  })

  it('lista y abre proyectos persistentes', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify([
            {
              id: document.id,
              ownerId: document.ownerId,
              metadata: document.metadata,
              revision: document.revision,
              createdAt: document.createdAt,
              updatedAt: document.updatedAt,
            },
          ]),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify(document), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(listProjects()).resolves.toHaveLength(1)
    await expect(getProject(document.id)).resolves.toEqual(document)

    expect(fetchMock).toHaveBeenNthCalledWith(1, 'http://localhost:8000/projects', {
      headers: expect.any(Headers),
    })
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      `http://localhost:8000/projects/${document.id}`,
      { headers: expect.any(Headers) },
    )
  })

  it('envía comandos con la revision actual', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(editorState), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    const umlClass: UmlClass = {
      id: '33333333-3333-3333-3333-333333333333',
      kind: 'class',
      name: 'Cliente',
      visibility: 'public',
      attributes: [],
      operations: [],
    }

    await executeProjectCommand(document.id, document.revision, {
      commandType: 'addElement',
      element: umlClass,
    })

    expect(fetchMock).toHaveBeenCalledWith(
      `http://localhost:8000/projects/${document.id}/commands`,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          baseRevision: document.revision,
          command: { commandType: 'addElement', element: umlClass },
        }),
      }),
    )
  })

  it('envía Undo y Redo con la revision actual', async () => {
    const fetchMock = vi
      .fn()
      .mockImplementation(() => Promise.resolve(new Response(JSON.stringify(editorState), { status: 200 })))
    vi.stubGlobal('fetch', fetchMock)

    await undoProject(document.id, document.revision)
    await redoProject(document.id, document.revision)

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      `http://localhost:8000/projects/${document.id}/undo`,
      expect.objectContaining({ body: JSON.stringify({ baseRevision: document.revision }) }),
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      `http://localhost:8000/projects/${document.id}/redo`,
      expect.objectContaining({ body: JSON.stringify({ baseRevision: document.revision }) }),
    )
  })

  it('expone códigos estables del backend', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ detail: { code: 'ELEMENT_ALREADY_EXISTS', message: 'UML element exists' } }),
          { status: 409 },
        ),
      ),
    )

    await expect(getProject(document.id)).rejects.toMatchObject({
      status: 409,
      code: 'ELEMENT_ALREADY_EXISTS',
    })
  })
})
