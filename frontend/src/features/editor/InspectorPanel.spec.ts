import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import InspectorPanel from './InspectorPanel.vue'
import type { ProjectDocument } from './types'

function documentWithClass(): ProjectDocument {
  return {
    id: '00000000-0000-0000-0000-000000000001',
    metadata: {},
    ownerId: '00000000-0000-0000-0000-000000000002',
    revision: 1,
    createdAt: '2026-09-15T12:00:00Z',
    updatedAt: '2026-09-15T12:01:00Z',
    umlModel: {
      elements: [
        {
          id: '00000000-0000-0000-0000-000000000010',
          kind: 'class',
          name: 'Cliente',
          visibility: 'public',
          attributes: [
            {
              id: '00000000-0000-0000-0000-000000000011',
              kind: 'attribute',
              name: 'email',
              type: 'String',
              visibility: 'private',
            },
          ],
          operations: [],
        },
      ],
    },
    diagramLayout: { nodes: {} },
  }
}

describe('InspectorPanel', () => {
  it('clona una clase reactiva para editarla sin DataCloneError', async () => {
    const document = documentWithClass()

    const wrapper = mount(InspectorPanel, {
      props: {
        document,
        selectedElementId: '00000000-0000-0000-0000-000000000010',
        busy: false,
      },
    })

    expect(wrapper.text()).toContain('Clase UML')
    expect(wrapper.text()).toContain('Atributos')

    const nameInput = wrapper.find('input')
    expect(nameInput.exists()).toBe(true)

    await nameInput.setValue('ClienteActualizado')

    expect((nameInput.element as HTMLInputElement).value).toBe('ClienteActualizado')
    expect(document.umlModel.elements[0]).toMatchObject({
      kind: 'class',
      name: 'Cliente',
    })
  })
})