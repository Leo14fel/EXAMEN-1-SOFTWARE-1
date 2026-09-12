<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getHealth } from './services/api'

const backendStatus = ref<'checking' | 'ok' | 'offline'>('checking')

const backendLabel = computed(() => {
  if (backendStatus.value === 'checking') return 'Backend: comprobando...'
  if (backendStatus.value === 'ok') return 'Backend: conectado'
  return 'Backend: sin conexion'
})

onMounted(async () => {
  try {
    const health = await getHealth()
    backendStatus.value = health.status === 'ok' ? 'ok' : 'offline'
  } catch {
    backendStatus.value = 'offline'
  }
})
</script>

<template>
  <v-app>
    <v-main>
      <v-container class="foundation-shell d-flex align-center justify-center">
        <v-card class="foundation-card pa-8" elevation="8" rounded="xl" max-width="760" width="100%">
          <div class="text-overline text-primary mb-2">EXAMEN SOFTWARE I</div>
          <h1 class="text-h3 font-weight-bold mb-4">Fundación del proyecto lista</h1>
          <p class="text-body-1 text-medium-emphasis mb-6">
            Esta pantalla solo confirma que Vue, Vuetify y la configuración base funcionan. El dominio UML se
            implementará caso por caso.
          </p>

          <v-divider class="mb-6" />

          <div class="d-flex ga-3 flex-wrap">
            <v-chip color="primary" variant="tonal">Vue web</v-chip>
            <v-chip color="secondary" variant="tonal">FastAPI</v-chip>
            <v-chip color="primary" variant="tonal">PostgreSQL</v-chip>
            <v-chip :color="backendStatus === 'ok' ? 'success' : 'warning'" variant="tonal">
              {{ backendLabel }}
            </v-chip>
          </div>
        </v-card>
      </v-container>
    </v-main>
  </v-app>
</template>
