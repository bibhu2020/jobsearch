<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Navbar from '@/components/Navbar.vue'
import KanbanBoard from '@/components/KanbanBoard.vue'
import AddJobModal from '@/components/AddJobModal.vue'
import JobDetailModal from '@/components/JobDetailModal.vue'
import { usePipelineStore, type PipelineCard } from '@/stores/pipeline'

const store = usePipelineStore()
const showAddModal = ref(false)
const selectedCard = ref<PipelineCard | null>(null)

onMounted(() => store.fetchCards())
</script>

<template>
  <div class="flex flex-col h-screen">
    <Navbar />
    <div class="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 border-b bg-white">
      <h1 class="text-lg sm:text-xl font-semibold text-gray-800">Job Pipeline</h1>
      <button @click="showAddModal = true"
        class="flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition">
        <span class="text-lg leading-none">+</span>
        <span class="hidden xs:inline sm:inline">Add Job</span>
      </button>
    </div>
    <div class="flex-1 overflow-hidden">
      <KanbanBoard @card-click="selectedCard = $event" />
    </div>

    <AddJobModal v-if="showAddModal" @close="showAddModal = false" />
    <JobDetailModal v-if="selectedCard" :card="selectedCard" @close="selectedCard = null" />
  </div>
</template>
