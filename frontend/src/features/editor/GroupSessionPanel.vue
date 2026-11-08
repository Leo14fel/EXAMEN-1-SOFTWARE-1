<script setup lang="ts">
import { computed, ref } from 'vue'
import { useEditorStore } from './editor-store'
import { sessionActivityLabel } from './group-session-api'

const store = useEditorStore()
const draft = ref('')
let pendingId: string | null = null
let pendingText = ''
const canSend = computed(() => store.effectiveRole === 'EDITOR' && store.syncStatus === 'connected' && store.sessionReady)
const hasEarlier = computed(() => (store.sessionEvents[0]?.sequence ?? 1) > 1)
const emit = defineEmits<{ select: [id: string] }>()

async function send() {
  const text = draft.value.trim()
  if (!text || text.length > 4000 || !canSend.value || store.sessionSending) return
  if (!pendingId || pendingText !== text) {
    pendingId = crypto.randomUUID()
    pendingText = text
  }
  try {
    await store.sendGroupMessage(pendingId, text)
    draft.value = ''
    pendingId = null
  } catch {
    // Keep the draft and request ID: retry is idempotent after an ambiguous response.
  }
}
</script>

<template>
  <section class="group-session-panel" aria-label="Conversación y actividad del grupo">
    <header class="d-flex align-center flex-wrap ga-2 mb-3">
      <v-icon icon="mdi-forum-outline" color="primary" />
      <h2 class="text-subtitle-1">Conversación del proyecto</h2>
      <span class="text-caption text-medium-emphasis">{{ store.sessionParticipants.length }} participantes en el historial · visible para todo el grupo</span>
    </header>
    <v-btn v-if="hasEarlier" size="small" variant="text" :loading="store.sessionLoadingHistory" @click="store.loadEarlierSession()">Cargar anteriores</v-btn>
    <div class="session-history" role="log" aria-live="polite" aria-label="Historial grupal">
      <p v-if="store.sessionEvents.length === 0" class="text-body-2 text-medium-emphasis">
        {{ store.sessionReady ? 'Todavía no hay mensajes ni actividad registrada.' : 'Cargando el historial compartido…' }}
      </p>
      <article v-for="entry in store.sessionEvents" :key="entry.id" :class="['session-entry', `session-entry--${entry.kind}`]">
        <div class="text-caption text-medium-emphasis"><strong>{{ entry.actorName }}</strong> · {{ new Date(entry.createdAt).toLocaleString() }}</div>
        <p v-if="entry.kind === 'message'" class="session-message">{{ entry.text }}</p>
        <div v-else class="text-body-2">
          {{ sessionActivityLabel(entry) }} · revisión {{ entry.projectRevision }}
          <v-btn v-if="entry.elementId && store.document?.umlModel.elements.some(element => element.id === entry.elementId)"
            size="x-small" variant="text" @click="emit('select', entry.elementId!)">Ver elemento</v-btn>
        </div>
      </article>
    </div>
    <v-alert v-if="store.sessionError" type="error" density="compact" class="my-2">{{ store.sessionError }}</v-alert>
    <form class="mt-3" @submit.prevent="send">
      <v-textarea v-model="draft" label="Mensaje para todo el grupo" rows="2" auto-grow :maxlength="4000" counter="4000"
        :disabled="!canSend || store.sessionSending" hide-details="auto" />
      <div class="d-flex align-center justify-space-between flex-wrap ga-2 mt-2">
        <span class="text-caption text-medium-emphasis">{{ store.effectiveRole === 'VIEWER' ? 'Tu acceso permite consultar el historial.' : store.syncStatus !== 'connected' ? 'Reconectando la sesión…' : 'Los mensajes y las operaciones quedan registrados.' }}</span>
        <v-btn type="submit" color="primary" variant="tonal" :loading="store.sessionSending" :disabled="!canSend || !draft.trim()">Enviar al grupo</v-btn>
      </div>
    </form>
  </section>
</template>

<style scoped>
.group-session-panel { margin-top: 16px; padding: 18px; border-radius: 16px; border: 1px solid rgba(139, 124, 246, .24); background: #15212e; }
.session-history { max-height: 360px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
.session-entry { padding: 10px 12px; border-radius: 12px; overflow-wrap: anywhere; }
.session-entry--message { background: rgba(53, 208, 186, .08); border: 1px solid rgba(53, 208, 186, .15); }
.session-entry--activity { background: rgba(139, 124, 246, .06); }
.session-message { margin: 6px 0 0; white-space: pre-wrap; }
</style>
