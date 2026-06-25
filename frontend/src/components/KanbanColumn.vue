<script setup lang="ts">
import { VueDraggable } from 'vue-draggable-plus'
import JobCard from './JobCard.vue'
import type { PipelineCard, Stage } from '@/stores/pipeline'

const props = defineProps<{
  stage: { key: Stage; label: string; color: string }
}>()

const emit = defineEmits<{
  (e: 'card-click', card: PipelineCard): void
  (e: 'drop', cardId: number, stage: Stage, index: number): void
}>()

const cards = defineModel<PipelineCard[]>('cards', { default: () => [] })

const STAGE_STYLES: Record<string, { dot: string; topBorder: string }> = {
  wishlist:     { dot: 'bg-violet-400',  topBorder: 'border-t-violet-400'  },
  applied:      { dot: 'bg-blue-500',    topBorder: 'border-t-blue-500'    },
  interviewing: { dot: 'bg-amber-500',   topBorder: 'border-t-amber-500'   },
  offer:        { dot: 'bg-emerald-500', topBorder: 'border-t-emerald-500' },
  rejected:     { dot: 'bg-red-400',     topBorder: 'border-t-red-400'     },
}

const style = STAGE_STYLES[props.stage.key] || { dot: 'bg-slate-500', topBorder: 'border-t-slate-500' }

function cardId(evt: any): number {
  return parseInt((evt.item as HTMLElement).dataset.cardId || '0')
}

function onAdd(evt: any) {
  emit('drop', cardId(evt), props.stage.key, evt.newIndex ?? 0)
}

function onUpdate(evt: any) {
  emit('drop', cardId(evt), props.stage.key, evt.newIndex ?? 0)
}
</script>

<template>
  <div class="flex flex-col w-[82vw] sm:w-64 flex-shrink-0 h-full min-h-0 snap-center" :data-stage="stage.key">

    <!-- Column header -->
    <div class="flex items-center justify-between mb-2.5 px-0.5">
      <div class="flex items-center gap-2">
        <span :class="['w-2 h-2 rounded-full flex-shrink-0', style.dot]"></span>
        <h3 class="text-sm font-semibold text-slate-300">{{ stage.label }}</h3>
      </div>
      <span class="text-xs font-medium bg-slate-700 text-slate-400 px-2 py-0.5 rounded-full tabular-nums">
        {{ cards.length }}
      </span>
    </div>

    <!--
      Card list — must be directly overflow-y-auto with NO overflow-hidden ancestor.
      An overflow:hidden parent breaks cross-column drag detection in Sortable.js.
      Use border-t-2 for the colored top strip instead.
    -->
    <div :class="[
      'flex-1 min-h-0 rounded-xl border border-slate-700/60 border-t-2',
      'bg-slate-800/60 overflow-y-auto p-2 pb-20 sm:pb-2',
      style.topBorder,
    ]">
      <VueDraggable
        v-model="cards"
        group="kanban"
        :animation="150"
        ghost-class="opacity-30"
        drag-class="shadow-xl"
        class="space-y-2 min-h-full"
        @add="onAdd"
        @update="onUpdate"
      >
        <div v-for="card in cards" :key="card.id" :data-card-id="card.id">
          <JobCard :card="card" :stage-key="stage.key" @click="emit('card-click', card)" />
        </div>
      </VueDraggable>

      <!-- Empty drop zone hint -->
      <div v-if="cards.length === 0"
        class="flex flex-col items-center justify-center py-8 text-slate-600">
        <svg class="h-8 w-8 mb-2 opacity-50" fill="none" stroke="currentColor" stroke-width="1" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        <p class="text-xs text-center leading-snug">Drop here or<br/>add a job</p>
      </div>
    </div>
  </div>
</template>
