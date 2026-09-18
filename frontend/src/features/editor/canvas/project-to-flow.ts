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

function relationshipLabel(
  relationship:
    | (UmlRelationshipBase & {
        kind: 'association' | 'aggregation' | 'composition'
        sourceMultiplicity: UmlMultiplicity
        targetMultiplicity: UmlMultiplicity
      })
    | (UmlRelationshipBase & { kind: 'generalization' }),
): string {
  if (relationship.kind === 'generalization') {
    return 'generalización'
  }

  const kindLabel = {
    association: 'asociación',
    aggregation: 'agregación',
    composition: 'composición',
  }[relationship.kind]

  return `${kindLabel} · ${multiplicityLabel(relationship.sourceMultiplicity)} → ${multiplicityLabel(
    relationship.targetMultiplicity,
  )}`
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

  const edges: Edge<UmlRelationshipEdgeData>[] = document.umlModel.elements
    .filter((element) => element.kind !== 'class')
    .map((relationship) => ({
      id: relationship.id,
      source: relationship.sourceId,
      target: relationship.targetId,
      type: 'smoothstep',
      label: relationshipLabel(relationship),
      markerStart: markerStart(relationship.kind),
      markerEnd: markerEnd(relationship.kind),
      selectable: true,
      selected: selectedElementId === relationship.id,
      focusable: true,
      deletable: false,
      data: { kind: relationship.kind },
      class: `uml-flow-edge uml-flow-edge--${relationship.kind}`,
    }))

  return { nodes, edges }
}