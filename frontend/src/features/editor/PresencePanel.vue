<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import type { Participant } from './editor-sync'
import { presenceColor } from './presence-ui'
import type { ProjectDocument } from './types'

const props = defineProps<{
  participants: Participant[]
  ownSessionId: string | null
  document: ProjectDocument
}>()
const emit = defineEmits<{ select: [id: string] }>()
const peers = computed(() => props.participants.filter((peer) => peer.sessionId !== props.ownSessionId))
const notice = ref('')
let previous = new Map<string, string>()
let timer: ReturnType<typeof setTimeout> | undefined
watch(peers, (current) => {
  const next = new Map(current.map((peer) => [peer.sessionId, peer.name]))
  const joined = [...next].filter(([id]) => !previous.has(id)).map(([, name]) => name)
  const left = [...previous].filter(([id]) => !next.has(id)).map(([, name]) => name)
  if (joined.length || left.length) {
    notice.value = [joined.length ? `${joined.join(', ')} se conectó` : '',
      left.length ? `${left.join(', ')} se desconectó` : ''].filter(Boolean).join(' · ')
    clearTimeout(timer)
    timer = setTimeout(() => { notice.value = '' }, 4000)
  }
  previous = next
})
onUnmounted(() => clearTimeout(timer))

function elementLabel(id: string | null): string {
  if (!id) return ''
  const element = props.document.umlModel.elements.find((element) => element.id === id)
  return element?.kind === 'class' ? element.name : element ? `Relación ${id.slice(0, 8)}` : ''
}
</script>

<template>
  <section class="presence-panel" aria-label="Participantes conectados">
    <div class="d-flex align-center flex-wrap ga-2">
      <v-icon icon="mdi-account-group-outline" color="primary" size="20" />
      <strong class="text-body-2">{{ participants.length }} sesiones conectadas</strong>
      <span v-if="peers.length === 0" class="text-caption text-medium-emphasis">Sin otros participantes conectados</span>
      <v-chip v-for="peer in peers" :key="peer.sessionId" size="small" variant="tonal"
        :color="presenceColor(peer.userId)" :title="`Última actividad: ${new Date(peer.lastActivity).toLocaleTimeString()}`"
        @click="peer.selectedElementId && emit('select', peer.selectedElementId)">
        <v-avatar start size="22" :color="presenceColor(peer.userId)">{{ peer.name.slice(0, 1).toUpperCase() }}</v-avatar>
        {{ peer.name }} · {{ peer.role === 'VIEWER' ? 'Observando' : 'Editor' }}
        <span v-if="peer.editingElementId"> · Editando {{ elementLabel(peer.editingElementId) }}</span>
        <span v-else-if="peer.selectedElementId"> · Seleccionó {{ elementLabel(peer.selectedElementId) }}</span>
      </v-chip>
    </div>
    <div class="text-caption text-primary mt-1" role="status" aria-live="polite">{{ notice }}</div>
  </section>
</template>

<style scoped>
.presence-panel { padding: 12px 16px; border: 1px solid rgba(53, 208, 186, .18); border-radius: 16px; background: #13212c; margin-bottom: 14px; }
</style>
