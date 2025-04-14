<!-- frontend/src/components/LoginForm.vue -->
<template>
  <form @submit.prevent="handleSubmit">
    <div class="input-group">
      <label for="email">E-mail</label>
      <input
        v-model="email"
        type="email"
        required
        autocomplete="username"
        @input="validateEmail"
      />
      <span class="error">{{ emailError }}</span>
    </div>

    <div class="input-group">
      <label for="password">Senha</label>
      <input
        v-model="password"
        type="password"
        required
        autocomplete="current-password"
        minlength="8"
      />
      <span class="error">{{ passwordError }}</span>
    </div>

    <button type="submit" :disabled="loading">
      {{ loading ? 'Carregando...' : 'Entrar' }}
    </button>

    <div v-if="error" class="error-message">{{ error }}</div>
  </form>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const validateEmail = () => {
  // Validação simples de e-mail
}

const handleSubmit = async () => {
  try {
    loading.value = true
    await authStore.login(email.value, password.value)
    // Redirecionamento após login
  } catch (err) {
    error.value = 'Credenciais inválidas'
  } finally {
    loading.value = false
  }
}
</script>