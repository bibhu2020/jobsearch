<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
</script>

<template>
  <nav class="bg-white border-b border-gray-200 px-4 py-3">
    <div class="flex items-center justify-between">
      <router-link :to="auth.isInterviewer ? '/interviewer' : '/pipeline'"
        class="text-lg font-bold text-indigo-600 tracking-tight">
        🎯 JobQuest AI
      </router-link>

      <!-- Desktop nav — Candidate mode -->
      <div v-if="!auth.isInterviewer" class="hidden sm:flex items-center gap-1">
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

      <!-- Desktop nav — Interviewer mode -->
      <div v-else class="hidden sm:flex items-center gap-1">
        <router-link to="/interviewer"
          class="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition"
          active-class="bg-indigo-50 text-indigo-700">Projects</router-link>
        <router-link to="/profile"
          class="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition"
          active-class="bg-indigo-50 text-indigo-700">Profile</router-link>
      </div>

      <!-- Mode toggle + sign out -->
      <div class="hidden sm:flex items-center gap-3">
        <button @click="auth.switchMode(auth.isInterviewer ? 'candidate' : 'interviewer')"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition"
          :class="auth.isInterviewer
            ? 'bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100'
            : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'">
          <span>{{ auth.isInterviewer ? '🧑‍💼 Interviewer' : '🔍 Candidate' }}</span>
          <svg class="h-3 w-3 opacity-50" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 3M21 7.5H7.5" />
          </svg>
        </button>
        <button @click="auth.logout()" class="text-sm text-gray-500 hover:text-gray-800 transition">
          Sign out
        </button>
      </div>
    </div>
  </nav>
</template>
