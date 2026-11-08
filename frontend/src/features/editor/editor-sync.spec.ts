import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { applyDocumentChanges, connectProjectSync, type PatchEvent } from './editor-sync'
import { useEditorStore } from './editor-store'
import type { ProjectDocument } from './types'

const document: ProjectDocument = {
  id: '11111111-1111-1111-1111-111111111111',
  ownerId: '22222222-2222-2222-2222-222222222222',
  metadata: { name: 'Ventas' }, revision: 0,
  createdAt: '2026-11-07T00:00:00Z', updatedAt: '2026-11-07T00:00:00Z',
  umlModel: { elements: [] }, diagramLayout: { nodes: {} },
}
const patch: PatchEvent = {
  type: 'patch', projectId: document.id, baseRevision: 0, revision: 1,
  changes: [{ op: 'set', path: ['revision'], value: 1 },
    { op: 'set', path: ['metadata', 'name'], value: 'Compartido' }],
  effectiveRole: 'EDITOR', canUndo: true, canRedo: false,
}

class FakeSocket {
  static instances: FakeSocket[] = []
  onopen: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onclose: ((event: { code: number }) => void) | null = null
  onerror: (() => void) | null = null
  sent: string[] = []
  close = vi.fn()
  constructor(readonly url: URL) { FakeSocket.instances.push(this) }
  send(value: string) { this.sent.push(value) }
  message(value: unknown) { this.onmessage?.({ data: JSON.stringify(value) }) }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.useFakeTimers()
  FakeSocket.instances = []
  vi.stubGlobal('WebSocket', FakeSocket)
})
afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals() })

describe('proyección colaborativa', () => {
  it('aplica delta atómico, ignora duplicados y detecta hueco sin cambiar el documento', () => {
    const store = useEditorStore()
    store.applyProjectDocument(document)
    expect(store.applySyncEvent(patch)).toBe(true)
    expect(store.document?.metadata.name).toBe('Compartido')
    expect(store.document?.revision).toBe(1)
    expect(store.applySyncEvent(patch)).toBe(true)
    const before = JSON.stringify(store.document)
    expect(store.applySyncEvent({ ...patch, baseRevision: 2, revision: 3 })).toBe(false)
    expect(JSON.stringify(store.document)).toBe(before)
    expect(store.applySyncEvent({ ...patch, projectId: 'otro' })).toBe(false)
    expect(document.revision).toBe(0)
  })

  it('snapshot recupera permisos y revisión; HTTP atrasado no hace retroceder la proyección', () => {
    const store = useEditorStore()
    store.applyProjectDocument(document)
    expect(store.applySyncEvent({ type: 'snapshot', document: { ...document, revision: 4 },
      canUndo: false, canRedo: false, effectiveRole: 'VIEWER' })).toBe(true)
    store.applyProjectState({ document: { ...document, revision: 1 }, canUndo: true, canRedo: true })
    expect(store.document?.revision).toBe(4)
    expect(store.effectiveRole).toBe('VIEWER')
    expect(store.canUndo).toBe(false)
  })

  it('un delta inválido no publica cambios parciales ni altera prototipos', () => {
    expect(() => applyDocumentChanges(document, [
      { op: 'set', path: ['revision'], value: 1 },
      { op: 'set', path: ['missing', 'x'], value: 2 },
    ])).toThrow()
    expect(() => applyDocumentChanges(document, [
      { op: 'set', path: ['__proto__', 'polluted'], value: true },
    ])).toThrow()
    expect(document.revision).toBe(0)
    expect(({} as Record<string, unknown>).polluted).toBeUndefined()
  })

  it('aplica eliminaciones de listas y cambios de layout sin sustituir todo el modelo', () => {
    const source = { ...document, metadata: { items: [1, 2, 3] } }
    const next = applyDocumentChanges(source, [
      { op: 'remove', path: ['metadata', 'items', 2] },
      { op: 'remove', path: ['metadata', 'items', 1] },
      { op: 'set', path: ['metadata', 'items', 1], value: 4 },
      { op: 'set', path: ['diagramLayout', 'nodes', 'clase'], value: { x: 2, y: 3 } },
    ])
    expect(next.metadata.items).toEqual([1, 4])
    expect(next.diagramLayout.nodes.clase).toEqual({ x: 2, y: 3 })
    expect(source.metadata.items).toEqual([1, 2, 3])
  })
})

describe('conexión y recuperación', () => {
  function start(onEvent = vi.fn().mockReturnValue(true)) {
    const onStatus = vi.fn(), onForbidden = vi.fn()
    const stop = connectProjectSync({ projectId: document.id, token: 'local-test-token',
      onEvent, onStatus, onForbidden })
    return { stop, onEvent, onStatus, onForbidden, socket: FakeSocket.instances[0]! }
  }

  it('autentica fuera de la URL y solicita una sola recuperación ante hueco', () => {
    const state = start(vi.fn().mockReturnValue(false))
    expect(state.socket.url.protocol).toBe('ws:')
    expect(String(state.socket.url)).not.toContain('local-test-token')
    state.socket.onopen?.()
    expect(JSON.parse(state.socket.sent[0]!)).toEqual({ type: 'authenticate', token: 'local-test-token' })
    state.socket.message(patch)
    state.socket.message(patch)
    expect(state.socket.sent.filter((raw) => JSON.parse(raw).type === 'resync')).toHaveLength(1)
    state.onEvent.mockReturnValue(true)
    state.socket.message({ type: 'snapshot', document, effectiveRole: 'EDITOR', canUndo: false, canRedo: false })
    expect(state.onStatus).toHaveBeenLastCalledWith('connected')
    state.stop()
  })

  it('reconecta tras corte y detiene eventos/timers al cambiar de proyecto o salir', () => {
    const state = start()
    state.socket.onclose?.({ code: 1006 })
    expect(state.onStatus).toHaveBeenLastCalledWith('reconnecting')
    vi.advanceTimersByTime(1000)
    expect(FakeSocket.instances).toHaveLength(2)
    state.socket.message(patch)
    expect(state.onEvent).not.toHaveBeenCalled()
    state.stop()
    FakeSocket.instances[1]!.onclose?.({ code: 1006 })
    vi.advanceTimersByTime(30000)
    expect(FakeSocket.instances).toHaveLength(2)
  })

  it.each([4401, 4403, 4404])('cierre de seguridad %s no reconecta', (code) => {
    const state = start()
    state.socket.onclose?.({ code })
    expect(state.onForbidden).toHaveBeenCalledWith(code)
    vi.advanceTimersByTime(30000)
    expect(FakeSocket.instances).toHaveLength(1)
    state.stop()
  })
})


describe('presencia por la conexión compartida', () => {
  it('agrupa cursor/selección en dos envíos por segundo y reenvía estado al reconectar', () => {
    const onEvent = vi.fn().mockReturnValue(true), onPresence = vi.fn()
    const stop = connectProjectSync({ projectId: document.id, token: 'test-token', onEvent,
      onPresence, onStatus: vi.fn(), onForbidden: vi.fn() })
    const socket = FakeSocket.instances[0]!
    socket.onopen?.()
    expect(JSON.parse(socket.sent[0]!)).toMatchObject({ presence: true })
    const snapshot = { type: 'snapshot', document, canUndo: false, canRedo: false, effectiveRole: 'EDITOR' }
    socket.message(snapshot)
    for (let i = 0; i < 50; i++) {
      stop.updatePresence({ cursor: { x: i, y: i }, selectedElementId: null, editingElementId: null })
    }
    expect(socket.sent).toHaveLength(1)
    vi.advanceTimersByTime(500)
    expect(socket.sent).toHaveLength(2)
    expect(JSON.parse(socket.sent[1]!).cursor).toEqual({ x: 49, y: 49 })
    // Receiving remote diagram updates does not manufacture local activity.
    socket.message(patch)
    vi.advanceTimersByTime(500)
    expect(socket.sent).toHaveLength(2)
    socket.message({ type: 'presence', projectId: document.id, sessionId: 'own', participants: [] })
    expect(onPresence).toHaveBeenCalledOnce()
    expect(onEvent).toHaveBeenCalledTimes(2)
    socket.onclose?.({ code: 1006 })
    vi.advanceTimersByTime(1000)
    const next = FakeSocket.instances[1]!
    next.onopen?.()
    next.message(snapshot)
    vi.advanceTimersByTime(500)
    expect(JSON.parse(next.sent[1]!).cursor).toEqual({ x: 49, y: 49 })
    stop()
  })

  it('no envía presencia pendiente después de salir', () => {
    const stop = connectProjectSync({ projectId: document.id, token: 'test',
      onEvent: () => true, onPresence: vi.fn(), onStatus: vi.fn(), onForbidden: vi.fn() })
    const socket = FakeSocket.instances[0]!
    socket.message({ type: 'snapshot', document, canUndo: false, canRedo: false, effectiveRole: 'EDITOR' })
    stop.updatePresence({ cursor: null, selectedElementId: 'class', editingElementId: 'class' })
    stop()
    vi.advanceTimersByTime(1000)
    expect(socket.sent).toEqual([])
  })
})


it('negocia conversación grupal y procesa páginas sin confundirlas con cambios UML', () => {
  const onConversation = vi.fn(), onEvent = vi.fn().mockReturnValue(true)
  const stop = connectProjectSync({ projectId: document.id, token: 'test', onEvent,
    onConversation, onStatus: vi.fn(), onForbidden: vi.fn() })
  const socket = FakeSocket.instances[0]!
  socket.onopen?.()
  expect(JSON.parse(socket.sent[0]!)).toMatchObject({ conversation: true })
  socket.message({ type: 'snapshot', document, effectiveRole: 'EDITOR', canUndo: false, canRedo: false })
  socket.message({ type: 'conversation', projectId: document.id, events: [], participants: [],
    cursor: 0, version: 0, hasEarlier: false, hasMore: false })
  expect(onConversation).toHaveBeenCalledOnce()
  expect(onEvent).toHaveBeenCalledOnce()
  stop()
})
