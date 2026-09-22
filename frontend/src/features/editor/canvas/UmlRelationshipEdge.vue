<script setup lang="ts">
import { BaseEdge, type EdgeProps } from '@vue-flow/core'
import { computed } from 'vue'
import type { UmlRelationshipEdgeData } from './project-to-flow'

const props = defineProps<EdgeProps<UmlRelationshipEdgeData>>()

interface EdgeGeometry {
  path: string
  sourceLabel: { x: number; y: number }
  targetLabel: { x: number; y: number }
}

const geometry = computed<EdgeGeometry>(() => {
  const { sourceX, sourceY, targetX, targetY } = props
  const parallelOffset = props.data.parallelOffset * 28

  if (props.data.isSelfLoop) {
    const direction = props.data.parallelOffset < 0 ? -1 : 1
    const loopOffset = 76 + Math.abs(parallelOffset)
    return {
      path: [
        `M ${sourceX},${sourceY}`,
        `C ${sourceX + direction * loopOffset},${sourceY + 76}`,
        `${targetX + direction * loopOffset},${targetY - 76}`,
        `${targetX},${targetY}`,
      ].join(' '),
      sourceLabel: { x: sourceX + direction * (loopOffset + 12), y: sourceY + 28 },
      targetLabel: { x: targetX + direction * (loopOffset + 12), y: targetY - 20 },
    }
  }

  const deltaX = targetX - sourceX
  const deltaY = targetY - sourceY
  const distance = Math.hypot(deltaX, deltaY) || 1
  const perpendicularX = (-deltaY / distance) * parallelOffset
  const perpendicularY = (deltaX / distance) * parallelOffset

  return {
    path: [
      `M ${sourceX},${sourceY}`,
      `C ${sourceX + deltaX * 0.25 + perpendicularX},${sourceY + deltaY * 0.25 + perpendicularY}`,
      `${sourceX + deltaX * 0.75 + perpendicularX},${sourceY + deltaY * 0.75 + perpendicularY}`,
      `${targetX},${targetY}`,
    ].join(' '),
    sourceLabel: {
      x: sourceX + deltaX * 0.15 + perpendicularX,
      y: sourceY + deltaY * 0.15 + perpendicularY - 10,
    },
    targetLabel: {
      x: sourceX + deltaX * 0.85 + perpendicularX,
      y: sourceY + deltaY * 0.85 + perpendicularY - 10,
    },
  }
})
</script>

<template>
  <BaseEdge
    :id="id"
    :path="geometry.path"
    :marker-start="markerStart"
    :marker-end="markerEnd"
    :interaction-width="Math.max(interactionWidth ?? 20, 28)"
  />
  <text
    v-if="data.sourceMultiplicityLabel"
    :x="geometry.sourceLabel.x"
    :y="geometry.sourceLabel.y"
    class="uml-relationship-edge__multiplicity"
    data-testid="source-multiplicity"
    pointer-events="none"
    text-anchor="middle"
  >
    {{ data.sourceMultiplicityLabel }}
  </text>
  <text
    v-if="data.targetMultiplicityLabel"
    :x="geometry.targetLabel.x"
    :y="geometry.targetLabel.y"
    class="uml-relationship-edge__multiplicity"
    data-testid="target-multiplicity"
    pointer-events="none"
    text-anchor="middle"
  >
    {{ data.targetMultiplicityLabel }}
  </text>
</template>

<style scoped>
.uml-relationship-edge__multiplicity {
  fill: #dbe7f2;
  font-size: 12px;
  font-weight: 700;
  paint-order: stroke;
  stroke: #0c141d;
  stroke-width: 4px;
  stroke-linejoin: round;
}
</style>
