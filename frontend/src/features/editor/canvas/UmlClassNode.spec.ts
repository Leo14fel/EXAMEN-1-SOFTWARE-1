import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UmlClassNode from './UmlClassNode.vue'

describe('UmlClassNode', () => {
  it('muestra nombre, atributos y operaciones UML', () => {
    const wrapper = mount(UmlClassNode, {
      global: {
        stubs: {
          Handle: true,
        },
      },
      props: {
        selected: true,
        data: {
          umlClass: {
            id: '00000000-0000-0000-0000-000000000010',
            kind: 'class',
            name: 'Cliente',
            visibility: 'public',
            attributes: [
              {
                id: '00000000-0000-0000-0000-000000000011',
                kind: 'attribute',
                name: 'email',
                visibility: 'private',
                type: 'String',
              },
            ],
            operations: [
              {
                id: '00000000-0000-0000-0000-000000000012',
                kind: 'operation',
                name: 'buscar',
                visibility: 'public',
                parameters: [
                  {
                    id: '00000000-0000-0000-0000-000000000013',
                    name: 'id',
                    type: 'UUID',
                  },
                ],
                returnType: 'Cliente',
              },
            ],
          },
        },
      },
    })

    expect(wrapper.text()).toContain('Cliente')
    expect(wrapper.text()).toContain('- email: String')
    expect(wrapper.text()).toContain('+ buscar(id: UUID): Cliente')
    expect(wrapper.classes()).toContain('uml-class-node--selected')
  })
})