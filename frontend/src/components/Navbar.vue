<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()

const initials = computed(() => {
  const name = auth.user?.name || auth.user?.email || '?'
  return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
})

function isActive(path: string) {
  return route.path === path || (path !== '/' && route.path.startsWith(path))
}
</script>

<template>
  <nav class="bg-slate-900 border-b border-slate-700/60 z-30 relative flex-shrink-0">
    <div class="flex items-center h-14 px-4 sm:px-6 gap-4">

      <!-- Logo -->
      <router-link :to="auth.isInterviewer ? '/interviewer' : '/pipeline'"
        class="flex items-center gap-2 font-bold text-[15px] tracking-tight flex-shrink-0">
        <span class="flex items-center justify-center w-7 h-7 bg-indigo-600 rounded-lg text-white text-sm shadow-lg shadow-indigo-900/50">🎯</span>
        <span class="hidden sm:inline text-white">JobQuest AI</span>
      </router-link>

      <!-- Candidate nav (desktop) -->
      <div v-if="!auth.isInterviewer" class="hidden sm:flex items-center h-full ml-2">
        <router-link v-for="link in [
          { to: '/pipeline', label: 'Pipeline' },
          { to: '/suggestions', label: 'Job Search' },
          { to: '/profile', label: 'Profile' },
        ]" :key="link.to" :to="link.to"
          :class="[
            'flex items-center h-full px-3 text-sm font-medium border-b-2 transition-colors',
            isActive(link.to)
              ? 'text-white border-indigo-500'
              : 'text-slate-400 border-transparent hover:text-slate-200 hover:border-slate-600',
          ]">
          {{ link.label }}
        </router-link>
      </div>

      <!-- Interviewer nav (desktop) -->
      <div v-else class="hidden sm:flex items-center h-full ml-2">
        <router-link v-for="link in [
          { to: '/interviewer', label: 'Projects' },
          { to: '/profile', label: 'Profile' },
        ]" :key="link.to" :to="link.to"
          :class="[
            'flex items-center h-full px-3 text-sm font-medium border-b-2 transition-colors',
            isActive(link.to)
              ? 'text-white border-indigo-500'
              : 'text-slate-400 border-transparent hover:text-slate-200 hover:border-slate-600',
          ]">
          {{ link.label }}
        </router-link>
      </div>

      <!-- Right controls -->
      <div class="flex items-center gap-2 ml-auto">

        <!-- Mode toggle -->
        <button @click="auth.switchMode(auth.isInterviewer ? 'candidate' : 'interviewer')"
          class="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all"
          :class="auth.isInterviewer
            ? 'bg-purple-500/10 text-purple-300 border-purple-500/30 hover:bg-purple-500/20'
            : 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30 hover:bg-indigo-500/20'">
          <span>{{ auth.isInterviewer ? '🧑‍💼' : '🔍' }}</span>
          <span>{{ auth.isInterviewer ? 'Hiring' : 'Job Hunt' }}</span>
        </button>

        <!-- Sign out -->
        <button @click="auth.logout()"
          class="hidden sm:flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-200 transition px-2 py-1 rounded-lg hover:bg-slate-800">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
          </svg>
        </button>

        <!-- User avatar -->
        <div class="w-8 h-8 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center flex-shrink-0 select-none ring-2 ring-indigo-500/30">
          {{ initials }}
        </div>
      </div>
    </div>
  </nav>
</template>
