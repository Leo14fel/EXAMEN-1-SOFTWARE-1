<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useEditorStore } from './editor-store'
import { AiApiError, evaluateAi, getAiResult, getAiStatus } from './ai-api'
import type { AiRequest, AiResult, AiStatus } from './ai-api'
import type { SessionEvent } from './group-session-api'

const store = useEditorStore()
const projectId = store.projectId
const status = ref<AiStatus | null>(null)
const loading = ref(false), busy = ref(false), error = ref(''), draft = ref('')
const pending = ref<AiRequest | null>(null)
const lastResult = ref<SessionEvent | null>(null)
const stale = computed(() => lastResult.value?.baseRevision !== undefined
  && lastResult.value.baseRevision !== store.document?.revision)
let alive = true
const canSend = computed(() => status.value?.configured && store.effectiveRole === 'EDITOR'
  && store.syncStatus === 'connected' && store.sessionReady && !!store.document
  && !busy.value && !pending.value && !!draft.value.trim() && draft.value.trim().length <= 2000)
function current() { return alive && store.projectId === projectId }
async function loadStatus() {
  if (!projectId) return
  loading.value = true
  try { const value = await getAiStatus(projectId); if (current()) { status.value = value; error.value = '' } }
  catch { if (current()) error.value = 'La evaluación de IA no está disponible por ahora.' }
  finally { if (current()) loading.value = false }
}
function completed(result: SessionEvent) {
  error.value = ''
  lastResult.value = result
  if (result.status === 'proposed') draft.value = ''
  pending.value = null
}
function receive(value: AiResult) {
  if (!current() || !projectId) return
  const events = [value.request, ...(value.result ? [value.result] : [])]
  store.applySessionPage({ projectId, events, participants: store.sessionParticipants.map(peer => ({ ...peer })),
    cursor: events.at(-1)?.sequence ?? 0, version: events.at(-1)?.sequence ?? 0,
    hasEarlier: false, hasMore: false })
  if (value.result) completed(value.result)
}
async function submit() {
  if (!canSend.value || !projectId || !store.document) return
  const body = { id: crypto.randomUUID(), baseRevision: store.document.revision, text: draft.value.trim() }
  pending.value = body; busy.value = true; error.value = ''; lastResult.value = null
  try { receive(await evaluateAi(projectId, body)) }
  catch (reason) {
    if (!current() || pending.value?.id !== body.id) return
    error.value = reason instanceof Error ? reason.message : 'No se pudo confirmar la solicitud.'
    if (reason instanceof AiApiError && ((reason.status >= 400 && reason.status < 500)
      || reason.code === 'AI_NOT_CONFIGURED')) {
      pending.value = null
      if (reason.code === 'AI_NOT_CONFIGURED') status.value = null
    }
  } finally { if (current()) busy.value = false }
}
async function checkResult() {
  if (!projectId || !pending.value || busy.value) return
  busy.value = true; error.value = ''
  try { receive(await getAiResult(projectId, pending.value.id)) }
  catch (reason) {
    if (!current()) return
    if (reason instanceof AiApiError && reason.code === 'AI_REQUEST_NOT_FOUND') {
      pending.value = null
      error.value = 'La solicitud no llegó a registrarse. Puedes enviarla nuevamente.'
    } else error.value = reason instanceof Error ? reason.message : 'No se pudo consultar el resultado.'
  } finally { if (current()) busy.value = false }
}
watch(() => store.sessionEvents, (events) => {
  const result = pending.value && events.find(event => event.kind === 'aiResult' && event.requestId === pending.value?.id)
  if (result && current()) completed(result)
})
onMounted(loadStatus)
onBeforeUnmount(() => { alive = false })
</script>

<template>
  <section class="ai-request-panel" aria-label="Evaluación grupal con IA">
    <header class="d-flex align-center flex-wrap ga-2 mb-2">
      <v-icon icon="mdi-creation-outline" color="secondary" />
      <h2 class="text-subtitle-1">Evaluar una solicitud con IA</h2>
      <v-btn size="small" variant="text" :loading="loading" :disabled="busy" @click="loadStatus">Comprobar disponibilidad</v-btn>
    </header>
    <p class="text-body-2 mb-3">La solicitud y su respuesta serán visibles para todo el grupo. Esta evaluación propone cambios; no modifica el diagrama.</p>
    <v-alert v-if="status && !status.configured" type="info" density="compact" class="mb-3">La IA está pendiente de configuración. Todavía no se ha guardado una clave del proveedor en el servidor.</v-alert>
    <p v-if="store.effectiveRole === 'VIEWER'" class="text-body-2 mb-2">Puedes consultar las solicitudes y respuestas en la conversación del grupo.</p>
    <v-alert v-if="error" type="warning" density="compact" class="mb-3">{{ error }}</v-alert>
    <form @submit.prevent="submit">
      <v-textarea v-model="draft" label="Solicitud para evaluar" rows="2" :maxlength="2000" counter="2000" hide-details="auto"
        :disabled="!status?.configured || store.effectiveRole !== 'EDITOR' || busy || !!pending" />
      <div class="d-flex align-center flex-wrap ga-2 mt-2">
        <v-btn type="submit" color="secondary" variant="tonal" :disabled="!canSend" :loading="busy">Evaluar para el grupo</v-btn>
        <v-btn v-if="pending" variant="text" :disabled="busy" @click="checkResult">Consultar resultado</v-btn>
        <span v-if="pending" class="text-caption">Esperando confirmación. La consulta del resultado no vuelve a llamar a la IA.</span>
      </div>
    </form>
    <v-alert v-if="lastResult" :type="lastResult.status === 'proposed' && !stale ? 'success' : 'info'" density="compact" class="mt-3">
      {{ lastResult.text }} La respuesta quedó registrada en la conversación del grupo.
      <p v-if="stale" class="mt-1">El diagrama cambió desde esta evaluación. Solicita una nueva revisión.</p>
    </v-alert>
  </section>
</template>

<style scoped>
.ai-request-panel { margin-top: 16px; padding: 18px; border-radius: 16px; background: #15212e; border: 1px solid rgba(139, 124, 246, .24); }
</style>
