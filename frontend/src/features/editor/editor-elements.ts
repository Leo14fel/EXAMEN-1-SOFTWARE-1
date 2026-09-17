import type {
  ProjectDocument,
  UmlAttribute,
  UmlClass,
  UmlMultiplicity,
  UmlOperation,
  UmlParameter,
  UmlRelationship,
  UmlVisibility,
} from './types'

export type RelationshipKind = UmlRelationship['kind']

export interface CreateRelationshipInput {
  kind: RelationshipKind
  sourceId: string
  targetId: string
  sourceMultiplicity?: UmlMultiplicity
  targetMultiplicity?: UmlMultiplicity
}

function newId(): string {
  return globalThis.crypto.randomUUID()
}

export function nextClassName(document: ProjectDocument): string {
  const used = new Set(
    document.umlModel.elements
      .filter((element): element is UmlClass => element.kind === 'class')
      .map((umlClass) => umlClass.name),
  )

  let index = 1
  while (used.has(`Clase${index}`)) index += 1
  return `Clase${index}`
}

export function createUmlClass(name: string): UmlClass {
  return {
    id: newId(),
    kind: 'class',
    name,
    visibility: 'public',
    attributes: [],
    operations: [],
  }
}

export function createAttribute(): UmlAttribute {
  return {
    id: newId(),
    kind: 'attribute',
    name: 'atributo',
    type: 'String',
    visibility: 'private',
  }
}

export function createOperation(): UmlOperation {
  return {
    id: newId(),
    kind: 'operation',
    name: 'operacion',
    visibility: 'public',
    parameters: [],
    returnType: null,
  }
}

export function createParameter(): UmlParameter {
  return {
    id: newId(),
    name: 'parametro',
    type: 'String',
  }
}

export function parseMultiplicity(lowerValue: string, upperValue: string): UmlMultiplicity | null {
  const normalizedLower = lowerValue.trim()
  const normalizedUpper = upperValue.trim()

  if (!/^\d+$/.test(normalizedLower)) return null
  const lower = Number(normalizedLower)

  if (normalizedUpper === '*') {
    return { lower, upper: '*' }
  }

  if (!/^\d+$/.test(normalizedUpper)) return null
  const upper = Number(normalizedUpper)
  if (upper < lower) return null

  return { lower, upper }
}

export function createRelationshipElement(input: CreateRelationshipInput): UmlRelationship {
  const id = newId()

  if (input.kind === 'generalization') {
    return {
      id,
      kind: 'generalization',
      sourceId: input.sourceId,
      targetId: input.targetId,
    }
  }

  if (!input.sourceMultiplicity || !input.targetMultiplicity) {
    throw new Error('Las multiplicidades son obligatorias para esta relacion')
  }

  return {
    id,
    kind: input.kind,
    sourceId: input.sourceId,
    targetId: input.targetId,
    sourceMultiplicity: input.sourceMultiplicity,
    targetMultiplicity: input.targetMultiplicity,
  }
}

export const visibilityOptions: Array<{ title: string; value: UmlVisibility }> = [
  { title: 'Publica (+)', value: 'public' },
  { title: 'Privada (-)', value: 'private' },
  { title: 'Protegida (#)', value: 'protected' },
  { title: 'Paquete (~)', value: 'package' },
]