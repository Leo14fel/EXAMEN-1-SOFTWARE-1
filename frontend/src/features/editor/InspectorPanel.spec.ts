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

function documentWithRelationship(kind: 'association' | 'generalization'): ProjectDocument {
  const document = documentWithClass()
  document.umlModel.elements.push({
    id: '00000000-0000-0000-0000-000000000020',
    kind: 'class',
    name: 'Pedido',
    visibility: 'public',
    attributes: [],
    operations: [],
  })
  document.umlModel.elements.push(
    kind === 'generalization'
      ? {
          id: '00000000-0000-0000-0000-000000000030',
          kind,
          sourceId: '00000000-0000-0000-0000-000000000020',
          targetId: '00000000-0000-0000-0000-000000000010',
        }
      : {
          id: '00000000-0000-0000-0000-000000000030',
          kind,
          sourceId: '00000000-0000-0000-0000-000000000010',
          targetId: '00000000-0000-0000-0000-000000000020',
          sourceMultiplicity: { lower: 1, upper: 1 },
          targetMultiplicity: { lower: 0, upper: '*' },
        },
  )
  return document
}

async function setInputByLabel(
  wrapper: ReturnType<typeof mount>,
  label: string,
  value: string,
): Promise<void> {
  const labelElement = wrapper.findAll('label').find((item) => item.text() === label)
  if (!labelElement) throw new Error(`expected ${label} label`)
  const input = wrapper.find(`#${labelElement.attributes('for')}`)
  await input.setValue(value)
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

  it('conserva el borrador sucio cuando cambia la revision por una mutacion externa', async () => {
    const document = documentWithClass()

    const wrapper = mount(InspectorPanel, {
      props: {
        document,
        selectedElementId: '00000000-0000-0000-0000-000000000010',
        busy: false,
      },
    })

    const nameInput = wrapper.find('input')
    await nameInput.setValue('ClienteBorrador')

    const updatedDocument = structuredClone(document)
    updatedDocument.revision = 2
    updatedDocument.diagramLayout.nodes['00000000-0000-0000-0000-000000000010'] = {
      x: 220,
      y: 180,
      width: 280,
      height: 180,
    }

    await wrapper.setProps({ document: updatedDocument })

    expect((nameInput.element as HTMLInputElement).value).toBe('ClienteBorrador')
    expect(wrapper.text()).toContain('Hay cambios sin guardar')
  })

  it('sincroniza el inspector en una nueva revision cuando no hay borrador sucio', async () => {
    const document = documentWithClass()

    const wrapper = mount(InspectorPanel, {
      props: {
        document,
        selectedElementId: '00000000-0000-0000-0000-000000000010',
        busy: false,
      },
    })

    const updatedDocument = structuredClone(document)
    updatedDocument.revision = 2
    const updatedClass = updatedDocument.umlModel.elements[0]
    if (!updatedClass || updatedClass.kind !== 'class') {
      throw new Error('expected UML class fixture')
    }
    updatedClass.name = 'ClienteServidor'

    await wrapper.setProps({ document: updatedDocument })

    const nameInput = wrapper.find('input')
    expect((nameInput.element as HTMLInputElement).value).toBe('ClienteServidor')
  })

  it('edita multiplicidades y elimina una relación seleccionada', async () => {
    const document = documentWithRelationship('association')
    const relationshipId = '00000000-0000-0000-0000-000000000030'
    const wrapper = mount(InspectorPanel, {
      props: { document, selectedElementId: relationshipId, busy: false },
    })
    await setInputByLabel(wrapper, 'Origen mínimo', '2')
    await setInputByLabel(wrapper, 'Origen máximo', '2')
    await wrapper.findAll('button').find((item) => item.text().includes('Guardar relación'))?.trigger('click')

    expect(wrapper.emitted('execute')?.[0]?.[0]).toMatchObject({
      commandType: 'updateElement',
      element: { sourceMultiplicity: { lower: 2, upper: 2 } },
    })

    await wrapper.findAll('button').find((item) => item.text().includes('Eliminar'))?.trigger('click')
    expect(wrapper.emitted('execute')?.[1]?.[0]).toEqual({
      commandType: 'removeElement',
      elementId: relationshipId,
    })
  })

  it('no muestra multiplicidades para una generalization', () => {
    const document = documentWithRelationship('generalization')
    const wrapper = mount(InspectorPanel, {
      props: {
        document,
        selectedElementId: '00000000-0000-0000-0000-000000000030',
        busy: false,
      },
    })

    expect(wrapper.text()).toContain('Generalización')
    expect(wrapper.text()).not.toContain('Origen mínimo')
  })

  it('excluye la clase origen como destino de una generalization', () => {
    const document = documentWithRelationship('generalization')
    const wrapper = mount(InspectorPanel, {
      props: {
        document,
        selectedElementId: '00000000-0000-0000-0000-000000000030',
        busy: false,
      },
    })

    const selects = wrapper.findAllComponents({ name: 'VSelect' })
    expect(selects[1]?.props('items')).toEqual([
      expect.objectContaining({ id: '00000000-0000-0000-0000-000000000010' }),
    ])
  })
})
