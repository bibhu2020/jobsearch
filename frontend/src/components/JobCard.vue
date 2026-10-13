<script setup lang="ts">
import type { PipelineCard } from '@/stores/pipeline'

const props = defineProps<{
  card: PipelineCard
  stageKey: string
}>()
defineEmits<{ (e: 'click'): void; (e: 'apply'): void }>()

const ACCENT: Record<string, string> = {
  wishlist:     'border-l-violet-400',
  applied:      'border-l-blue-500',
  interviewing: 'border-l-amber-500',
  offer:        'border-l-emerald-500',
  rejected:     'border-l-red-400',
}

function initial(name: string) {
  return (name || '?')[0].toUpperCase()
}

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const days = Math.floor(diff / 86400000)
  if (days === 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days}d ago`
  if (days < 30) return `${Math.floor(days / 7)}w ago`
  return `${Math.floor(days / 30)}mo ago`
}

const accent = ACCENT[props.stageKey] ?? 'border-l-slate-600'
</script>

<template>
  <div
    @click="$emit('click')"
    :class="[
      'bg-slate-800 rounded-lg border border-slate-700/60 border-l-4 p-3 shadow-sm',
      'hover:shadow-md hover:border-slate-600 hover:-translate-y-px',
      'cursor-pointer transition-all select-none group',
      accent,
    ]"
  >
    <!-- Title + company -->
    <p class="text-sm font-semibold text-slate-100 leading-snug line-clamp-2 group-hover:text-indigo-400 transition-colors">
      {{ card.title || 'Untitled Position' }}
    </p>

    <!-- Company row -->
    <div class="flex items-center gap-1.5 mt-1.5">
      <span class="flex-shrink-0 w-4 h-4 rounded bg-slate-700 text-slate-400 text-[9px] font-bold flex items-center justify-center">
        {{ initial(card.company) }}
      </span>
      <p class="text-xs text-slate-400 truncate">{{ card.company }}</p>
    </div>

    <!-- Footer -->
    <div class="flex items-center justify-between mt-2.5 pt-2 border-t border-slate-700/60">
      <span v-if="card.location" class="text-[11px] text-slate-500 truncate max-w-[110px] flex items-center gap-1">
        <svg class="h-3 w-3 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
        </svg>
        {{ card.location }}
      </span>
      <span v-else class="flex-1"></span>
      <span class="text-[11px] text-slate-500 flex-shrink-0">{{ timeAgo(card.created_at) }}</span>
    </div>

    <!-- Auto-apply (Wishlist only) -->
    <button v-if="stageKey === 'wishlist' && card.url"
      @click.stop="$emit('apply')" @mousedown.stop @touchstart.stop
      class="mt-2 w-full flex items-center justify-center gap-1.5 px-2 py-1.5 rounded-md text-xs font-semibold bg-indigo-600/90 hover:bg-indigo-500 text-white transition">
      <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
      </svg>
      Apply
    </button>
  </div>
</template>
