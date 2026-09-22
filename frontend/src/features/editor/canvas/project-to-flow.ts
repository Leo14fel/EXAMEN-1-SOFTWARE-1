import type { Edge, Node } from '@vue-flow/core'
import type {
  ProjectDocument,
  UmlClass,
  UmlMultiplicity,
  UmlRelationshipBase,
} from '../types'

export interface UmlClassNodeData {
  umlClass: UmlClass
}

export interface UmlRelationshipEdgeData {
  kind: 'association' | 'aggregation' | 'composition' | 'generalization'
  isSelfLoop: boolean
  parallelOffset: number
  sourceMultiplicityLabel?: string
  targetMultiplicityLabel?: string
}

export interface ProjectFlowProjection {
  nodes: Node<UmlClassNodeData>[]
  edges: Edge<UmlRelationshipEdgeData>[]
}

export const DEFAULT_NODE_WIDTH = 280
export const DEFAULT_NODE_HEIGHT = 180

const GRID_COLUMNS = 3
const GRID_X_GAP = 340
const GRID_Y_GAP = 260
const GRID_ORIGIN_X = 60
const GRID_ORIGIN_Y = 60

function multiplicityLabel(value: UmlMultiplicity): string {
  if (typeof value.upper === 'number' && value.lower === value.upper) {
    return String(value.lower)
  }
  return `${value.lower}..${value.upper}`
}

function markerStart(kind: UmlRelationshipEdgeData['kind']): string | undefined {
  if (kind === 'aggregation') return 'url(#uml-aggregation-diamond)'
  if (kind === 'composition') return 'url(#uml-composition-diamond)'
  return undefined
}

function markerEnd(kind: UmlRelationshipEdgeData['kind']): string | undefined {
  return kind === 'generalization' ? 'url(#uml-generalization-triangle)' : undefined
}

export function projectDocumentToFlow(
  document: ProjectDocument,
  selectedElementId: string | null = null,
): ProjectFlowProjection {
  const classes = document.umlModel.elements.filter(
    (element): element is UmlClass => element.kind === 'class',
  )

  const nodes: Node<UmlClassNodeData>[] = classes.map((umlClass, index) => {
    const layout = document.diagramLayout.nodes[umlClass.id]
    const fallbackColumn = index % GRID_COLUMNS
    const fallbackRow = Math.floor(index / GRID_COLUMNS)

    return {
      id: umlClass.id,
      type: 'umlClass',
      position: {
        x: layout?.x ?? GRID_ORIGIN_X + fallbackColumn * GRID_X_GAP,
        y: layout?.y ?? GRID_ORIGIN_Y + fallbackRow * GRID_Y_GAP,
      },
      width: layout?.width ?? DEFAULT_NODE_WIDTH,
      height: layout?.height ?? DEFAULT_NODE_HEIGHT,
      draggable: true,
      connectable: false,
      selectable: true,
      selected: selectedElementId === umlClass.id,
      focusable: true,
      deletable: false,
      data: { umlClass },
      class: 'uml-flow-node',
    }
  })

  const relationships = document.umlModel.elements.filter(
    (element): element is Exclude<typeof element, UmlClass> => element.kind !== 'class',
  )
  const relationshipCounts = new Map<string, number>()
  for (const relationship of relationships) {
    const key = `${relationship.sourceId}:${relationship.targetId}`
    relationshipCounts.set(key, (relationshipCounts.get(key) ?? 0) + 1)
  }
  const relationshipIndexes = new Map<string, number>()

  const edges: Edge<UmlRelationshipEdgeData>[] = relationships.map((relationship) => {
    const key = `${relationship.sourceId}:${relationship.targetId}`
    const index = relationshipIndexes.get(key) ?? 0
    relationshipIndexes.set(key, index + 1)
    const count = relationshipCounts.get(key) ?? 1
    const isSelfLoop = relationship.sourceId === relationship.targetId

    return {
      id: relationship.id,
      source: relationship.sourceId,
      target: relationship.targetId,
      type: 'umlRelationship',
      markerStart: markerStart(relationship.kind),
      markerEnd: markerEnd(relationship.kind),
      selectable: true,
      selected: selectedElementId === relationship.id,
      focusable: true,
      deletable: false,
      data: {
        kind: relationship.kind,
        isSelfLoop,
        parallelOffset: index - (count - 1) / 2,
        ...(relationship.kind === 'generalization'
          ? {}
          : {
              sourceMultiplicityLabel: multiplicityLabel(relationship.sourceMultiplicity),
              targetMultiplicityLabel: multiplicityLabel(relationship.targetMultiplicity),
            }),
      },
      class: `uml-flow-edge uml-flow-edge--${relationship.kind}`,
    }
  })

  return { nodes, edges }
}
