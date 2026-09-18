<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import type { UmlVisibility } from '../types'
import type { UmlClassNodeData } from './project-to-flow'

defineProps<{
  data: UmlClassNodeData
  selected?: boolean
}>()

const visibilitySymbols: Record<UmlVisibility, string> = {
  public: '+',
  private: '-',
  protected: '#',
  package: '~',
}

function visibilitySymbol(visibility: UmlVisibility): string {
  return visibilitySymbols[visibility]
}

function operationSignature(operation: UmlClassNodeData['umlClass']['operations'][number]): string {
  const parameters = operation.parameters
    .map((parameter) => `${parameter.name}: ${parameter.type}`)
    .join(', ')
  const returnType = operation.returnType ? `: ${operation.returnType}` : ''
  return `${operation.name}(${parameters})${returnType}`
}
</script>

<template>
  <article class="uml-class-node" :class="{ 'uml-class-node--selected': selected }">
    <Handle type="target" :position="Position.Top" class="uml-handle" />
    <Handle type="source" :position="Position.Bottom" class="uml-handle" />

    <header class="uml-class-node__header">
      <span class="uml-class-node__stereotype">«class»</span>
      <strong>{{ data.umlClass.name }}</strong>
    </header>

    <section class="uml-class-node__section">
      <div class="uml-class-node__section-title">Atributos</div>
      <div v-if="data.umlClass.attributes.length === 0" class="uml-class-node__empty">
        Sin atributos
      </div>
      <div
        v-for="attribute in data.umlClass.attributes"
        :key="attribute.id"
        class="uml-class-node__member"
      >
        {{ visibilitySymbol(attribute.visibility) }} {{ attribute.name }}: {{ attribute.type }}
      </div>
    </section>

    <section class="uml-class-node__section">
      <div class="uml-class-node__section-title">Operaciones</div>
      <div v-if="data.umlClass.operations.length === 0" class="uml-class-node__empty">
        Sin operaciones
      </div>
      <div
        v-for="operation in data.umlClass.operations"
        :key="operation.id"
        class="uml-class-node__member"
      >
        {{ visibilitySymbol(operation.visibility) }} {{ operationSignature(operation) }}
      </div>
    </section>
  </article>
</template>

<style scoped>
.uml-class-node {
  width: 100%;
  min-width: 240px;
  min-height: 150px;
  overflow: visible;
  border: 1px solid rgba(148, 163, 184, 0.4);
  border-radius: 12px;
  background: #17222d;
  color: #e5edf5;
  box-shadow: 0 14px 32px rgba(2, 6, 23, 0.28);
  transition:
    border-color 120ms ease,
    box-shadow 120ms ease;
}

.uml-class-node--selected {
  border-color: #35d0ba;
  box-shadow:
    0 0 0 2px rgba(53, 208, 186, 0.22),
    0 14px 34px rgba(2, 6, 23, 0.35);
}

.uml-class-node__header {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 12px 12px 0 0;
  background: rgba(53, 208, 186, 0.08);
  text-align: center;
}

.uml-class-node__stereotype {
  color: #8fa4b8;
  font-size: 10px;
  letter-spacing: 0.06em;
}

.uml-class-node__section {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
}

.uml-class-node__section:last-child {
  border-bottom: 0;
}

.uml-class-node__section-title {
  margin-bottom: 6px;
  color: #8fa4b8;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.uml-class-node__member {
  padding: 2px 0;
  font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
  font-size: 11px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.uml-class-node__empty {
  color: #718399;
  font-size: 11px;
  font-style: italic;
}

:deep(.uml-handle) {
  width: 9px;
  height: 9px;
  border: 2px solid #0c141d;
  background: #35d0ba;
  opacity: 0;
  pointer-events: none;
}
</style>