<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import Navbar from '@/components/Navbar.vue'
import SuggestionCard from '@/components/SuggestionCard.vue'
import { useSuggestionsStore } from '@/stores/suggestions'

const store = useSuggestionsStore()
const keywords = ref('')
const countryOverride = ref('')

const effectiveCountry = () => countryOverride.value.trim() || store.detectedCountry

onMounted(async () => {
  await store.detectCountry()
  store.fetchSuggestions()
})

function stepIcon(step: { status: string; conclusion: string | null }) {
  if (step.status === 'completed') {
    if (step.conclusion === 'success') return 'success'
    if (step.conclusion === 'skipped') return 'skipped'
    return 'failure'
  }
  if (step.status === 'in_progress') return 'running'
  return 'queued'
}

const isRunning = computed(() =>
  store.workflowStatus === 'dispatching' || store.workflowStatus === 'running'
)
</script>

<template>
  <div class="flex flex-col h-screen bg-slate-900">
    <Navbar />

    <!-- Controls header -->
    <div class="bg-slate-900 border-b border-slate-700/60 px-4 sm:px-6 py-4 space-y-3 flex-shrink-0">

      <!-- Title + trigger -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 class="text-base font-semibold text-slate-100">Job Search</h1>
          <p class="text-xs text-slate-500 mt-0.5">AI-curated matches · runs on GitHub Actions using your profile</p>
        </div>
        <button
          @click="store.triggerAction(keywords, effectiveCountry())"
          :disabled="isRunning"
          class="flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-sm font-semibold transition-all shadow-sm shadow-indigo-900/50 flex-shrink-0">
          <svg v-if="isRunning" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 010 1.972l-11.54 6.347a1.125 1.125 0 01-1.667-.986V5.653z" />
          </svg>
          {{ store.workflowStatus === 'dispatching' ? 'Triggering…' : isRunning ? 'Running…' : 'Run Job Search' }}
        </button>
      </div>

      <!-- Keyword + location row -->
      <div class="flex flex-col sm:flex-row gap-2">
        <div class="flex-1 relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 pointer-events-none" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803a7.5 7.5 0 0010.607 0z" />
          </svg>
          <input v-model="keywords" type="text"
            placeholder="Keywords (e.g. Python, Azure DevOps, remote…)"
            class="w-full pl-9 pr-3 py-2 rounded-lg border-slate-600 bg-slate-800 text-slate-100 placeholder-slate-500 focus:bg-slate-700 text-sm focus:border-indigo-500 focus:ring-indigo-500 transition"
            @keydown.enter="store.triggerAction(keywords, effectiveCountry())" />
        </div>
        <div class="flex items-center gap-2 sm:w-56">
          <svg class="h-4 w-4 text-slate-500 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
          </svg>
          <input v-model="countryOverride" type="text"
            :placeholder="store.detectedCountry || 'Country / location'"
            class="flex-1 py-2 rounded-lg border-slate-600 bg-slate-800 text-slate-100 placeholder-slate-500 focus:bg-slate-700 text-sm focus:border-indigo-500 focus:ring-indigo-500 transition" />
          <span v-if="store.detectedCountry && !countryOverride"
            class="hidden sm:inline-flex text-[10px] font-medium text-indigo-400 bg-indigo-900/30 border border-indigo-700/40 px-1.5 py-0.5 rounded-full whitespace-nowrap">
            auto
          </span>
        </div>
      </div>

      <!-- Live workflow status -->
      <transition name="slide-down">
        <div v-if="store.workflowStatus !== 'idle'"
          class="rounded-xl border overflow-hidden text-sm"
          :class="{
            'border-indigo-700/60 bg-indigo-900/20': isRunning,
            'border-emerald-700/60 bg-emerald-900/20': store.workflowStatus === 'completed',
            'border-red-700/60 bg-red-900/20': store.workflowStatus === 'error',
          }">
          <!-- Status bar -->
          <div class="flex items-center justify-between px-4 py-3">
            <div class="flex items-center gap-2.5">
              <svg v-if="isRunning" class="animate-spin h-4 w-4 text-indigo-400 flex-shrink-0" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <svg v-else-if="store.workflowStatus === 'completed'" class="h-4 w-4 text-emerald-400 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              <svg v-else class="h-4 w-4 text-red-400 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
              </svg>
              <span class="font-medium text-sm" :class="{
                'text-indigo-300': isRunning,
                'text-emerald-300': store.workflowStatus === 'completed',
                'text-red-300': store.workflowStatus === 'error',
              }">{{ store.workflowMessage }}</span>
            </div>
            <div class="flex items-center gap-3">
              <a v-if="store.workflowRun?.runUrl" :href="store.workflowRun.runUrl" target="_blank" rel="noopener"
                class="text-xs font-medium text-indigo-400 hover:text-indigo-300 transition">
                View run ↗
              </a>
              <button @click="store.dismissWorkflow()"
                class="w-6 h-6 flex items-center justify-center text-slate-500 hover:text-slate-300 rounded transition">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Steps -->
          <div v-if="store.workflowRun?.steps?.length"
            class="border-t px-4 py-3 space-y-1.5"
            :class="{
              'border-indigo-700/40': isRunning,
              'border-emerald-700/40': store.workflowStatus === 'completed',
              'border-red-700/40': store.workflowStatus === 'error',
            }">
            <div v-for="step in store.workflowRun.steps" :key="step.name"
              class="flex items-center gap-2.5 text-xs">
              <template v-if="stepIcon(step) === 'success'">
                <svg class="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                </svg>
              </template>
              <template v-else-if="stepIcon(step) === 'running'">
                <svg class="animate-spin h-3.5 w-3.5 text-indigo-400 flex-shrink-0" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
              </template>
              <template v-else-if="stepIcon(step) === 'failure'">
                <svg class="h-3.5 w-3.5 text-red-400 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-1-9a1 1 0 112 0v4a1 1 0 11-2 0V9zm1 7a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
                </svg>
              </template>
              <template v-else-if="stepIcon(step) === 'skipped'">
                <span class="h-3.5 w-3.5 rounded-full bg-slate-600 flex-shrink-0 inline-block"></span>
              </template>
              <template v-else>
                <span class="h-3.5 w-3.5 rounded-full border-2 border-slate-600 flex-shrink-0 inline-block"></span>
              </template>
              <span :class="{
                'text-slate-100 font-medium': stepIcon(step) === 'running',
                'text-slate-600': stepIcon(step) === 'queued' || stepIcon(step) === 'skipped',
                'text-emerald-400': stepIcon(step) === 'success',
                'text-red-400': stepIcon(step) === 'failure',
              }">{{ step.name }}</span>
            </div>
          </div>
          <div v-else-if="isRunning"
            class="border-t border-indigo-700/40 px-4 py-2 text-xs text-indigo-400 italic">
            Waiting for GitHub Actions runner…
          </div>
        </div>
      </transition>
    </div>

    <!-- Suggestions list -->
    <div class="flex-1 overflow-y-auto px-4 sm:px-6 py-5 pb-24 sm:pb-6">

      <!-- Loading -->
      <div v-if="store.loading && !store.suggestions.length" class="flex justify-center pt-20">
        <div class="animate-spin h-8 w-8 border-4 border-indigo-500 border-t-transparent rounded-full"></div>
      </div>

      <!-- Empty state -->
      <div v-else-if="!store.suggestions.length"
        class="flex flex-col items-center justify-center text-center pt-16 sm:pt-24 px-6">
        <div class="w-16 h-16 rounded-2xl bg-indigo-900/30 border border-indigo-700/40 flex items-center justify-center mb-4">
          <svg class="h-8 w-8 text-indigo-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803a7.5 7.5 0 0010.607 0z" />
          </svg>
        </div>
        <h2 class="text-base font-semibold text-slate-200 mb-1">No suggestions yet</h2>
        <p class="text-sm text-slate-500 max-w-sm leading-relaxed">
          Click <span class="font-semibold text-indigo-400">Run Job Search</span> — your profile is used to find
          matching roles across 10 sources. Results appear automatically when the search completes (~5 min).
        </p>
      </div>

      <!-- Cards -->
      <div v-else class="max-w-3xl mx-auto space-y-3">
        <div class="flex items-center justify-between mb-4">
          <p class="text-sm font-medium text-slate-400">
            {{ store.suggestions.length }} suggestion{{ store.suggestions.length !== 1 ? 's' : '' }}
          </p>
          <span v-if="effectiveCountry()" class="text-xs font-medium text-indigo-400 bg-indigo-900/30 px-2.5 py-1 rounded-full border border-indigo-700/40">
            📍 {{ effectiveCountry() }}
          </span>
        </div>
        <SuggestionCard
          v-for="s in store.suggestions"
          :key="s.id"
          :suggestion="s"
          @add="store.addToWishlist(s.id)"
          @dismiss="store.dismiss(s.id)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
