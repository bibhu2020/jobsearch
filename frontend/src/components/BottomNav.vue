<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
</script>

<template>
  <nav
    class="sm:hidden fixed bottom-0 inset-x-0 z-40 bg-white border-t border-gray-200 shadow-[0_-1px_6px_0_rgb(0,0,0,0.07)]"
    style="padding-bottom: env(safe-area-inset-bottom)"
  >
    <div class="flex items-center justify-around h-16">

      <!-- ── Candidate mode ── -->
      <template v-if="!auth.isInterviewer">

        <!-- Pipeline -->
        <router-link to="/pipeline"
          class="flex flex-col items-center gap-0.5 flex-1 py-2 text-gray-400 transition-colors"
          active-class="!text-indigo-600">
          <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M9 4.5v15m6-15v15M3.75 4.5h16.5a.75.75 0 01.75.75v13.5a.75.75 0 01-.75.75H3.75a.75.75 0 01-.75-.75V5.25a.75.75 0 01.75-.75z" />
          </svg>
          <span class="text-[10px] font-medium leading-none">Pipeline</span>
        </router-link>

        <!-- Suggestions -->
        <router-link to="/suggestions"
          class="flex flex-col items-center gap-0.5 flex-1 py-2 text-gray-400 transition-colors"
          active-class="!text-indigo-600">
          <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803a7.5 7.5 0 0010.607 0z" />
          </svg>
          <span class="text-[10px] font-medium leading-none">Search</span>
        </router-link>

      </template>

      <!-- ── Interviewer mode ── -->
      <template v-else>

        <!-- Projects -->
        <router-link to="/interviewer"
          class="flex flex-col items-center gap-0.5 flex-1 py-2 text-gray-400 transition-colors"
          active-class="!text-purple-600">
          <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
          </svg>
          <span class="text-[10px] font-medium leading-none">Projects</span>
        </router-link>

      </template>

      <!-- Profile (both modes) -->
      <router-link to="/profile"
        class="flex flex-col items-center gap-0.5 flex-1 py-2 text-gray-400 transition-colors"
        active-class="!text-indigo-600">
        <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M17.982 18.725A7.488 7.488 0 0012 15.75a7.488 7.488 0 00-5.982 2.975m11.963 0a9 9 0 10-11.963 0m11.963 0A8.966 8.966 0 0112 21a8.966 8.966 0 01-5.982-2.275M15 9.75a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span class="text-[10px] font-medium leading-none">Profile</span>
      </router-link>

      <!-- Mode toggle -->
      <button
        @click="auth.switchMode(auth.isInterviewer ? 'candidate' : 'interviewer')"
        class="flex flex-col items-center gap-0.5 flex-1 py-2 transition-colors"
        :class="auth.isInterviewer ? 'text-purple-500' : 'text-gray-400'">
        <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 3M21 7.5H7.5" />
        </svg>
        <span class="text-[10px] font-medium leading-none">{{ auth.isInterviewer ? 'Hiring' : 'Candidate' }}</span>
      </button>

      <!-- Sign out -->
      <button
        @click="auth.logout()"
        class="flex flex-col items-center gap-0.5 flex-1 py-2 text-gray-400 hover:text-red-500 transition-colors">
        <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
        </svg>
        <span class="text-[10px] font-medium leading-none">Sign out</span>
      </button>

    </div>
  </nav>
</template>
