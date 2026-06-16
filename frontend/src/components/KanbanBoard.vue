<script setup lang="ts">
import { reactive, watch } from 'vue'
import KanbanColumn from './KanbanColumn.vue'
import { usePipelineStore, STAGES, type PipelineCard, type Stage } from '@/stores/pipeline'

const emit = defineEmits<{ (e: 'card-click', card: PipelineCard): void }>()
const store = usePipelineStore()

const stageLists = reactive<Record<Stage, PipelineCard[]>>({
  wishlist: [], applied: [], interviewing: [], offer: [], rejected: [],
})

watch(
  () => store.cards,
  (cards) => {
    for (const stage of Object.keys(stageLists) as Stage[]) {
      const next = cards.filter(c => c.stage === stage).sort((a, b) => a.position - b.position)
      stageLists[stage].splice(0, stageLists[stage].length, ...next)
    }
  },
  { immediate: true },
)

async function onDrop(cardId: number, toStage: Stage, toIndex: number) {
  await store.moveCard(cardId, toStage, toIndex)
}
</script>

<template>
  <div class="flex h-full gap-3 p-3 sm:gap-4 sm:p-4 overflow-x-auto snap-x snap-mandatory scrollbar-hide">
    <KanbanColumn
      v-for="stage in STAGES"
      :key="stage.key"
      :stage="stage"
      v-model:cards="stageLists[stage.key]"
      @card-click="emit('card-click', $event)"
      @drop="onDrop"
    />
  </div>
</template>
