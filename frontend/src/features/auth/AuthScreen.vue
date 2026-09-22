<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from './auth-store'

const auth = useAuthStore()
const registerMode = ref(false)
const email = ref('')
const password = ref('')

async function submit(): Promise<void> {
  if (!email.value.trim() || password.value.length < 8 || auth.loading) return
  try {
    if (registerMode.value) await auth.signUp(email.value, password.value)
    else await auth.signIn(email.value, password.value)
  } catch {
    // The store exposes the server message in the form.
  }
}
</script>

<template>
  <v-app class="auth-app">
    <v-main class="auth-main">
      <v-card class="auth-card" elevation="10">
        <v-card-text class="pa-8">
          <div class="text-overline text-primary">EXAMEN SOFTWARE I</div>
          <h1 class="text-h5 font-weight-bold mb-2">{{ registerMode ? 'Crear cuenta' : 'Iniciar sesión' }}</h1>
          <p class="text-body-2 text-medium-emphasis mb-6">Accede a tus proyectos UML personales.</p>
          <v-form @submit.prevent="submit">
            <v-text-field v-model="email" label="Correo electrónico" type="email" autocomplete="email" />
            <v-text-field
              v-model="password"
              label="Contraseña"
              type="password"
              autocomplete="current-password"
              hint="Mínimo 8 caracteres"
            />
            <v-alert v-if="auth.error" type="error" density="compact" variant="tonal" class="mb-4">
              {{ auth.error }}
            </v-alert>
            <v-btn block color="primary" type="submit" :loading="auth.loading" :disabled="password.length < 8">
              {{ registerMode ? 'Registrarme' : 'Entrar' }}
            </v-btn>
          </v-form>
          <v-btn block variant="text" class="mt-3" :disabled="auth.loading" @click="registerMode = !registerMode">
            {{ registerMode ? 'Ya tengo cuenta' : 'Crear una cuenta' }}
          </v-btn>
        </v-card-text>
      </v-card>
    </v-main>
  </v-app>
</template>

<style scoped>
.auth-main { min-height: 100vh; display: grid; place-items: center; background: radial-gradient(circle at top left, rgba(53, 208, 186, .13), transparent 35%), #0f1720; }
.auth-card { width: min(440px, calc(100% - 32px)); background: #111c26; }
</style>
