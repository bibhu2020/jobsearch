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
  <div class="min-h-screen flex">

    <!-- Left: Login Form (1/3) -->
    <div class="w-full lg:w-1/3 flex items-center justify-center bg-white px-8 py-12 relative z-10 shadow-2xl">
      <div class="w-full max-w-sm">
        <div class="mb-8">
          <div class="text-3xl font-bold text-indigo-600 tracking-tight mb-1">🎯 JobQuest AI</div>
          <p class="text-gray-400 text-sm mt-1">Welcome back — sign in to continue</p>
        </div>

        <form @submit.prevent="submit" class="space-y-5">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Email address</label>
            <input v-model="email" type="email" required autocomplete="email" placeholder="you@example.com"
              class="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm shadow-sm focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
            <input v-model="password" type="password" required autocomplete="current-password" placeholder="••••••••"
              class="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm shadow-sm focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition" />
          </div>

          <p v-if="error" class="text-red-500 text-sm bg-red-50 px-3 py-2 rounded-lg">{{ error }}</p>

          <button type="submit" :disabled="loading"
            class="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] text-white font-semibold text-sm transition-all disabled:opacity-50 shadow-md shadow-indigo-200">
            {{ loading ? 'Signing in…' : 'Sign In' }}
          </button>
        </form>

        <div class="mt-8 pt-6 border-t border-gray-100 text-center">
          <p class="text-sm text-gray-500">
            Don't have an account?
          </p>
          <router-link to="/register"
            class="mt-2 inline-block w-full py-3 rounded-xl border-2 border-indigo-600 text-indigo-600 font-semibold text-sm hover:bg-indigo-50 transition text-center">
            Create Free Account
          </router-link>
        </div>
      </div>
    </div>

    <!-- Right: Feature Showcase (2/3) -->
    <div class="hidden lg:flex lg:w-2/3 bg-gradient-to-br from-indigo-950 via-indigo-900 to-violet-900 flex-col justify-center px-16 py-14 relative overflow-hidden">

      <!-- Decorative orbs -->
      <div class="absolute -top-24 -right-24 w-96 h-96 bg-indigo-500 opacity-10 rounded-full blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-32 -left-16 w-80 h-80 bg-violet-500 opacity-15 rounded-full blur-3xl pointer-events-none"></div>
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-blue-400 opacity-5 rounded-full blur-3xl pointer-events-none"></div>

      <div class="relative z-10 max-w-2xl">

        <!-- Headline -->
        <div class="mb-10">
          <div class="inline-flex items-center gap-2 bg-indigo-800/60 border border-indigo-700/50 rounded-full px-4 py-1.5 mb-5">
            <span class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
            <span class="text-indigo-200 text-xs font-medium tracking-wide">AI-Powered Job Tracker</span>
          </div>
          <h1 class="text-4xl font-bold text-white leading-snug mb-3">
            Land your dream job<br/>
            <span class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-300 to-violet-300">faster with AI</span>
          </h1>
          <p class="text-indigo-300 text-base leading-relaxed">
            Stop juggling spreadsheets. JobQuest AI tracks every application, generates tailored documents, and discovers new opportunities — automatically.
          </p>
        </div>

        <!-- Pipeline flow diagram -->
        <div class="mb-10 bg-white/5 border border-white/10 rounded-2xl px-6 py-5">
          <p class="text-indigo-400 text-xs font-semibold uppercase tracking-widest mb-4">Your hiring pipeline</p>
          <div class="flex items-center gap-2 flex-wrap">
            <div v-for="(stage, i) in [
              { label: 'Saved',     bg: 'bg-slate-600',  ring: 'ring-slate-500',  n: '12' },
              { label: 'Applied',   bg: 'bg-blue-600',   ring: 'ring-blue-500',   n: '8'  },
              { label: 'Interview', bg: 'bg-amber-500',  ring: 'ring-amber-400',  n: '3'  },
              { label: 'Offer',     bg: 'bg-emerald-500',ring: 'ring-emerald-400',n: '1'  },
            ]" :key="i" class="flex items-center gap-2">
              <div :class="[stage.bg, stage.ring, 'rounded-xl px-4 py-2.5 text-white shadow-lg ring-1 ring-opacity-60 min-w-[72px] text-center']">
                <div class="text-xl font-bold">{{ stage.n }}</div>
                <div class="text-xs font-medium opacity-80">{{ stage.label }}</div>
              </div>
              <svg v-if="i < 3" class="w-4 h-4 text-indigo-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- Feature cards 2x2 -->
        <div class="grid grid-cols-2 gap-4 mb-10">
          <div v-for="f in [
            {
              title: 'AI Document Generator',
              desc: 'Tailored cover letters, resume rewrites & interview prep — generated in seconds.',
              svg: `<svg class='w-5 h-5' fill='none' stroke='currentColor' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z'/></svg>`,
              color: 'text-violet-300',
              bg: 'bg-violet-500/10 border-violet-500/20',
            },
            {
              title: 'Visual Kanban Board',
              desc: 'Drag-and-drop cards through stages. Never lose track of where you stand.',
              svg: `<svg class='w-5 h-5' fill='none' stroke='currentColor' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2'/></svg>`,
              color: 'text-blue-300',
              bg: 'bg-blue-500/10 border-blue-500/20',
            },
            {
              title: 'Weekly Job Discovery',
              desc: 'AI agent scans 5 job sources every Friday night and surfaces the best fits.',
              svg: `<svg class='w-5 h-5' fill='none' stroke='currentColor' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z'/></svg>`,
              color: 'text-emerald-300',
              bg: 'bg-emerald-500/10 border-emerald-500/20',
            },
            {
              title: 'Resume Analysis',
              desc: 'Upload your resume and AI extracts skills, experience & match strength instantly.',
              svg: `<svg class='w-5 h-5' fill='none' stroke='currentColor' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'/></svg>`,
              color: 'text-amber-300',
              bg: 'bg-amber-500/10 border-amber-500/20',
            },
          ]" :key="f.title"
            :class="['rounded-2xl p-4 border backdrop-blur-sm hover:bg-white/10 transition-colors', f.bg]">
            <div :class="['mb-2.5', f.color]" v-html="f.svg"></div>
            <h3 class="text-white font-semibold text-sm mb-1">{{ f.title }}</h3>
            <p class="text-indigo-300 text-xs leading-relaxed">{{ f.desc }}</p>
          </div>
        </div>

        <!-- Stats bar -->
        <div class="flex items-center gap-10 pt-6 border-t border-white/10">
          <div>
            <div class="text-2xl font-bold text-white">GPT-4o</div>
            <div class="text-indigo-400 text-xs mt-0.5">Powered by OpenAI</div>
          </div>
          <div class="w-px h-8 bg-white/10"></div>
          <div>
            <div class="text-2xl font-bold text-white">5 Sources</div>
            <div class="text-indigo-400 text-xs mt-0.5">Jobs aggregated weekly</div>
          </div>
          <div class="w-px h-8 bg-white/10"></div>
          <div>
            <div class="text-2xl font-bold text-white">Free</div>
            <div class="text-indigo-400 text-xs mt-0.5">No credit card needed</div>
          </div>
        </div>

      </div>
    </div>

  </div>
</template>
