<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Navbar from '@/components/Navbar.vue'
import SuggestionCard from '@/components/SuggestionCard.vue'
import { useSuggestionsStore } from '@/stores/suggestions'

const store = useSuggestionsStore()
const keywords = ref('')
const countryOverride = ref('')
const importCount = ref<number | null>(null)

const effectiveCountry = () => countryOverride.value.trim() || store.detectedCountry

onMounted(async () => {
  await store.detectCountry()
  store.fetchSuggestions()
})

async function handleImport() {
  importCount.value = null
  const n = await store.importResults()
  importCount.value = n
}
</script>

<template>
  <div class="flex flex-col h-screen">
    <Navbar />

    <div class="border-b bg-white px-4 sm:px-6 py-4 space-y-3">
      <!-- Title row -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 class="text-lg sm:text-xl font-semibold text-gray-800">Job Suggestions</h1>
          <p class="text-xs sm:text-sm text-gray-500 mt-0.5">AI-curated matches — runs weekly via GitHub Actions</p>
        </div>
        <div class="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          <!-- Trigger GitHub Actions -->
          <button
            @click="store.triggerAction(keywords, effectiveCountry())"
            :disabled="store.workflowStatus === 'dispatching'"
            class="flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition"
          >
            <svg v-if="store.workflowStatus === 'dispatching'" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
              <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2z"/>
              <circle cx="12" cy="12" r="3" fill="currentColor" stroke="none"/>
            </svg>
            {{ store.workflowStatus === 'dispatching' ? 'Triggering…' : 'Run Search (GitHub Actions)' }}
          </button>

          <!-- Import committed results -->
          <button
            @click="handleImport"
            :disabled="store.loading"
            class="flex items-center justify-center gap-2 px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 text-gray-700 rounded-lg text-sm font-medium transition"
          >
            <svg v-if="store.loading" class="animate-spin h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4 text-gray-500">
              <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            {{ store.loading ? 'Importing…' : 'Import Results' }}
          </button>
        </div>
      </div>

      <!-- Workflow status banner -->
      <div
        v-if="store.workflowStatus === 'dispatched'"
        class="flex items-start gap-2 bg-green-50 border border-green-200 rounded-lg px-3 py-2 text-sm text-green-800"
      >
        <svg class="h-4 w-4 mt-0.5 shrink-0 text-green-600" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
        </svg>
        <span>{{ store.workflowMessage }}</span>
        <button @click="store.workflowStatus = 'idle'" class="ml-auto text-green-600 hover:text-green-800">✕</button>
      </div>
      <div
        v-if="store.workflowStatus === 'error'"
        class="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-800"
      >
        <svg class="h-4 w-4 mt-0.5 shrink-0 text-red-600" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
        </svg>
        <span>{{ store.workflowMessage }}</span>
        <button @click="store.workflowStatus = 'idle'" class="ml-auto text-red-600 hover:text-red-800">✕</button>
      </div>

      <!-- Import success banner -->
      <div
        v-if="importCount !== null"
        class="flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 text-sm text-blue-800"
      >
        <svg class="h-4 w-4 shrink-0 text-blue-600" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
        </svg>
        <span>{{ importCount === 0 ? 'No new results to import — check back after the workflow finishes.' : `Imported ${importCount} new job${importCount !== 1 ? 's' : ''}.` }}</span>
        <button @click="importCount = null" class="ml-auto text-blue-600 hover:text-blue-800">✕</button>
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
          <span v-if="store.detectedCountry && !countryOverride"
            class="inline-flex items-center gap-1 bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-medium px-2.5 py-1 rounded-full">
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

    <div class="flex-1 overflow-y-auto p-4 sm:p-6">
      <div v-if="store.loading && !store.suggestions.length" class="flex justify-center pt-20">
        <div class="animate-spin h-8 w-8 border-4 border-indigo-500 border-t-transparent rounded-full"></div>
      </div>
      <div v-else-if="!store.suggestions.length" class="text-center pt-16 sm:pt-24 text-gray-400">
        <div class="text-5xl mb-4">🔎</div>
        <p class="text-lg font-medium">No suggestions yet</p>
        <p class="text-sm mt-1 px-6">Click "Run Search (GitHub Actions)" — results appear after the workflow commits them (~5 min), then click "Import Results".</p>
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
