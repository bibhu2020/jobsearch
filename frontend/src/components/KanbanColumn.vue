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

// Two-way bound to stageLists[stage.key] in KanbanBoard
const cards = defineModel<PipelineCard[]>('cards', { default: () => [] })

function cardId(evt: any): number {
  return parseInt((evt.item as HTMLElement).dataset.cardId || '0')
}

// Fired when a card from ANOTHER column is dropped into this one
function onAdd(evt: any) {
  emit('drop', cardId(evt), props.stage.key, evt.newIndex ?? 0)
}

// Fired when a card is reordered within THIS column
function onUpdate(evt: any) {
  emit('drop', cardId(evt), props.stage.key, evt.newIndex ?? 0)
}
</script>

<template>
  <div class="flex flex-col w-64 flex-shrink-0 h-full min-h-0">
    <!-- Column header — fixed, never scrolls -->
    <div class="flex items-center justify-between mb-3 flex-shrink-0">
      <h3 class="text-sm font-semibold text-gray-700">{{ stage.label }}</h3>
      <span class="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{{ cards.length }}</span>
    </div>

    <!-- Card list — fills remaining height and scrolls -->
    <div :class="['flex-1 min-h-0 rounded-xl border-2 p-2 overflow-y-auto transition-colors', stage.color]">
      <VueDraggable
        v-model="cards"
        group="kanban"
        :animation="150"
        ghost-class="opacity-40"
        class="space-y-2 min-h-full"
        @add="onAdd"
        @update="onUpdate"
      >
        <div v-for="card in cards" :key="card.id" :data-card-id="card.id">
          <JobCard :card="card" @click="emit('card-click', card)" />
        </div>
      </VueDraggable>
    </div>
  </div>
</template>
