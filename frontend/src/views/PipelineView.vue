<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import Navbar from '@/components/Navbar.vue'
import KanbanBoard from '@/components/KanbanBoard.vue'
import AddJobModal from '@/components/AddJobModal.vue'
import JobDetailModal from '@/components/JobDetailModal.vue'
import { usePipelineStore, type PipelineCard } from '@/stores/pipeline'

const store = usePipelineStore()
const showAddModal = ref(false)
const selectedCard = ref<PipelineCard | null>(null)
const total = computed(() => store.cards.length)

onMounted(() => store.fetchCards())
</script>

<template>
  <div class="flex flex-col h-screen bg-slate-900">
    <Navbar />

    <!-- Page header -->
    <div class="bg-slate-900 border-b border-slate-700/60 px-4 sm:px-6 py-3 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center gap-3">
        <h1 class="text-base font-semibold text-slate-100">Job Pipeline</h1>
        <span v-if="total > 0"
          class="text-xs font-medium bg-indigo-900/40 text-indigo-400 px-2 py-0.5 rounded-full tabular-nums border border-indigo-700/40">
          {{ total }} {{ total === 1 ? 'job' : 'jobs' }}
        </span>
      </div>
      <button @click="showAddModal = true"
        class="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 active:scale-[0.98] text-white rounded-lg text-sm font-medium transition-all shadow-sm shadow-indigo-900/50">
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Add Job
      </button>
    </div>

    <!-- Board -->
    <div class="flex-1 overflow-hidden">
      <KanbanBoard @card-click="selectedCard = $event" />
    </div>

    <AddJobModal v-if="showAddModal" @close="showAddModal = false" />
    <JobDetailModal v-if="selectedCard" :card="selectedCard" @close="selectedCard = null" />
  </div>
</template>
