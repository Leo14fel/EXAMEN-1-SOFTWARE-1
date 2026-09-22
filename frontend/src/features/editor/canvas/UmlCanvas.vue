<script setup lang="ts">
import { computed } from 'vue'
import type { Node } from '@vue-flow/core'
import { useVueFlow, VueFlow } from '@vue-flow/core'
import type { DiagramNodeLayout, ProjectDocument } from '../types'
import UmlClassNode from './UmlClassNode.vue'
import UmlRelationshipEdge from './UmlRelationshipEdge.vue'
import {
  DEFAULT_NODE_HEIGHT,
  DEFAULT_NODE_WIDTH,
  projectDocumentToFlow,
  type UmlClassNodeData,
} from './project-to-flow'

const props = defineProps<{
  document: ProjectDocument
  selectedElementId: string | null
  busy?: boolean
}>()

const emit = defineEmits<{
  select: [elementId: string | null]
  moveNode: [payload: { elementId: string; layout: DiagramNodeLayout }]
}>()

const { fitView, zoomIn, zoomOut } = useVueFlow()

const projection = computed(() =>
  projectDocumentToFlow(props.document, props.selectedElementId),
)
const isEmpty = computed(() => projection.value.nodes.length === 0)

function selectNode(event: { node: { id: string } }): void {
  emit('select', event.node.id)
}

function selectEdge(event: { edge: { id: string } }): void {
  emit('select', event.edge.id)
}

function clearSelection(): void {
  emit('select', null)
}

function handleNodeDragStop(event: { node: Node<UmlClassNodeData> }): void {
  if (props.busy) return

  const current = props.document.diagramLayout.nodes[event.node.id]
  emit('moveNode', {
    elementId: event.node.id,
    layout: {
      x: event.node.position.x,
      y: event.node.position.y,
      width: current?.width ?? DEFAULT_NODE_WIDTH,
      height: current?.height ?? DEFAULT_NODE_HEIGHT,
    },
  })
}

function handleZoomIn(): void {
  void zoomIn()
}

function handleZoomOut(): void {
  void zoomOut()
}

function fitContent(): void {
  void fitView({ padding: 0.2, duration: 250 })
}

defineExpose({ fitContent })
</script>

<template>
  <section class="uml-canvas-shell">
    <svg class="uml-marker-defs" aria-hidden="true">
      <defs>
        <marker
          id="uml-aggregation-diamond"
          viewBox="0 0 12 12"
          ref-x="10"
          ref-y="6"
          marker-width="12"
          marker-height="12"
          orient="auto-start-reverse"
        >
          <path d="M 1 6 L 6 1 L 11 6 L 6 11 Z" fill="#0c141d" stroke="#60a5fa" stroke-width="1.3" />
        </marker>
        <marker
          id="uml-composition-diamond"
          viewBox="0 0 12 12"
          ref-x="10"
          ref-y="6"
          marker-width="12"
          marker-height="12"
          orient="auto-start-reverse"
        >
          <path d="M 1 6 L 6 1 L 11 6 L 6 11 Z" fill="#35d0ba" stroke="#35d0ba" stroke-width="1.3" />
        </marker>
        <marker
          id="uml-generalization-triangle"
          viewBox="0 0 14 14"
          ref-x="12"
          ref-y="7"
          marker-width="14"
          marker-height="14"
          orient="auto"
        >
          <path d="M 1 1 L 13 7 L 1 13 Z" fill="#0c141d" stroke="#8b7cf6" stroke-width="1.3" />
        </marker>
      </defs>
    </svg>

    <div class="uml-canvas-meta">
      <span>{{ projection.nodes.length }} clases</span>
      <span>{{ projection.edges.length }} relaciones</span>
      <span v-if="selectedElementId">Seleccionado: {{ selectedElementId.slice(0, 8) }}</span>
      <span v-else>Sin selección</span>
    </div>

    <VueFlow
      :nodes="projection.nodes"
      :edges="projection.edges"
      :nodes-draggable="!busy"
      :nodes-connectable="false"
      :elements-selectable="true"
      :min-zoom="0.2"
      :max-zoom="2"
      fit-view-on-init
      class="uml-canvas"
      @node-click="selectNode"
      @edge-click="selectEdge"
      @node-drag-stop="handleNodeDragStop"
      @pane-click="clearSelection"
    >
      <template #node-umlClass="nodeProps">
        <UmlClassNode :data="nodeProps.data" :selected="nodeProps.selected" />
      </template>
      <template #edge-umlRelationship="edgeProps">
        <UmlRelationshipEdge v-bind="edgeProps" />
      </template>
    </VueFlow>

    <div class="uml-canvas-controls" aria-label="Controles del canvas">
      <button type="button" title="Acercar" aria-label="Acercar" @click="handleZoomIn">+</button>
      <button type="button" title="Alejar" aria-label="Alejar" @click="handleZoomOut">−</button>
      <button type="button" title="Ajustar contenido" aria-label="Ajustar contenido" @click="fitContent">
        □
      </button>
    </div>

    <div v-if="isEmpty" class="uml-canvas-empty">
      <v-icon icon="mdi-vector-square" size="48" class="mb-3" />
      <div class="text-h6 mb-2">Documento UML vacío</div>
      <p class="text-body-2 text-medium-emphasis ma-0">
        Usa “Nueva clase” para comenzar el modelo. Toda edición se ejecuta mediante el Command Bus.
      </p>
    </div>
  </section>
</template>

<style scoped>
.uml-canvas-shell {
  position: relative;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 16px;
  background: #0c141d;
}

.uml-marker-defs {
  position: absolute;
  width: 0;
  height: 0;
}

.uml-canvas {
  width: 100%;
  height: 100%;
  min-height: 620px;
  background-color: #0c141d;
  background-image: radial-gradient(circle, rgba(99, 116, 136, 0.38) 1px, transparent 1px);
  background-size: 22px 22px;
}

.uml-canvas-meta {
  position: absolute;
  z-index: 5;
  top: 14px;
  left: 14px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  pointer-events: none;
}

.uml-canvas-meta span {
  padding: 5px 9px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 999px;
  background: rgba(12, 20, 29, 0.88);
  color: #9db0c3;
  font-size: 11px;
  backdrop-filter: blur(8px);
}

.uml-canvas-controls {
  position: absolute;
  z-index: 6;
  right: 14px;
  bottom: 14px;
  display: flex;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 10px;
  background: #17222d;
  box-shadow: 0 10px 26px rgba(2, 6, 23, 0.26);
}

.uml-canvas-controls button {
  width: 38px;
  height: 38px;
  border: 0;
  border-right: 1px solid rgba(148, 163, 184, 0.18);
  background: transparent;
  color: #dbe7f2;
  font-size: 18px;
  cursor: pointer;
}

.uml-canvas-controls button:last-child {
  border-right: 0;
}

.uml-canvas-controls button:hover,
.uml-canvas-controls button:focus-visible {
  background: rgba(53, 208, 186, 0.12);
  outline: none;
}

.uml-canvas-empty {
  position: absolute;
  z-index: 4;
  top: 50%;
  left: 50%;
  width: min(420px, calc(100% - 48px));
  padding: 28px;
  transform: translate(-50%, -50%);
  border: 1px dashed rgba(148, 163, 184, 0.3);
  border-radius: 16px;
  background: rgba(15, 23, 32, 0.92);
  text-align: center;
  pointer-events: none;
}

:deep(.vue-flow__edge-textbg) {
  fill: #17222d;
}

:deep(.vue-flow__edge-text) {
  fill: #c6d3df;
  font-size: 11px;
}

:deep(.vue-flow__edge.selected .vue-flow__edge-path) {
  stroke-width: 3;
}

:deep(.uml-flow-edge--generalization .vue-flow__edge-path) {
  stroke: #8b7cf6;
}

:deep(.uml-flow-edge--composition .vue-flow__edge-path) {
  stroke: #35d0ba;
  stroke-width: 2;
}

:deep(.uml-flow-edge--aggregation .vue-flow__edge-path) {
  stroke: #60a5fa;
}

:deep(.uml-flow-edge--association .vue-flow__edge-path) {
  stroke: #94a3b8;
}
</style>
