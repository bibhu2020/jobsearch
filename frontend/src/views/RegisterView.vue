<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const name = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.register(name.value, email.value, password.value)
  } catch (e: any) {
    error.value = e.response?.data?.message || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex">

    <!-- Left: Register Form (1/3) -->
    <div class="w-full lg:w-1/3 flex items-center justify-center bg-white px-8 py-12 relative z-10 shadow-2xl">
      <div class="w-full max-w-sm">
        <div class="mb-8">
          <div class="text-3xl font-bold text-indigo-600 tracking-tight mb-1">🎯 JobQuest AI</div>
          <p class="text-gray-400 text-sm mt-1">Create your free account — takes 30 seconds</p>
        </div>

        <form @submit.prevent="submit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Full name</label>
            <input v-model="name" type="text" required placeholder="Jane Smith"
              class="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm shadow-sm focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Email address</label>
            <input v-model="email" type="email" required placeholder="you@example.com"
              class="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm shadow-sm focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
            <input v-model="password" type="password" required minlength="6" placeholder="Min. 6 characters"
              class="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm shadow-sm focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition" />
          </div>

          <p v-if="error" class="text-red-500 text-sm bg-red-50 px-3 py-2 rounded-lg">{{ error }}</p>

          <button type="submit" :disabled="loading"
            class="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] text-white font-semibold text-sm transition-all disabled:opacity-50 shadow-md shadow-indigo-200">
            {{ loading ? 'Creating account…' : 'Create Free Account' }}
          </button>
        </form>

        <p class="mt-4 text-center text-xs text-gray-400">
          By signing up you agree to use this tool responsibly.
        </p>

        <div class="mt-6 pt-6 border-t border-gray-100 text-center">
          <p class="text-sm text-gray-500">Already have an account?</p>
          <router-link to="/login"
            class="mt-2 inline-block w-full py-3 rounded-xl border-2 border-indigo-600 text-indigo-600 font-semibold text-sm hover:bg-indigo-50 transition text-center">
            Sign In
          </router-link>
        </div>
      </div>
    </div>

    <!-- Right: Feature Showcase (2/3) — same as login page -->
    <div class="hidden lg:flex lg:w-2/3 bg-gradient-to-br from-indigo-950 via-indigo-900 to-violet-900 flex-col justify-center px-16 py-14 relative overflow-hidden">

      <!-- Decorative orbs -->
      <div class="absolute -top-24 -right-24 w-96 h-96 bg-indigo-500 opacity-10 rounded-full blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-32 -left-16 w-80 h-80 bg-violet-500 opacity-15 rounded-full blur-3xl pointer-events-none"></div>

      <div class="relative z-10 max-w-2xl">

        <!-- Headline -->
        <div class="mb-10">
          <div class="inline-flex items-center gap-2 bg-indigo-800/60 border border-indigo-700/50 rounded-full px-4 py-1.5 mb-5">
            <span class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
            <span class="text-indigo-200 text-xs font-medium tracking-wide">Free · No credit card · Start in 30s</span>
          </div>
          <h1 class="text-4xl font-bold text-white leading-snug mb-3">
            Your AI co-pilot for<br/>
            <span class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-300 to-violet-300">every job application</span>
          </h1>
          <p class="text-indigo-300 text-base leading-relaxed">
            From discovering openings to crafting the perfect cover letter, JobQuest AI handles the heavy lifting so you can focus on the interviews.
          </p>
        </div>

        <!-- How it works steps -->
        <div class="mb-10 bg-white/5 border border-white/10 rounded-2xl px-6 py-5">
          <p class="text-indigo-400 text-xs font-semibold uppercase tracking-widest mb-4">How it works</p>
          <div class="space-y-4">
            <div v-for="(step, i) in [
              { n: '1', label: 'Upload your resume',       desc: 'AI extracts your skills and experience in seconds.',            color: 'bg-violet-500' },
              { n: '2', label: 'Discover matched jobs',    desc: 'Weekly agent scans 5 sources and scores relevance for you.',    color: 'bg-blue-500'   },
              { n: '3', label: 'Generate your kit',        desc: 'One click produces a cover letter, resume rewrite & prep guide.', color: 'bg-amber-500'  },
              { n: '4', label: 'Track your pipeline',      desc: 'Drag cards from Applied to Offer on your personal Kanban board.', color: 'bg-emerald-500'},
            ]" :key="i" class="flex items-start gap-4">
              <div :class="[step.color, 'w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0 mt-0.5']">{{ step.n }}</div>
              <div>
                <div class="text-white text-sm font-semibold">{{ step.label }}</div>
                <div class="text-indigo-300 text-xs mt-0.5">{{ step.desc }}</div>
              </div>
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
