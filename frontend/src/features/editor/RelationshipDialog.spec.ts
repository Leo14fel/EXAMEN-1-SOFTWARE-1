import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import RelationshipDialog from './RelationshipDialog.vue'
import type { UmlClass } from './types'

const employee: UmlClass = {
  id: '00000000-0000-0000-0000-000000000010',
  kind: 'class',
  name: 'Empleado',
  visibility: 'public',
  attributes: [],
  operations: [],
}

function createButton(wrapper: ReturnType<typeof mount>): HTMLButtonElement {
  const button = wrapper.findAll('button').find((item) => item.text().includes('Crear relación'))
  if (!button) throw new Error('expected create relationship button')
  return button.element as HTMLButtonElement
}

function mountDialog() {
  return mount(RelationshipDialog, {
    props: { modelValue: false, classes: [employee], busy: false },
    global: {
      stubs: {
        VDialog: { template: '<div><slot /></div>' },
      },
    },
  })
}

describe('RelationshipDialog', () => {
  it.each(['association', 'aggregation', 'composition'] as const)(
    'permite una autorrelación de %s',
    async (kind) => {
      const wrapper = mountDialog()
      await wrapper.setProps({ modelValue: true })
      const [kindSelect] = wrapper.findAllComponents({ name: 'VSelect' })
      if (!kindSelect) throw new Error('expected relationship kind select')

      await kindSelect.vm.$emit('update:modelValue', kind)
      await wrapper.findAll('button').find((item) => item.text().includes('Crear relación'))?.trigger('click')

      const emitted = wrapper.emitted('create')
      expect(emitted?.[0]?.[0]).toMatchObject({
        kind,
        sourceId: employee.id,
        targetId: employee.id,
      })
    },
  )

  it('impide una autoherencia y oculta multiplicidades para generalization', async () => {
    const wrapper = mountDialog()
    await wrapper.setProps({ modelValue: true })
    const [kindSelect] = wrapper.findAllComponents({ name: 'VSelect' })
    if (!kindSelect) throw new Error('expected relationship kind select')

    await kindSelect.vm.$emit('update:modelValue', 'generalization')

    expect(wrapper.text()).not.toContain('Origen mínimo')
    const selects = wrapper.findAllComponents({ name: 'VSelect' })
    expect(selects[2]?.props('items')).toEqual([])
    expect(createButton(wrapper).disabled).toBe(true)
  })
})
