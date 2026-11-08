import { mount } from '@vue/test-utils'
import { afterEach, expect, it, vi } from 'vitest'
import PresencePanel from './PresencePanel.vue'
import { cursorOnCanvas, presenceColor } from './presence-ui'
import { useEditorStore } from './editor-store'
import { createPinia, setActivePinia } from 'pinia'
import type { Participant } from './editor-sync'
import type { ProjectDocument } from './types'

const document: ProjectDocument = {
  id: 'project', ownerId: 'owner', metadata: {}, revision: 8,
  createdAt: '', updatedAt: '', umlModel: { elements: [
    { id: 'class', kind: 'class', name: 'Cliente', visibility: 'public', attributes: [], operations: [] },
  ] }, diagramLayout: { nodes: {} },
}
const peer: Participant = { sessionId: 'peer-session', userId: 'peer-user', name: '<script>Andrea</script>',
  role: 'EDITOR', lastActivity: '2026-11-07T12:00:00Z', selectedElementId: 'class',
  editingElementId: 'class', cursor: { x: 5, y: 10 } }

afterEach(() => vi.useRealTimers())

it('muestra identidad escapada, edición y selección; anuncia entrada y salida temporal', async () => {
  vi.useFakeTimers()
  const wrapper = mount(PresencePanel, { props: { document, participants: [], ownSessionId: 'mine' } })
  await wrapper.setProps({ participants: [peer] })
  expect(wrapper.text()).toContain('Editando Cliente')
  expect(wrapper.find('script').exists()).toBe(false)
  await wrapper.find('.v-chip').trigger('click')
  expect(wrapper.emitted('select')?.[0]).toEqual(['class'])
  expect(wrapper.get('[role="status"]').text()).toContain('se conectó')
  await wrapper.setProps({ participants: [] })
  expect(wrapper.get('[role="status"]').text()).toContain('se desconectó')
  await vi.advanceTimersByTimeAsync(4000)
  expect(wrapper.get('[role="status"]').text()).toBe('')
  wrapper.unmount()
})

it('no renderiza la propia sesión como un cursor remoto', () => {
  const wrapper = mount(PresencePanel, { props: { document, participants: [peer], ownSessionId: peer.sessionId } })
  expect(wrapper.find('.v-chip').exists()).toBe(false)
  wrapper.unmount()
})

it('presencia separada no cambia revisión ni documento y rechaza otro proyecto', () => {
  setActivePinia(createPinia())
  const store = useEditorStore()
  store.applyProjectDocument(document)
  store.applyPresence({ type: 'presence', projectId: 'other', sessionId: 'mine', participants: [peer] })
  expect(store.participants).toEqual([])
  store.applyPresence({ type: 'presence', projectId: document.id, sessionId: 'mine', participants: [peer] })
  expect(store.participants).toEqual([peer])
  expect(store.document).toEqual(document)
  expect(store.document?.revision).toBe(8)
})

it('proyecta el cursor con pan/zoom y mantiene un color estable por usuario', () => {
  expect(cursorOnCanvas({ x: 5, y: 10 }, { x: 100, y: -50, zoom: 2 })).toEqual({ left: '110px', top: '-30px' })
  expect(presenceColor('Andrea')).toBe(presenceColor('Andrea'))
})
