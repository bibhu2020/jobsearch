<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
const menuOpen = ref(false)
</script>

<template>
  <nav class="bg-white border-b border-gray-200 px-4 py-3">
    <div class="flex items-center justify-between">
      <router-link to="/pipeline" class="text-lg font-bold text-indigo-600 tracking-tight" @click="menuOpen = false">
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
      <button @click="auth.logout()" class="hidden sm:block text-sm text-gray-500 hover:text-gray-800 transition">Sign out</button>

      <!-- Mobile hamburger -->
      <button @click="menuOpen = !menuOpen" class="sm:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100 transition">
        <svg v-if="!menuOpen" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
        <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Mobile menu -->
    <div v-if="menuOpen" class="sm:hidden pt-3 pb-1 border-t mt-3 space-y-1">
      <router-link to="/pipeline" @click="menuOpen = false"
        class="block px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100 transition"
        active-class="bg-indigo-50 text-indigo-700">📋 Pipeline</router-link>
      <router-link to="/suggestions" @click="menuOpen = false"
        class="block px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100 transition"
        active-class="bg-indigo-50 text-indigo-700">🔍 Suggestions</router-link>
      <router-link to="/profile" @click="menuOpen = false"
        class="block px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100 transition"
        active-class="bg-indigo-50 text-indigo-700">👤 Profile</router-link>
      <button @click="auth.logout()"
        class="block w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium text-red-500 hover:bg-red-50 transition">
        Sign out
      </button>
    </div>
  </nav>
</template>
