<script setup lang="ts">
import { ref } from 'vue'
import { acceptInvitation } from './invitations-api'
import { useEditorStore } from './editor-store'
const emit = defineEmits<{ accepted: [] }>()
const store = useEditorStore(), token = ref(''), error = ref(''), busy = ref(false)
async function redeem() {
  if (busy.value || !token.value.trim()) return
  busy.value = true; error.value = ''
  try {
    const accepted = await acceptInvitation(token.value.trim()); token.value = ''
    try { await store.loadProjects(); await store.openProject(accepted.projectId); emit('accepted') }
    catch { error.value = 'La invitación se aceptó. Actualiza Proyectos para abrir el proyecto compartido.' }
  } catch (reason) { error.value = reason instanceof Error ? reason.message : 'No se pudo canjear.' }
  finally { busy.value = false }
}
</script>
<template>
  <form @submit.prevent="redeem">
    <p class="text-body-2 mb-3">Usa el código del propietario e ingresa con el mismo correo al que fue dirigido.</p>
    <v-textarea v-model="token" label="Código de invitación" maxlength="256" rows="3" :disabled="busy" />
    <v-alert v-if="error" type="error" density="compact" class="mb-3">{{ error }}</v-alert>
    <v-btn type="submit" color="primary" :loading="busy" :disabled="!token.trim()">Aceptar invitación</v-btn>
  </form>
</template>
