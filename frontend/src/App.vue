<script setup lang="ts">
import { onMounted } from 'vue'
import AuthScreen from './features/auth/AuthScreen.vue'
import { useAuthStore } from './features/auth/auth-store'
import EditorWorkspace from './features/editor/EditorWorkspace.vue'

const auth = useAuthStore()
onMounted(() => void auth.bootstrap())
</script>

<template>
  <div v-if="!auth.resolved" class="app-loading">Restaurando sesión...</div>
  <AuthScreen v-else-if="!auth.isAuthenticated" />
  <EditorWorkspace v-else />
</template>

<style scoped>
.app-loading { min-height: 100vh; display: grid; place-items: center; background: #0f1720; color: #dbe7f2; }
</style>
