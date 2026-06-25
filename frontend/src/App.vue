<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import BottomNav from '@/components/BottomNav.vue'

const auth = useAuthStore()

onMounted(async () => {
  if (auth.isAuthenticated) await auth.fetchMode()
})
</script>

<template>
  <router-view />
  <BottomNav v-if="auth.isAuthenticated" />
</template>
