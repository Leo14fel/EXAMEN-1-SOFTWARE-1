import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, expect, it, vi } from 'vitest'
import AiRequestPanel from './AiRequestPanel.vue'
import * as api from './ai-api'
import { useEditorStore } from './editor-store'
import type { AiResult } from './ai-api'
import type { ProjectDocument } from './types'

vi.mock('./ai-api', async (original) => ({ ...await original<typeof import('./ai-api')>(),
  getAiStatus: vi.fn(), evaluateAi: vi.fn(), getAiResult: vi.fn() }))
const document: ProjectDocument = { id: 'project', ownerId: 'owner', metadata: {}, revision: 4,
  createdAt: '', updatedAt: '', umlModel: { elements: [] }, diagramLayout: { nodes: {} } }
function result(): AiResult { return {
  request: { id: 'request-event', requestId: 'request-id', kind: 'aiRequest', actorId: 'owner', actorName: 'Andrea', text: 'Crea Producto', sequence: 1, createdAt: '' },
  result: { id: 'result-event', requestId: 'request-id', kind: 'aiResult', actorId: 'ai:gemini', actorName: 'IA · Gemini', text: 'Propuesta: crear Producto. No se aplicó ningún cambio.', status: 'proposed', canApply: false, sequence: 2, createdAt: '' }, pending: false,
} }
beforeEach(() => {
  setActivePinia(createPinia()); vi.clearAllMocks()
  const store = useEditorStore()
  store.applyProjectDocument(structuredClone(document)); store.effectiveRole = 'EDITOR'; store.syncStatus = 'connected'
  store.applySessionPage({ projectId: document.id, events: [], participants: [], cursor: 0, version: 0, hasEarlier: false, hasMore: false })
  vi.mocked(api.getAiStatus).mockResolvedValue({ configured: true, mode: 'proposalOnly', modelCandidate: 'test-only' })
})

it('sin clave muestra el estado real y no permite enviar ni simula una respuesta', async () => {
  vi.mocked(api.getAiStatus).mockResolvedValue({ configured: false, mode: 'proposalOnly', modelCandidate: 'test-only' })
  const wrapper = mount(AiRequestPanel); await flushPromises()
  expect(wrapper.text()).toContain('pendiente de configuración')
  expect(wrapper.find('textarea').attributes('disabled')).toBeDefined()
  await wrapper.find('form').trigger('submit')
  expect(api.evaluateAi).not.toHaveBeenCalled(); wrapper.unmount()
})

it('el observador consulta la conversación y no puede solicitar una evaluación', async () => {
  useEditorStore().effectiveRole = 'VIEWER'
  const wrapper = mount(AiRequestPanel); await flushPromises()
  expect(wrapper.text()).toContain('Puedes consultar las solicitudes')
  await wrapper.find('form').trigger('submit')
  expect(api.evaluateAi).not.toHaveBeenCalled(); wrapper.unmount()
})

it('envía la revisión vigente y publica el resultado compartido sin cambiar el modelo', async () => {
  vi.mocked(api.evaluateAi).mockResolvedValue(result())
  const wrapper = mount(AiRequestPanel); await flushPromises()
  await wrapper.find('textarea').setValue('Crea Producto'); await wrapper.find('form').trigger('submit'); await flushPromises()
  expect(api.evaluateAi).toHaveBeenCalledWith('project', expect.objectContaining({ baseRevision: 4, text: 'Crea Producto' }))
  expect(useEditorStore().sessionEvents).toHaveLength(2)
  expect(useEditorStore().document).toEqual(document)
  expect(wrapper.text()).toContain('conversación del grupo')
  expect(wrapper.text()).not.toContain('Aplicar propuesta')
  wrapper.unmount()
})

it('tras una respuesta de red incierta solo consulta el mismo ID sin otra llamada de IA', async () => {
  vi.mocked(api.evaluateAi).mockRejectedValue(new Error('Conexión interrumpida'))
  const wrapper = mount(AiRequestPanel); await flushPromises()
  await wrapper.find('textarea').setValue('Crea Producto'); await wrapper.find('form').trigger('submit'); await flushPromises()
  const id = vi.mocked(api.evaluateAi).mock.calls[0]![1].id
  await wrapper.find('form').trigger('submit')
  expect(api.evaluateAi).toHaveBeenCalledTimes(1)
  vi.mocked(api.getAiResult).mockResolvedValue(result())
  await wrapper.findAll('button').find(button => button.text().includes('Consultar resultado'))!.trigger('click'); await flushPromises()
  expect(api.getAiResult).toHaveBeenCalledWith('project', id)
  expect(api.evaluateAi).toHaveBeenCalledTimes(1)
  wrapper.unmount()
})

it('si no se registró la solicitud, conserva el texto para enviarlo otra vez explícitamente', async () => {
  vi.mocked(api.evaluateAi).mockRejectedValue(new Error('Conexión interrumpida'))
  const wrapper = mount(AiRequestPanel); await flushPromises()
  await wrapper.find('textarea').setValue('Crea Producto'); await wrapper.find('form').trigger('submit'); await flushPromises()
  vi.mocked(api.getAiResult).mockRejectedValue(new api.AiApiError(404, 'AI_REQUEST_NOT_FOUND'))
  await wrapper.findAll('button').find(button => button.text().includes('Consultar resultado'))!.trigger('click'); await flushPromises()
  expect(wrapper.text()).toContain('no llegó a registrarse')
  expect((wrapper.find('textarea').element as HTMLTextAreaElement).value).toBe('Crea Producto')
  expect(api.evaluateAi).toHaveBeenCalledTimes(1); wrapper.unmount()
})

it('descarta una respuesta tardía al cambiar de proyecto', async () => {
  let resolve!: (value: AiResult) => void
  vi.mocked(api.evaluateAi).mockReturnValue(new Promise(done => { resolve = done }))
  const wrapper = mount(AiRequestPanel); await flushPromises()
  await wrapper.find('textarea').setValue('Crea Producto'); await wrapper.find('form').trigger('submit')
  wrapper.unmount()
  useEditorStore().applyProjectDocument({ ...structuredClone(document), id: 'other' })
  resolve(result()); await flushPromises()
  expect(useEditorStore().sessionEvents).toHaveLength(0)
})

it('avisa si el diagrama cambia después de recibir una propuesta', async () => {
  const value = result()
  value.result!.baseRevision = 4
  vi.mocked(api.evaluateAi).mockResolvedValue(value)
  const wrapper = mount(AiRequestPanel); await flushPromises()
  await wrapper.find('textarea').setValue('Crea Producto'); await wrapper.find('form').trigger('submit'); await flushPromises()
  useEditorStore().applyProjectDocument({ ...structuredClone(document), revision: 5 })
  await flushPromises()
  expect(wrapper.text()).toContain('El diagrama cambió desde esta evaluación')
  expect(api.evaluateAi).toHaveBeenCalledTimes(1)
  wrapper.unmount()
})
