import { describe, expect, it } from 'vitest'
import type {
  ProjectDocument,
  UmlAssociation,
  UmlClass,
  UmlComposition,
  UmlGeneralization,
} from '../types'
import { projectDocumentToFlow } from './project-to-flow'

function umlClass(id: string, name: string): UmlClass {
  return {
    id,
    kind: 'class',
    name,
    visibility: 'public',
    attributes: [],
    operations: [],
  }
}

function baseDocument(elements: ProjectDocument['umlModel']['elements']): ProjectDocument {
  return {
    id: '00000000-0000-0000-0000-000000000001',
    metadata: {},
    ownerId: '00000000-0000-0000-0000-000000000002',
    revision: 0,
    createdAt: '2026-09-15T12:00:00Z',
    updatedAt: '2026-09-15T12:00:00Z',
    umlModel: { elements },
    diagramLayout: { nodes: {} },
  }
}

describe('projectDocumentToFlow', () => {
  it('proyecta clases editables usando DiagramLayout cuando existe', () => {
    const customer = umlClass('00000000-0000-0000-0000-000000000010', 'Cliente')
    const document = baseDocument([customer])
    document.diagramLayout.nodes[customer.id] = {
      x: 120,
      y: 240,
      width: 320,
      height: 210,
    }

    const projection = projectDocumentToFlow(document, customer.id)

    expect(projection.nodes).toHaveLength(1)
    expect(projection.nodes[0]).toMatchObject({
      id: customer.id,
      type: 'umlClass',
      position: { x: 120, y: 240 },
      width: 320,
      height: 210,
      draggable: true,
      connectable: false,
      selected: true,
    })
  })

  it('asigna posiciones deterministas cuando una clase aun no tiene layout', () => {
    const first = umlClass('00000000-0000-0000-0000-000000000010', 'Cliente')
    const second = umlClass('00000000-0000-0000-0000-000000000011', 'Pedido')

    const firstProjection = projectDocumentToFlow(baseDocument([first, second]))
    const secondProjection = projectDocumentToFlow(baseDocument([first, second]))

    expect(firstProjection.nodes.map((node) => node.position)).toEqual(
      secondProjection.nodes.map((node) => node.position),
    )
    expect(firstProjection.nodes[0].position).not.toEqual(firstProjection.nodes[1].position)
  })

  it('proyecta association y composition con multiplicidades y marcador UML', () => {
    const customer = umlClass('00000000-0000-0000-0000-000000000010', 'Cliente')
    const order = umlClass('00000000-0000-0000-0000-000000000011', 'Pedido')
    const association: UmlAssociation = {
      id: '00000000-0000-0000-0000-000000000020',
      kind: 'association',
      sourceId: customer.id,
      targetId: order.id,
      sourceMultiplicity: { lower: 1, upper: 1 },
      targetMultiplicity: { lower: 0, upper: '*' },
    }
    const composition: UmlComposition = {
      id: '00000000-0000-0000-0000-000000000021',
      kind: 'composition',
      sourceId: customer.id,
      targetId: order.id,
      sourceMultiplicity: { lower: 1, upper: 1 },
      targetMultiplicity: { lower: 1, upper: '*' },
    }

    const projection = projectDocumentToFlow(
      baseDocument([customer, order, association, composition]),
    )

    expect(projection.edges[0].label).toBe('asociación · 1 → 0..*')
    expect(projection.edges[1]).toMatchObject({
      label: 'composición · 1 → 1..*',
      markerStart: 'url(#uml-composition-diamond)',
    })
  })

  it('generalization apunta desde hija hacia padre con triangulo en target', () => {
    const child = umlClass('00000000-0000-0000-0000-000000000010', 'Administrador')
    const parent = umlClass('00000000-0000-0000-0000-000000000011', 'Usuario')
    const generalization: UmlGeneralization = {
      id: '00000000-0000-0000-0000-000000000030',
      kind: 'generalization',
      sourceId: child.id,
      targetId: parent.id,
    }

    const projection = projectDocumentToFlow(baseDocument([child, parent, generalization]))

    expect(projection.edges).toEqual([
      expect.objectContaining({
        id: generalization.id,
        source: child.id,
        target: parent.id,
        label: 'generalización',
        markerEnd: 'url(#uml-generalization-triangle)',
      }),
    ])
  })
})