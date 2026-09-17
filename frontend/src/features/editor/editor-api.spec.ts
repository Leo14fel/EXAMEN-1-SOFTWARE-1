import { afterEach, describe, expect, it, vi } from 'vitest'
import { createEditorSession, EditorApiError, executeEditorCommand } from './editor-api'
import type { EditorSessionState, UmlClass } from './types'

const state: EditorSessionState = {
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

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('editor api', () => {
  it('crea una sesión temporal de editor', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(state), { status: 201 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(createEditorSession()).resolves.toEqual(state)
    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/editor/sessions', {
      method: 'POST',
    })
  })

  it('envía comandos usando el contrato público camelCase', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ...state, canUndo: true }), { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const umlClass: UmlClass = {
      id: '44444444-4444-4444-4444-444444444444',
      kind: 'class',
      name: 'Cliente',
      visibility: 'public',
      attributes: [],
      operations: [],
    }

    await executeEditorCommand(state.sessionId, {
      commandType: 'addElement',
      element: umlClass,
    })

    expect(fetchMock).toHaveBeenCalledWith(
      `http://localhost:8000/editor/sessions/${state.sessionId}/commands`,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ commandType: 'addElement', element: umlClass }),
      }),
    )
  })

  it('expone código estable cuando el backend rechaza el comando', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: { code: 'ELEMENT_ALREADY_EXISTS', message: 'UML element already exists' },
          }),
          { status: 409 },
        ),
      ),
    )

    try {
      await createEditorSession()
      throw new Error('Se esperaba EditorApiError')
    } catch (error) {
      expect(error).toBeInstanceOf(EditorApiError)
      expect((error as EditorApiError).status).toBe(409)
      expect((error as EditorApiError).code).toBe('ELEMENT_ALREADY_EXISTS')
    }
  })
})