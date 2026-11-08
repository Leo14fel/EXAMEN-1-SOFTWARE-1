import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, expect, it, vi } from 'vitest'
import { useEditorStore } from './editor-store'
import GroupSessionPanel from './GroupSessionPanel.vue'
import * as api from './group-session-api'
import type { SessionEvent, SessionPage } from './group-session-api'
import type { ProjectDocument } from './types'

vi.mock('./group-session-api', async (original) => ({
  ...await original<typeof import('./group-session-api')>(), sendSessionMessage: vi.fn(), getEarlierSession: vi.fn(),
}))
const document: ProjectDocument = { id: 'project', ownerId: 'owner', metadata: {}, revision: 9,
  createdAt: '', updatedAt: '', umlModel: { elements: [] }, diagramLayout: { nodes: {} } }
function event(sequence: number): SessionEvent { return { id: `m${sequence}`, sequence, kind: 'message', actorId: 'owner', actorName: 'Andrea', createdAt: '2026-11-07T00:00:00Z', text: `Mensaje ${sequence}` } }
function page(events: SessionEvent[]): SessionPage { return { projectId: document.id, events,
  participants: [{ userId: 'owner', name: 'Andrea', joinedAt: '' }], cursor: events.at(-1)?.sequence ?? 0,
  version: 10, hasEarlier: true, hasMore: false } }
beforeEach(() => { setActivePinia(createPinia()); vi.clearAllMocks() })

it('muestra solicitudes y resultados de IA como contenido compartido sin tratarlos como cambios UML', () => {
  const store = ready()
  store.applySessionPage(page([
    { ...event(1), kind: 'aiRequest', text: 'Crea Producto' },
    { ...event(2), kind: 'aiResult', actorName: 'IA · Gemini', text: '<script>no ejecutar</script>', status: 'proposed', canApply: false },
  ]))
  const wrapper = mount(GroupSessionPanel)
  expect(wrapper.text()).toContain('Solicitud a IA:')
  expect(wrapper.text()).toContain('evaluación sin aplicar cambios')
  expect(wrapper.text()).toContain('<script>no ejecutar</script>')
  expect(wrapper.find('script').exists()).toBe(false)
  expect(store.document).toEqual(document)
  wrapper.unmount()
})
function ready() {
  const store = useEditorStore()
  store.applyProjectDocument(document)
  store.effectiveRole = 'EDITOR'
  store.syncStatus = 'connected'
  store.applySessionPage(page([]))
  return store
}

it('mezcla páginas y difusión sin duplicar ni filtrar otro proyecto o alterar UML', () => {
  const store = ready()
  store.applySessionPage(page([event(3), event(4)]))
  store.applySessionPage(page([event(1), event(2), event(3)]))
  store.applySessionPage({ ...page([event(5)]), projectId: 'other' })
  expect(store.sessionEvents.map(entry => entry.sequence)).toEqual([1, 2, 3, 4])
  expect(store.document).toEqual(document)
})

it('conserva borrador e ID al reintentar un envío fallido', async () => {
  const store = ready()
  vi.mocked(api.sendSessionMessage).mockRejectedValueOnce(new Error('Sin conexión')).mockResolvedValueOnce(event(1))
  const wrapper = mount(GroupSessionPanel)
  await wrapper.find('textarea').setValue('Hola grupo')
  await wrapper.find('form').trigger('submit')
  await vi.waitFor(() => expect(store.sessionSending).toBe(false))
  expect((wrapper.find('textarea').element as HTMLTextAreaElement).value).toBe('Hola grupo')
  await wrapper.find('form').trigger('submit')
  await vi.waitFor(() => expect(store.sessionEvents).toHaveLength(1))
  const calls = vi.mocked(api.sendSessionMessage).mock.calls
  expect(calls[0]?.[1]).toBe(calls[1]?.[1])
  expect(calls[0]?.[2]).toBe('Hola grupo')
  await vi.waitFor(() => expect((wrapper.find('textarea').element as HTMLTextAreaElement).value).toBe(''))
  expect(store.document?.revision).toBe(9)
  wrapper.unmount()
})

it('VIEWER consulta historial sin poder enviar', async () => {
  const store = ready()
  store.effectiveRole = 'VIEWER'
  store.applySessionPage(page([event(1)]))
  const wrapper = mount(GroupSessionPanel)
  expect(wrapper.text()).toContain('Mensaje 1')
  expect(wrapper.find('textarea').attributes('disabled')).toBeDefined()
  await wrapper.find('form').trigger('submit')
  expect(api.sendSessionMessage).not.toHaveBeenCalled()
  wrapper.unmount()
})

it('actividad y mensajes son texto escapado, con autor y revisión', () => {
  const store = ready()
  store.applySessionPage(page([{ ...event(1), text: '<script>no ejecutar</script>' }, {
    ...event(2), kind: 'activity', action: 'undo', projectRevision: 10,
  }]))
  const wrapper = mount(GroupSessionPanel)
  expect(wrapper.find('script').exists()).toBe(false)
  expect(wrapper.text()).toContain('<script>no ejecutar</script>')
  expect(wrapper.text()).toContain('deshizo una operación')
  expect(wrapper.text()).toContain('revisión 10')
  wrapper.unmount()
})

it('carga anteriores y elimina el botón cuando llegó al inicio', async () => {
  const store = ready()
  store.applySessionPage(page([event(3)]))
  vi.mocked(api.getEarlierSession).mockResolvedValue(page([event(1), event(2)]))
  const wrapper = mount(GroupSessionPanel)
  await wrapper.findAll('button').find(button => button.text().includes('Cargar anteriores'))!.trigger('click')
  await vi.waitFor(() => expect(store.sessionEvents).toHaveLength(3))
  expect(api.getEarlierSession).toHaveBeenCalledWith(document.id, 3)
  expect(wrapper.text()).not.toContain('Cargar anteriores')
  wrapper.unmount()
})

it('una respuesta HTTP de otro proyecto abierto no contamina el historial actual', async () => {
  const store = ready()
  let resolve!: (entry: SessionEvent) => void
  vi.mocked(api.sendSessionMessage).mockReturnValue(new Promise(done => { resolve = done }))
  const pending = store.sendGroupMessage('id', 'hola')
  store.applyProjectDocument({ ...document, id: 'other' })
  store.sessionEvents = []
  resolve(event(1))
  await pending
  expect(store.sessionEvents).toEqual([])
})
