import { describe, expect, it } from 'vitest'
import type { ProjectDocument } from './types'
import {
  createRelationshipElement,
  createUmlClass,
  nextClassName,
  parseMultiplicity,
} from './editor-elements'

function documentWithNames(names: string[]): ProjectDocument {
  return {
    id: '00000000-0000-0000-0000-000000000001',
    metadata: {},
    ownerId: '00000000-0000-0000-0000-000000000002',
    revision: 0,
    createdAt: '2026-09-15T12:00:00Z',
    updatedAt: '2026-09-15T12:00:00Z',
    umlModel: {
      elements: names.map((name, index) => ({
        ...createUmlClass(name),
        id: `00000000-0000-0000-0000-${String(index + 10).padStart(12, '0')}`,
      })),
    },
    diagramLayout: { nodes: {} },
  }
}

describe('editor-elements', () => {
  it('elige el siguiente nombre de clase sin duplicar los existentes', () => {
    expect(nextClassName(documentWithNames(['Clase1', 'Clase2']))).toBe('Clase3')
  })

  it('valida multiplicidades UML', () => {
    expect(parseMultiplicity('0', '*')).toEqual({ lower: 0, upper: '*' })
    expect(parseMultiplicity('1', '3')).toEqual({ lower: 1, upper: 3 })
    expect(parseMultiplicity('3', '1')).toBeNull()
    expect(parseMultiplicity('-1', '*')).toBeNull()
  })

  it('crea generalizacion sin multiplicidades', () => {
    const relationship = createRelationshipElement({
      kind: 'generalization',
      sourceId: 'child',
      targetId: 'parent',
    })

    expect(relationship).toMatchObject({
      kind: 'generalization',
      sourceId: 'child',
      targetId: 'parent',
    })
    expect('sourceMultiplicity' in relationship).toBe(false)
  })

  it('crea composicion con multiplicidades explicitas', () => {
    const relationship = createRelationshipElement({
      kind: 'composition',
      sourceId: 'whole',
      targetId: 'part',
      sourceMultiplicity: { lower: 1, upper: 1 },
      targetMultiplicity: { lower: 0, upper: '*' },
    })

    expect(relationship).toMatchObject({
      kind: 'composition',
      sourceMultiplicity: { lower: 1, upper: 1 },
      targetMultiplicity: { lower: 0, upper: '*' },
    })
  })
})