<script setup lang="ts">
import { computed } from 'vue'
import type { Suggestion } from '@/stores/suggestions'

const props = defineProps<{ suggestion: Suggestion }>()
defineEmits<{ (e: 'add'): void; (e: 'dismiss'): void }>()

const score = computed(() => props.suggestion.match_score || 0)

const scoreStyle = computed(() => {
  if (score.value >= 80) return { ring: 'text-emerald-400', bg: 'bg-emerald-500', track: 'bg-emerald-900/40 border-emerald-700/40', badge: 'bg-emerald-900/30 text-emerald-400 border-emerald-700/40' }
  if (score.value >= 65) return { ring: 'text-blue-400',    bg: 'bg-blue-500',    track: 'bg-blue-900/40 border-blue-700/40',       badge: 'bg-blue-900/30 text-blue-400 border-blue-700/40'       }
  if (score.value >= 50) return { ring: 'text-amber-400',   bg: 'bg-amber-500',   track: 'bg-amber-900/40 border-amber-700/40',     badge: 'bg-amber-900/30 text-amber-400 border-amber-700/40'   }
  return                         { ring: 'text-red-400',    bg: 'bg-red-500',     track: 'bg-red-900/40 border-red-700/40',         badge: 'bg-red-900/30 text-red-400 border-red-700/40'         }
})

const recommendation = computed(() => {
  const r = props.suggestion.recommendation
  if (r === 'apply')    return { label: 'Apply',    icon: '✓', cls: 'bg-emerald-900/30 text-emerald-400 border-emerald-700/40' }
  if (r === 'consider') return { label: 'Consider', icon: '~', cls: 'bg-amber-900/30 text-amber-400 border-amber-700/40' }
  return                       { label: 'Skip',     icon: '✕', cls: 'bg-slate-700/50 text-slate-500 border-slate-600' }
})

const SOURCE_COLOR: Record<string, string> = {
  remotive:         'bg-violet-900/40 text-violet-400',
  dice:             'bg-red-900/40 text-red-400',
  builtin:          'bg-emerald-900/40 text-emerald-400',
  wellfound:        'bg-orange-900/40 text-orange-400',
  linkedin:         'bg-sky-900/40 text-sky-400',
  remote100k:       'bg-green-900/40 text-green-400',
  remoterocketship: 'bg-purple-900/40 text-purple-400',
  weworkremotely:   'bg-cyan-900/40 text-cyan-400',
  remoteok:         'bg-teal-900/40 text-teal-400',
  indeed:           'bg-indigo-900/40 text-indigo-400',
}
</script>

<template>
  <div class="bg-slate-800 rounded-xl border border-slate-700/60 shadow-sm hover:shadow-md hover:border-slate-600 transition-all overflow-hidden">

    <!-- Header row -->
    <div class="flex items-start gap-4 p-4">

      <!-- Score circle -->
      <div class="flex-shrink-0 flex flex-col items-center pt-0.5">
        <div :class="['relative w-12 h-12 rounded-full flex items-center justify-center border-2', scoreStyle.track]">
          <span :class="['text-sm font-bold tabular-nums leading-none', scoreStyle.ring]">{{ score }}</span>
        </div>
        <span class="text-[10px] text-slate-600 mt-1 font-medium">match</span>
      </div>

      <!-- Job info -->
      <div class="flex-1 min-w-0">
        <div class="flex items-start justify-between gap-2 mb-1">
          <h3 class="text-sm font-bold text-slate-100 leading-snug">{{ suggestion.title }}</h3>
          <span :class="['flex-shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-full', SOURCE_COLOR[suggestion.source] ?? 'bg-slate-700 text-slate-400']">
            {{ suggestion.source }}
          </span>
        </div>
        <p class="text-sm text-slate-400">
          {{ suggestion.company }}<span v-if="suggestion.location" class="text-slate-500"> · {{ suggestion.location }}</span>
        </p>

        <!-- Recommendation + score bar -->
        <div class="flex items-center gap-3 mt-2">
          <span :class="['inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border', recommendation.cls]">
            {{ recommendation.icon }} {{ recommendation.label }}
          </span>
          <div class="flex-1 h-1.5 rounded-full bg-slate-700 overflow-hidden">
            <div :class="['h-full rounded-full transition-all', scoreStyle.bg]" :style="`width:${score}%`" />
          </div>
        </div>
      </div>
    </div>

    <!-- Body -->
    <div class="px-4 pb-4 space-y-3 border-t border-slate-700/60 pt-3">

      <!-- AI summary -->
      <p v-if="suggestion.match_reason" class="text-sm text-slate-300 leading-relaxed">
        {{ suggestion.match_reason }}
      </p>

      <!-- Matching / gaps grid -->
      <div v-if="suggestion.matching?.length || suggestion.gaps?.length"
        class="grid grid-cols-2 gap-3 bg-slate-900/60 rounded-xl p-3 border border-slate-700/40">
        <div v-if="suggestion.matching?.length">
          <p class="text-[10px] font-bold text-emerald-500 uppercase tracking-widest mb-1.5">Strengths</p>
          <ul class="space-y-1">
            <li v-for="m in suggestion.matching" :key="m" class="flex items-start gap-1.5 text-xs text-slate-400">
              <span class="text-emerald-400 font-bold mt-0.5 flex-shrink-0">✓</span>
              {{ m }}
            </li>
          </ul>
        </div>
        <div v-if="suggestion.gaps?.length">
          <p class="text-[10px] font-bold text-amber-500 uppercase tracking-widest mb-1.5">Gaps</p>
          <ul class="space-y-1">
            <li v-for="g in suggestion.gaps" :key="g" class="flex items-start gap-1.5 text-xs text-slate-400">
              <span class="text-amber-400 font-bold mt-0.5 flex-shrink-0">!</span>
              {{ g }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Description snippet -->
      <p v-if="suggestion.description" class="text-xs text-slate-500 line-clamp-2 leading-relaxed">
        {{ suggestion.description }}
      </p>

      <!-- Actions -->
      <div class="flex items-center gap-2 pt-1">
        <a v-if="suggestion.url" :href="suggestion.url" target="_blank"
          class="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium transition">
          View posting
          <svg class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
          </svg>
        </a>
        <div class="flex gap-2 ml-auto">
          <button @click="$emit('dismiss')"
            class="px-3 py-1.5 border border-slate-700 hover:bg-slate-700 text-slate-500 hover:text-slate-300 text-xs rounded-lg transition font-medium">
            Dismiss
          </button>
          <button @click="$emit('add')"
            class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition shadow-sm shadow-indigo-900/50">
            + Add to Pipeline
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
