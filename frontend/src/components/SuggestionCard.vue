<script setup lang="ts">
import { computed } from 'vue'
import type { Suggestion } from '@/stores/suggestions'

const props = defineProps<{ suggestion: Suggestion }>()
defineEmits<{ (e: 'add'): void; (e: 'dismiss'): void }>()

const score = computed(() => props.suggestion.match_score || 0)

const scoreColor = computed(() => {
  if (score.value >= 70) return { ring: 'text-emerald-600', bg: 'bg-emerald-50', bar: 'bg-emerald-500' }
  if (score.value >= 50) return { ring: 'text-amber-600', bg: 'bg-amber-50', bar: 'bg-amber-500' }
  return { ring: 'text-red-500', bg: 'bg-red-50', bar: 'bg-red-400' }
})

const recommendation = computed(() => {
  const r = props.suggestion.recommendation
  if (r === 'apply') return { label: 'Yes — Apply', cls: 'bg-emerald-100 text-emerald-800 border-emerald-200' }
  if (r === 'consider') return { label: 'Maybe — Consider', cls: 'bg-amber-100 text-amber-800 border-amber-200' }
  return { label: 'Skip', cls: 'bg-red-100 text-red-700 border-red-200' }
})

const sourceColors: Record<string, string> = {
  // Tier 1
  remotive:          'bg-violet-100 text-violet-700',
  dice:              'bg-red-100 text-red-700',
  builtin:           'bg-emerald-100 text-emerald-700',
  wellfound:         'bg-orange-100 text-orange-700',
  linkedin:          'bg-sky-100 text-sky-700',
  // Tier 2
  remote100k:        'bg-green-100 text-green-700',
  remoterocketship:  'bg-purple-100 text-purple-700',
  weworkremotely:    'bg-cyan-100 text-cyan-700',
  remoteok:          'bg-teal-100 text-teal-700',
  // Tier 3
  indeed:            'bg-indigo-100 text-indigo-700',
}
</script>

<template>
  <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
    <!-- Top bar: score + header -->
    <div class="flex items-stretch">
      <!-- Score column -->
      <div :class="['flex flex-col items-center justify-center px-5 py-4 min-w-[90px]', scoreColor.bg]">
        <span :class="['text-3xl font-bold tabular-nums leading-none', scoreColor.ring]">{{ score }}</span>
        <span :class="['text-xs font-semibold mt-0.5', scoreColor.ring]">% match</span>
        <div class="w-12 h-1.5 rounded-full bg-gray-200 mt-2 overflow-hidden">
          <div :class="['h-full rounded-full transition-all', scoreColor.bar]" :style="`width:${score}%`" />
        </div>
      </div>

      <!-- Job info -->
      <div class="flex-1 min-w-0 px-4 py-4 border-l border-gray-100">
        <div class="flex items-start justify-between gap-2">
          <div class="min-w-0">
            <h3 class="text-base font-semibold text-gray-900 leading-snug">{{ suggestion.title }}</h3>
            <p class="text-sm text-gray-500 mt-0.5">{{ suggestion.company }}<span v-if="suggestion.location"> · {{ suggestion.location }}</span></p>
          </div>
          <span :class="['shrink-0 text-xs px-2 py-0.5 rounded-full font-medium', sourceColors[suggestion.source] || 'bg-gray-100 text-gray-600']">
            {{ suggestion.source }}
          </span>
        </div>

        <!-- Recommendation badge -->
        <div class="mt-2">
          <span :class="['inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded-full border', recommendation.cls]">
            {{ recommendation.label }}
          </span>
        </div>
      </div>
    </div>

    <div class="px-5 pb-4 pt-3 space-y-3 border-t border-gray-100">
      <!-- AI summary -->
      <p v-if="suggestion.match_reason" class="text-sm text-gray-700 leading-relaxed">
        {{ suggestion.match_reason }}
      </p>

      <!-- What matches / gaps -->
      <div class="grid grid-cols-2 gap-3" v-if="suggestion.matching?.length || suggestion.gaps?.length">
        <div v-if="suggestion.matching?.length">
          <p class="text-xs font-semibold text-emerald-700 uppercase tracking-wide mb-1.5">What matches</p>
          <ul class="space-y-1">
            <li v-for="m in suggestion.matching" :key="m" class="flex items-start gap-1.5 text-xs text-gray-700">
              <span class="text-emerald-500 mt-0.5 shrink-0">✓</span>
              <span>{{ m }}</span>
            </li>
          </ul>
        </div>
        <div v-if="suggestion.gaps?.length">
          <p class="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1.5">Gaps / concerns</p>
          <ul class="space-y-1">
            <li v-for="g in suggestion.gaps" :key="g" class="flex items-start gap-1.5 text-xs text-gray-700">
              <span class="text-amber-500 mt-0.5 shrink-0">!</span>
              <span>{{ g }}</span>
            </li>
          </ul>
        </div>
      </div>

      <!-- Description snippet -->
      <p class="text-xs text-gray-400 line-clamp-2">{{ suggestion.description }}</p>

      <!-- Actions -->
      <div class="flex gap-2 pt-1">
        <a v-if="suggestion.url" :href="suggestion.url" target="_blank"
          class="text-xs text-indigo-500 hover:underline self-center">View posting →</a>
        <div class="flex gap-2 ml-auto">
          <button @click="$emit('dismiss')"
            class="px-3 py-1.5 border border-gray-300 hover:bg-gray-50 text-gray-600 text-xs rounded-lg transition">
            Dismiss
          </button>
          <button @click="$emit('add')"
            class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-lg transition">
            + Add to Wishlist
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
