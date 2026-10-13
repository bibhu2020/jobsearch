<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

onMounted(async () => {
  const token = new URLSearchParams(window.location.hash.slice(1)).get('token')
  history.replaceState(null, '', window.location.pathname) // drop the token from the address bar
  if (!token) {
    router.replace({ path: '/login', query: { error: 'Sign-in did not complete — please try again' } })
    return
  }
  await auth.completeLogin(token)
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-900 text-sm text-slate-400">Signing you in…</div>
</template>
