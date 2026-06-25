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
  <!-- snap-center so mobile swipe snaps one column at a time -->
  <div class="flex flex-col w-[80vw] sm:w-64 flex-shrink-0 h-full min-h-0 snap-center">
    <!-- Column header -->
    <div class="flex items-center justify-between mb-3 flex-shrink-0">
      <h3 class="text-sm font-semibold text-gray-700">{{ stage.label }}</h3>
      <span class="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{{ cards.length }}</span>
    </div>

    <!-- Card list -->
    <div :class="['flex-1 min-h-0 rounded-xl border-2 p-2 pb-20 sm:pb-2 overflow-y-auto transition-colors', stage.color]">
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
