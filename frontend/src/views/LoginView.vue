<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
  } catch (e: any) {
    error.value = e.response?.data?.message || 'Invalid credentials'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-slate-100">
    <div class="bg-white rounded-2xl shadow-xl p-10 w-full max-w-md">
      <div class="mb-8 text-center">
        <div class="text-3xl font-bold text-indigo-600 tracking-tight">🎯 JobQuest AI</div>
        <p class="text-gray-500 mt-2">Sign in to your job tracker</p>
      </div>
      <form @submit.prevent="submit" class="space-y-5">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input v-model="email" type="email" required autocomplete="email"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input v-model="password" type="password" required autocomplete="current-password"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500" />
        </div>
        <p v-if="error" class="text-red-600 text-sm">{{ error }}</p>
        <button type="submit" :disabled="loading"
          class="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold transition disabled:opacity-50">
          {{ loading ? 'Signing in…' : 'Sign In' }}
        </button>
      </form>
      <p class="mt-6 text-center text-sm text-gray-500">
        No account?
        <router-link to="/register" class="text-indigo-600 font-medium hover:underline">Create one</router-link>
      </p>
    </div>
  </div>
</template>
