import { describe, expect, it } from 'vitest'
import type { ProjectDocument, UmlClass } from '../types'
import { computeAutoLayout } from './auto-layout'

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

describe('computeAutoLayout', () => {
  it('devuelve vacio para un documento sin clases', () => {
    const document: ProjectDocument = {
      id: '00000000-0000-0000-0000-000000000001',
      metadata: {},
      ownerId: '00000000-0000-0000-0000-000000000002',
      revision: 0,
      createdAt: '2026-09-15T12:00:00Z',
      updatedAt: '2026-09-15T12:00:00Z',
      umlModel: { elements: [] },
      diagramLayout: { nodes: {} },
    }

    expect(computeAutoLayout(document)).toEqual({})
  })

  it('calcula layouts positivos y distintos para clases relacionadas', () => {
    const customer = umlClass('00000000-0000-0000-0000-000000000010', 'Cliente')
    const order = umlClass('00000000-0000-0000-0000-000000000011', 'Pedido')
    const document: ProjectDocument = {
      id: '00000000-0000-0000-0000-000000000001',
      metadata: {},
      ownerId: '00000000-0000-0000-0000-000000000002',
      revision: 0,
      createdAt: '2026-09-15T12:00:00Z',
      updatedAt: '2026-09-15T12:00:00Z',
      umlModel: {
        elements: [
          customer,
          order,
          {
            id: '00000000-0000-0000-0000-000000000020',
            kind: 'association',
            sourceId: customer.id,
            targetId: order.id,
            sourceMultiplicity: { lower: 1, upper: 1 },
            targetMultiplicity: { lower: 0, upper: '*' },
          },
        ],
      },
      diagramLayout: { nodes: {} },
    }

    const result = computeAutoLayout(document)

    expect(Object.keys(result)).toHaveLength(2)
    expect(result[customer.id]).toMatchObject({ width: 280, height: 180 })
    expect(result[order.id]).toMatchObject({ width: 280, height: 180 })
    expect(result[customer.id]).not.toEqual(result[order.id])
    expect(result[customer.id].y).toBeLessThan(result[order.id].y)
  })

  it('ignora self-loops para el grafo de layout sin eliminarlos del documento', () => {
    const folder = umlClass('00000000-0000-0000-0000-000000000010', 'Carpeta')
    const document: ProjectDocument = {
      id: '00000000-0000-0000-0000-000000000001',
      metadata: {},
      ownerId: '00000000-0000-0000-0000-000000000002',
      revision: 0,
      createdAt: '2026-09-15T12:00:00Z',
      updatedAt: '2026-09-15T12:00:00Z',
      umlModel: {
        elements: [
          folder,
          {
            id: '00000000-0000-0000-0000-000000000020',
            kind: 'composition',
            sourceId: folder.id,
            targetId: folder.id,
            sourceMultiplicity: { lower: 0, upper: 1 },
            targetMultiplicity: { lower: 0, upper: '*' },
          },
        ],
      },
      diagramLayout: { nodes: {} },
    }

    const result = computeAutoLayout(document)

    expect(result[folder.id]).toMatchObject({ width: 280, height: 180 })
    expect(document.umlModel.elements).toHaveLength(2)
  })
})
