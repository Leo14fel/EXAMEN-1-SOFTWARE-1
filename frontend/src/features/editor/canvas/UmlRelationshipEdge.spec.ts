import { mount } from '@vue/test-utils'
import { Position } from '@vue-flow/core'
import { describe, expect, it } from 'vitest'
import UmlRelationshipEdge from './UmlRelationshipEdge.vue'

function edgeProps(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    id: 'relationship-1',
    source: 'class-a',
    target: 'class-b',
    sourceNode: {},
    targetNode: {},
    type: 'umlRelationship',
    sourceX: 100,
    sourceY: 180,
    targetX: 300,
    targetY: 20,
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
    markerStart: '',
    markerEnd: '',
    selected: false,
    interactionWidth: 20,
    events: {},
    data: {
      kind: 'association',
      isSelfLoop: false,
      parallelOffset: 0,
      sourceMultiplicityLabel: '1',
      targetMultiplicityLabel: '0..*',
    },
    ...overrides,
  }
}

describe('UmlRelationshipEdge', () => {
  it('dibuja una relación normal con multiplicidades junto a sus extremos', () => {
    const wrapper = mount(UmlRelationshipEdge, { props: edgeProps() as never })

    expect(wrapper.find('.vue-flow__edge-path').attributes('d')).toContain('M 100,180')
    expect(wrapper.get('[data-testid="source-multiplicity"]').text()).toBe('1')
    expect(wrapper.get('[data-testid="target-multiplicity"]').text()).toBe('0..*')
    expect(wrapper.get('[data-testid="source-multiplicity"]').attributes('x')).not.toBe(
      wrapper.get('[data-testid="target-multiplicity"]').attributes('x'),
    )
  })

  it('dibuja un self-loop visible, seleccionable y con marker de composición', () => {
    const wrapper = mount(UmlRelationshipEdge, {
      props: edgeProps({
        source: 'folder',
        target: 'folder',
        sourceX: 140,
        sourceY: 220,
        targetX: 140,
        targetY: 40,
        markerStart: 'url(#uml-composition-diamond)',
        data: {
          kind: 'composition',
          isSelfLoop: true,
          parallelOffset: 0,
          sourceMultiplicityLabel: '1',
          targetMultiplicityLabel: '0..*',
        },
      }) as never,
    })

    const path = wrapper.find('.vue-flow__edge-path')
    expect(path.attributes('d')).toContain('C 216,296 216,-36 140,40')
    expect(path.attributes('marker-start')).toBe('url(#uml-composition-diamond)')
    expect(path.exists()).toBe(true)
    expect(wrapper.get('[data-testid="source-multiplicity"]').text()).toBe('1')
    expect(wrapper.get('[data-testid="target-multiplicity"]').text()).toBe('0..*')
  })

  it('no inventa multiplicidades para generalization y conserva el triángulo en target', () => {
    const wrapper = mount(UmlRelationshipEdge, {
      props: edgeProps({
        markerEnd: 'url(#uml-generalization-triangle)',
        data: { kind: 'generalization', isSelfLoop: false, parallelOffset: 0 },
      }) as never,
    })

    expect(wrapper.find('[data-testid="source-multiplicity"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="target-multiplicity"]').exists()).toBe(false)
    expect(wrapper.find('.vue-flow__edge-path').attributes('marker-end')).toBe(
      'url(#uml-generalization-triangle)',
    )
  })
})
