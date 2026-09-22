import { dagre } from 'd3-dag'
import type { DiagramNodeLayout, ProjectDocument, UmlClass } from '../types'

const DEFAULT_WIDTH = 280
const DEFAULT_HEIGHT = 180
const FALLBACK_COLUMNS = 3
const FALLBACK_X_GAP = 360
const FALLBACK_Y_GAP = 260

function classesOf(document: ProjectDocument): UmlClass[] {
  return document.umlModel.elements.filter(
    (element): element is UmlClass => element.kind === 'class',
  )
}

function fallbackLayout(document: ProjectDocument): Record<string, DiagramNodeLayout> {
  const result: Record<string, DiagramNodeLayout> = {}

  classesOf(document).forEach((umlClass, index) => {
    const current = document.diagramLayout.nodes[umlClass.id]
    result[umlClass.id] = {
      x: 60 + (index % FALLBACK_COLUMNS) * FALLBACK_X_GAP,
      y: 60 + Math.floor(index / FALLBACK_COLUMNS) * FALLBACK_Y_GAP,
      width: current?.width ?? DEFAULT_WIDTH,
      height: current?.height ?? DEFAULT_HEIGHT,
    }
  })

  return result
}

export function computeAutoLayout(
  document: ProjectDocument,
): Record<string, DiagramNodeLayout> {
  const classes = classesOf(document)
  if (classes.length === 0) return {}

  try {
    const graph = new dagre.graphlib.Graph()
    graph.setGraph({ rankdir: 'TB', nodesep: 80, ranksep: 110 })
    graph.setDefaultEdgeLabel(() => ({}))

    for (const umlClass of classes) {
      const current = document.diagramLayout.nodes[umlClass.id]
      graph.setNode(umlClass.id, {
        width: current?.width ?? DEFAULT_WIDTH,
        height: current?.height ?? DEFAULT_HEIGHT,
      })
    }

    for (const relationship of document.umlModel.elements) {
      if (relationship.kind !== 'class' && relationship.sourceId !== relationship.targetId) {
        graph.setEdge(relationship.sourceId, relationship.targetId)
      }
    }

    dagre.layout(graph)

    const result: Record<string, DiagramNodeLayout> = {}
    for (const umlClass of classes) {
      const current = document.diagramLayout.nodes[umlClass.id]
      const width = current?.width ?? DEFAULT_WIDTH
      const height = current?.height ?? DEFAULT_HEIGHT
      const position = graph.node(umlClass.id) as { x: number; y: number }

      if (!position || !Number.isFinite(position.x) || !Number.isFinite(position.y)) {
        return fallbackLayout(document)
      }

      result[umlClass.id] = {
        x: position.x - width / 2,
        y: position.y - height / 2,
        width,
        height,
      }
    }

    return result
  } catch {
    return fallbackLayout(document)
  }
}
