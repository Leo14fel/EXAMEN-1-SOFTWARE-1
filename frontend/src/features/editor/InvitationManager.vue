<script setup lang="ts">
import { ref, watch } from 'vue'
import { cancelInvitation, createInvitation, listInvitations, type Invitation } from './invitations-api'
import type { ProjectRole } from './types'
const props = defineProps<{ projectId: string }>()
const email = ref(''), role = ref<ProjectRole>('VIEWER'), hours = ref(24)
const invitations = ref<Invitation[]>([]), token = ref(''), error = ref(''), busy = ref(false), copyStatus = ref('')
async function load() {
  try { invitations.value = await listInvitations(props.projectId) }
  catch (reason) { error.value = reason instanceof Error ? reason.message : 'No se pudieron consultar invitaciones.' }
}
watch(() => props.projectId, () => { token.value = ''; error.value = ''; invitations.value = []; void load() }, { immediate: true })
async function create() {
  if (busy.value || !email.value.trim() || hours.value < 1 || hours.value > 168) return
  busy.value = true; error.value = ''; token.value = ''; copyStatus.value = ''
  try {
    const created = await createInvitation(props.projectId, email.value.trim(), role.value, Number(hours.value))
    token.value = created.token; invitations.value.push(created); email.value = ''
  } catch (reason) { error.value = reason instanceof Error ? reason.message : 'No se pudo crear la invitación.' }
  finally { busy.value = false }
}
async function cancel(id: string) {
  busy.value = true; error.value = ''
  try {
    await cancelInvitation(props.projectId, id)
    invitations.value = invitations.value.filter(item => item.id !== id)
    if (token.value.includes(`.${id}.`)) token.value = ''
  } catch (reason) { error.value = reason instanceof Error ? reason.message : 'No se pudo cancelar.' }
  finally { busy.value = false }
}
async function copy() {
  try { await navigator.clipboard.writeText(token.value); copyStatus.value = 'Código copiado.' }
  catch { copyStatus.value = 'Selecciona y copia el código manualmente.' }
}
</script>
<template>
  <section class="mt-5" aria-label="Invitaciones pendientes">
    <h3 class="text-subtitle-1 mb-2">Invitar con código</h3>
    <p class="text-caption text-medium-emphasis">Comparte el código con la persona indicada. Deberá registrarse o ingresar con ese correo y elegir «Canjear invitación». No se envían correos automáticamente.</p>
    <form class="mt-3" @submit.prevent="create">
      <v-text-field v-model="email" label="Correo de la persona invitada" type="email" :disabled="busy" />
      <div class="d-flex ga-2">
        <v-select v-model="role" label="Rol de la invitación" :items="['VIEWER', 'EDITOR']" :disabled="busy" />
        <v-text-field v-model.number="hours" label="Vigencia en horas" type="number" min="1" max="168" :disabled="busy" />
      </div>
      <v-btn type="submit" variant="tonal" color="primary" :loading="busy" :disabled="!email.trim()">Crear código de invitación</v-btn>
    </form>
    <v-alert v-if="error" type="error" density="compact" class="my-2">{{ error }}</v-alert>
    <div v-if="token" class="mt-3">
      <v-textarea :model-value="token" label="Código para compartir · guárdalo ahora" readonly rows="3" />
      <v-btn size="small" variant="text" @click="copy">Copiar código</v-btn><span role="status" class="text-caption">{{ copyStatus }}</span>
    </div>
    <v-list class="mt-3" bg-color="transparent">
      <v-list-item v-for="item in invitations" :key="item.id" :title="item.email" :subtitle="`${item.role} · vence ${new Date(item.expiresAt).toLocaleString()}`">
        <template #append><v-btn size="small" variant="text" :disabled="busy" @click="cancel(item.id)">Cancelar invitación</v-btn></template>
      </v-list-item>
      <v-list-item v-if="!invitations.length" title="Sin invitaciones pendientes" />
    </v-list>
  </section>
</template>
