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

// Step icon helper
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
  <div class="flex flex-col h-screen">
    <Navbar />

    <div class="border-b bg-white px-4 sm:px-6 py-4 space-y-3">
      <!-- Title row -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 class="text-lg sm:text-xl font-semibold text-gray-800">Job Suggestions</h1>
          <p class="text-xs sm:text-sm text-gray-500 mt-0.5">AI-curated matches — runs on GitHub Actions using your profile</p>
        </div>
        <div class="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          <button
            @click="store.triggerAction(keywords, effectiveCountry())"
            :disabled="isRunning"
            class="flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition"
          >
            <svg v-if="isRunning" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
              <polygon points="5,3 19,12 5,21" fill="currentColor" stroke="none" />
            </svg>
            {{ store.workflowStatus === 'dispatching' ? 'Triggering…' : isRunning ? 'Running…' : 'Run Job Search' }}
          </button>
        </div>
      </div>

      <!-- Live workflow status panel -->
      <div
        v-if="store.workflowStatus !== 'idle'"
        class="rounded-xl border overflow-hidden text-sm"
        :class="{
          'border-indigo-200 bg-indigo-50': store.workflowStatus === 'dispatching' || store.workflowStatus === 'running',
          'border-green-200 bg-green-50': store.workflowStatus === 'completed',
          'border-red-200 bg-red-50': store.workflowStatus === 'error',
        }"
      >
        <!-- Header bar -->
        <div class="flex items-center justify-between px-4 py-3">
          <div class="flex items-center gap-2.5">
            <!-- Animated spinner while running -->
            <svg
              v-if="store.workflowStatus === 'dispatching' || store.workflowStatus === 'running'"
              class="animate-spin h-4 w-4 text-indigo-500 shrink-0"
              fill="none" viewBox="0 0 24 24"
            >
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            <!-- Success -->
            <svg v-else-if="store.workflowStatus === 'completed'" class="h-4 w-4 text-green-600 shrink-0" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            <!-- Error -->
            <svg v-else class="h-4 w-4 text-red-500 shrink-0" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>

            <span
              class="font-medium"
              :class="{
                'text-indigo-800': isRunning,
                'text-green-800': store.workflowStatus === 'completed',
                'text-red-800': store.workflowStatus === 'error',
              }"
            >{{ store.workflowMessage }}</span>
          </div>

          <div class="flex items-center gap-3 shrink-0">
            <a
              v-if="store.workflowRun?.runUrl"
              :href="store.workflowRun.runUrl"
              target="_blank"
              rel="noopener"
              class="text-xs text-indigo-600 hover:underline"
            >View run ↗</a>
            <button
              @click="store.dismissWorkflow()"
              class="text-gray-400 hover:text-gray-600 text-base leading-none"
              aria-label="Dismiss"
            >✕</button>
          </div>
        </div>

        <!-- Step progress — only when we have step data -->
        <div v-if="store.workflowRun?.steps?.length" class="border-t px-4 py-3 space-y-2"
          :class="{
            'border-indigo-100': isRunning,
            'border-green-100': store.workflowStatus === 'completed',
            'border-red-100': store.workflowStatus === 'error',
          }"
        >
          <div
            v-for="step in store.workflowRun.steps"
            :key="step.name"
            class="flex items-center gap-2.5 text-xs"
          >
            <!-- Step icon -->
            <template v-if="stepIcon(step) === 'success'">
              <svg class="h-3.5 w-3.5 text-green-500 shrink-0" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
            </template>
            <template v-else-if="stepIcon(step) === 'running'">
              <svg class="animate-spin h-3.5 w-3.5 text-indigo-500 shrink-0" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
            </template>
            <template v-else-if="stepIcon(step) === 'failure'">
              <svg class="h-3.5 w-3.5 text-red-500 shrink-0" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-1-9a1 1 0 112 0v4a1 1 0 11-2 0V9zm1 7a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
              </svg>
            </template>
            <template v-else-if="stepIcon(step) === 'skipped'">
              <svg class="h-3.5 w-3.5 text-gray-300 shrink-0" viewBox="0 0 20 20" fill="currentColor">
                <circle cx="10" cy="10" r="8"/>
              </svg>
            </template>
            <template v-else>
              <!-- queued dot -->
              <span class="h-3.5 w-3.5 rounded-full border-2 border-gray-300 shrink-0 inline-block"></span>
            </template>

            <span
              :class="{
                'text-gray-800 font-medium': stepIcon(step) === 'running',
                'text-gray-500': stepIcon(step) === 'queued' || stepIcon(step) === 'skipped',
                'text-green-700': stepIcon(step) === 'success',
                'text-red-600': stepIcon(step) === 'failure',
              }"
            >{{ step.name }}</span>
          </div>
        </div>

        <!-- Waiting for run to appear -->
        <div
          v-else-if="store.workflowStatus === 'running'"
          class="border-t border-indigo-100 px-4 py-2 text-xs text-indigo-500 italic"
        >
          Waiting for GitHub Actions runner to pick up the job…
        </div>
      </div>

      <!-- Keyword search -->
      <input
        v-model="keywords"
        type="text"
        placeholder="Optional: keywords (e.g. Azure DevOps, Python engineer…)"
        class="w-full rounded-lg border-gray-300 text-sm focus:border-indigo-500 focus:ring-indigo-500"
        @keydown.enter="store.triggerAction(keywords, effectiveCountry())"
      />

      <!-- Country row -->
      <div class="flex flex-wrap items-center gap-2 text-sm">
        <span class="text-gray-500 shrink-0">📍 Country:</span>
        <span v-if="store.detectingCountry" class="text-gray-400 italic text-xs">Detecting…</span>
        <template v-else>
          <span
            v-if="store.detectedCountry && !countryOverride"
            class="inline-flex items-center gap-1 bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-medium px-2.5 py-1 rounded-full"
          >
            🌐 {{ store.detectedCountry }}
            <span class="text-indigo-400 text-[10px]">(auto)</span>
          </span>
          <input
            v-model="countryOverride"
            type="text"
            :placeholder="store.detectedCountry ? `Override: ${store.detectedCountry}` : 'e.g. United Kingdom…'"
            class="w-44 sm:w-56 text-xs rounded-md border-gray-300 focus:border-indigo-400 focus:ring-indigo-400 py-1"
          />
          <span class="hidden sm:inline text-xs text-gray-400">Jobs outside this country are penalised</span>
        </template>
      </div>
    </div>

    <!-- Suggestions list -->
    <div class="flex-1 overflow-y-auto p-4 sm:p-6">
      <div v-if="store.loading && !store.suggestions.length" class="flex justify-center pt-20">
        <div class="animate-spin h-8 w-8 border-4 border-indigo-500 border-t-transparent rounded-full"></div>
      </div>
      <div v-else-if="!store.suggestions.length" class="text-center pt-16 sm:pt-24 text-gray-400">
        <div class="text-5xl mb-4">🔎</div>
        <p class="text-lg font-medium">No suggestions yet</p>
        <p class="text-sm mt-1 px-6">
          Click <strong>Run Job Search</strong> — your profile will be used to find matching roles on GitHub Actions.
          Results appear automatically when the search completes (~5 min).
        </p>
      </div>
      <div v-else class="max-w-3xl mx-auto space-y-4">
        <p class="text-sm text-gray-500">
          {{ store.suggestions.length }} suggestion{{ store.suggestions.length !== 1 ? 's' : '' }} found
          <span v-if="effectiveCountry()" class="text-indigo-500 font-medium"> · {{ effectiveCountry() }}</span>
        </p>
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
