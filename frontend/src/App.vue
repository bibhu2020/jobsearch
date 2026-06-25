<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import BottomNav from '@/components/BottomNav.vue'

const auth = useAuthStore()
</script>

<template>
  <router-view />
  <BottomNav v-if="auth.isAuthenticated" />
</template>
