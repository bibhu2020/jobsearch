<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
</script>

<template>
  <nav class="bg-white border-b border-gray-200 px-4 py-3">
    <div class="flex items-center justify-between">
      <router-link to="/pipeline" class="text-lg font-bold text-indigo-600 tracking-tight">
        🎯 JobQuest AI
      </router-link>

      <!-- Desktop nav -->
      <div class="hidden sm:flex items-center gap-1">
        <router-link to="/pipeline"
          class="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition"
          active-class="bg-indigo-50 text-indigo-700">Pipeline</router-link>
        <router-link to="/suggestions"
          class="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition"
          active-class="bg-indigo-50 text-indigo-700">Suggestions</router-link>
        <router-link to="/profile"
          class="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition"
          active-class="bg-indigo-50 text-indigo-700">Profile</router-link>
      </div>

      <button @click="auth.logout()" class="hidden sm:block text-sm text-gray-500 hover:text-gray-800 transition">
        Sign out
      </button>
    </div>
  </nav>
</template>
