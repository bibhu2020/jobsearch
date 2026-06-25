<script setup lang="ts">
import { reactive, watch, ref, onMounted, onUnmounted } from 'vue'
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

// Mobile stage tab tracking
const boardRef = ref<HTMLElement | null>(null)
const activeStage = ref<Stage>(STAGES[0].key)

function scrollToStage(stageKey: Stage) {
  const board = boardRef.value
  if (!board) return
  const col = board.querySelector(`[data-stage="${stageKey}"]`) as HTMLElement | null
  if (col) col.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' })
  activeStage.value = stageKey
}

function onScroll() {
  const board = boardRef.value
  if (!board) return
  const scrollLeft = board.scrollLeft
  const width = board.clientWidth
  for (const stage of STAGES) {
    const col = board.querySelector(`[data-stage="${stage.key}"]`) as HTMLElement | null
    if (!col) continue
    const left = col.offsetLeft - board.offsetLeft
    if (left >= scrollLeft - 20 && left <= scrollLeft + width / 2) {
      activeStage.value = stage.key
      break
    }
  }
}

onMounted(() => boardRef.value?.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => boardRef.value?.removeEventListener('scroll', onScroll))

const STAGE_DOT: Record<string, string> = {
  wishlist: 'bg-violet-400', applied: 'bg-blue-500',
  interviewing: 'bg-amber-500', offer: 'bg-emerald-500', rejected: 'bg-red-400',
}
</script>

<template>
  <div class="flex flex-col h-full">

    <!-- Mobile stage tabs (sm:hidden) -->
    <div class="sm:hidden flex items-center gap-1.5 px-3 py-2 bg-slate-900 border-b border-slate-700/60 overflow-x-auto scrollbar-hide">
      <button
        v-for="stage in STAGES"
        :key="stage.key"
        @click="scrollToStage(stage.key)"
        :class="[
          'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all border flex-shrink-0',
          activeStage === stage.key
            ? 'bg-slate-700 text-white border-slate-600'
            : 'text-slate-500 border-transparent hover:text-slate-300',
        ]">
        <span :class="['w-1.5 h-1.5 rounded-full flex-shrink-0', STAGE_DOT[stage.key]]"></span>
        {{ stage.label }}
        <span class="text-[10px] font-semibold tabular-nums opacity-70">{{ stageLists[stage.key].length }}</span>
      </button>
    </div>

    <!-- Board -->
    <div ref="boardRef" class="flex-1 flex gap-3 p-3 sm:gap-4 sm:p-4 overflow-x-auto snap-x snap-mandatory scrollbar-hide">
      <KanbanColumn
        v-for="stage in STAGES"
        :key="stage.key"
        :stage="stage"
        v-model:cards="stageLists[stage.key]"
        @card-click="emit('card-click', $event)"
        @drop="onDrop"
      />
    </div>
  </div>
</template>
