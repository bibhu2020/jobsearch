<script setup lang="ts">
import { onMounted, ref } from 'vue'
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
</script>

<template>
  <div class="flex flex-col h-screen">
    <Navbar />

    <div class="border-b bg-white px-4 sm:px-6 py-4 space-y-3">
      <!-- Title row -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 class="text-lg sm:text-xl font-semibold text-gray-800">Job Suggestions</h1>
          <p class="text-xs sm:text-sm text-gray-500 mt-0.5">AI-curated matches from 10 live sources</p>
        </div>
        <button
          @click="store.sync(keywords, effectiveCountry())"
          :disabled="store.syncing"
          class="flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition w-full sm:w-auto"
        >
          <svg v-if="store.syncing" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          {{ store.syncing ? 'Searching…' : '🔍 Find New Jobs' }}
        </button>
      </div>

      <!-- Keyword search -->
      <input
        v-model="keywords"
        type="text"
        placeholder="Optional: keywords (e.g. Azure DevOps, Python engineer…)"
        class="w-full rounded-lg border-gray-300 text-sm focus:border-indigo-500 focus:ring-indigo-500"
        @keydown.enter="store.sync(keywords, effectiveCountry())"
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
      <div v-if="store.syncing" class="flex flex-col items-center pt-12 sm:pt-16 gap-4 text-gray-500">
        <div class="animate-spin h-10 w-10 border-4 border-indigo-500 border-t-transparent rounded-full"></div>
        <p class="text-sm text-center px-4">
          Searching Remotive, Dice, BuiltIn, Wellfound, LinkedIn,
          Remote100K, RemoteRocketship, WeWorkRemotely, RemoteOK &amp; Indeed…
        </p>
      </div>
      <div v-else-if="store.loading" class="flex justify-center pt-20">
        <div class="animate-spin h-8 w-8 border-4 border-indigo-500 border-t-transparent rounded-full"></div>
      </div>
      <div v-else-if="!store.suggestions.length" class="text-center pt-16 sm:pt-24 text-gray-400">
        <div class="text-5xl mb-4">🔎</div>
        <p class="text-lg font-medium">No suggestions yet</p>
        <p class="text-sm mt-1 px-6">Type keywords above (or set up your profile) then click "Find New Jobs"</p>
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
