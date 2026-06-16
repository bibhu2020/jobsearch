<script setup lang="ts">
import { ref, watch } from 'vue'
import GenerateKitPanel from './GenerateKitPanel.vue'
import { usePipelineStore, type PipelineCard } from '@/stores/pipeline'

const props = defineProps<{ card: PipelineCard }>()
const emit = defineEmits<{ (e: 'close'): void }>()
const store = usePipelineStore()
const notes = ref(props.card.notes || '')
const showFullDesc = ref(false)
const descLimit = 400

watch(() => props.card.notes, (v) => { notes.value = v || '' })

function saveNotes() {
  store.updateNotes(props.card.id, notes.value)
}

async function deleteCard() {
  if (confirm('Remove this job from your pipeline?')) {
    await store.deleteCard(props.card.id)
    emit('close')
  }
}
</script>

<template>
  <div class="fixed inset-0 bg-black/40 z-50 flex justify-end" @click.self="emit('close')">
    <div class="bg-white w-full max-w-xl h-full overflow-y-auto shadow-2xl flex flex-col">

      <!-- Header -->
      <div class="sticky top-0 bg-white border-b px-6 py-4 flex items-start justify-between z-10">
        <div class="flex-1 min-w-0 pr-4">
          <h2 class="text-lg font-bold text-gray-900 leading-tight">{{ card.title || 'Untitled Position' }}</h2>
          <p class="text-sm text-gray-500 mt-0.5">{{ card.company }}<span v-if="card.location"> · {{ card.location }}</span></p>
        </div>
        <button @click="emit('close')" class="text-gray-400 hover:text-gray-600 text-2xl leading-none flex-shrink-0">×</button>
      </div>

      <div class="flex-1 px-6 py-5 space-y-6">

        <!-- Quick actions -->
        <div class="flex gap-2 flex-wrap">
          <a v-if="card.url" :href="card.url" target="_blank"
            class="px-3 py-1.5 text-sm border border-gray-200 rounded-lg text-indigo-600 hover:bg-indigo-50 transition">
            🔗 View Posting
          </a>
          <button @click="deleteCard"
            class="px-3 py-1.5 text-sm border border-red-200 rounded-lg text-red-500 hover:bg-red-50 transition ml-auto">
            🗑 Remove
          </button>
        </div>

        <!-- Description -->
        <div v-if="card.description">
          <h3 class="text-sm font-semibold text-gray-700 mb-2">Job Description</h3>
          <p class="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
            {{ showFullDesc ? card.description : card.description.slice(0, descLimit) }}
            <span v-if="card.description.length > descLimit">
              <button @click="showFullDesc = !showFullDesc" class="text-indigo-500 hover:underline ml-1">
                {{ showFullDesc ? 'Show less' : '… Read more' }}
              </button>
            </span>
          </p>
        </div>

        <!-- Notes -->
        <div>
          <h3 class="text-sm font-semibold text-gray-700 mb-2">My Notes</h3>
          <textarea v-model="notes" @blur="saveNotes" rows="3"
            placeholder="Add notes, reminders, contacts…"
            class="w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-sm resize-none" />
        </div>

        <!-- Generate Kit -->
        <GenerateKitPanel :card-id="card.id" :job-title="card.title || ''" :company="card.company || ''" />
      </div>
    </div>
  </div>
</template>
