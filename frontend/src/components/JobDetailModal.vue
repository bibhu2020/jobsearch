<script setup lang="ts">
import { ref, watch } from 'vue'
import GenerateKitPanel from './GenerateKitPanel.vue'
import { usePipelineStore, type PipelineCard } from '@/stores/pipeline'

const props = defineProps<{ card: PipelineCard }>()
const emit = defineEmits<{ (e: 'close'): void }>()
const store = usePipelineStore()
const notes = ref(props.card.notes || '')
const showFullDesc = ref(false)
const notesSaved = ref(false)
const descLimit = 400

watch(() => props.card.notes, (v) => { notes.value = v || '' })

const STAGE_BADGE: Record<string, string> = {
  wishlist:     'bg-violet-900/40 text-violet-300 border-violet-700/60',
  applied:      'bg-blue-900/40 text-blue-300 border-blue-700/60',
  interviewing: 'bg-amber-900/40 text-amber-300 border-amber-700/60',
  offer:        'bg-emerald-900/40 text-emerald-300 border-emerald-700/60',
  rejected:     'bg-red-900/40 text-red-300 border-red-700/60',
}

const STAGE_STRIP: Record<string, string> = {
  wishlist:     'bg-violet-400',
  applied:      'bg-blue-500',
  interviewing: 'bg-amber-500',
  offer:        'bg-emerald-500',
  rejected:     'bg-red-400',
}

function saveNotes() {
  store.updateNotes(props.card.id, notes.value)
  notesSaved.value = true
  setTimeout(() => { notesSaved.value = false }, 2000)
}

async function deleteCard() {
  if (confirm('Remove this job from your pipeline?')) {
    await store.deleteCard(props.card.id)
    emit('close')
  }
}
</script>

<template>
  <div class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-end" @click.self="emit('close')">
    <div class="bg-slate-900 w-full sm:max-w-xl h-full overflow-y-auto shadow-2xl flex flex-col border-l border-slate-700/60">

      <!-- Top color strip -->
      <div :class="['h-1 flex-shrink-0', STAGE_STRIP[card.stage] ?? 'bg-indigo-500']"></div>

      <!-- Header -->
      <div class="sticky top-0 bg-slate-900 border-b border-slate-700/60 px-5 py-4 flex items-start justify-between z-10">
        <div class="flex-1 min-w-0 pr-3">
          <div class="flex items-center gap-2 mb-1 flex-wrap">
            <span :class="['text-xs font-semibold px-2.5 py-0.5 rounded-full border capitalize', STAGE_BADGE[card.stage] ?? 'bg-slate-700 text-slate-300 border-slate-600']">
              {{ card.stage }}
            </span>
          </div>
          <h2 class="text-base font-bold text-slate-100 leading-snug">{{ card.title || 'Untitled Position' }}</h2>
          <p class="text-sm text-slate-400 mt-0.5">
            {{ card.company }}<span v-if="card.location" class="text-slate-500"> · {{ card.location }}</span>
          </p>
        </div>
        <button @click="emit('close')"
          class="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg text-slate-500 hover:text-slate-200 hover:bg-slate-800 transition">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="flex-1 px-5 py-5 space-y-5">

        <!-- Quick actions -->
        <div class="flex items-center gap-2">
          <a v-if="card.url" :href="card.url" target="_blank"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm border border-slate-700 rounded-lg text-indigo-400 hover:bg-slate-800 hover:border-slate-600 transition font-medium">
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
            </svg>
            View Posting
          </a>
          <button @click="deleteCard"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm border border-slate-700 rounded-lg text-red-400 hover:bg-red-900/20 hover:border-red-700/60 transition ml-auto font-medium">
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
            Remove
          </button>
        </div>

        <!-- Description -->
        <div v-if="card.description" class="rounded-xl bg-slate-800 border border-slate-700/60 p-4">
          <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Job Description</h3>
          <p class="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
            {{ showFullDesc ? card.description : card.description.slice(0, descLimit) }}
          </p>
          <button v-if="card.description.length > descLimit"
            @click="showFullDesc = !showFullDesc"
            class="text-indigo-400 hover:text-indigo-300 text-xs font-medium mt-2 transition">
            {{ showFullDesc ? '↑ Show less' : '↓ Read more' }}
          </button>
        </div>

        <!-- Notes -->
        <div>
          <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">My Notes</h3>
          <textarea v-model="notes" @blur="saveNotes" rows="3"
            placeholder="Add notes, contacts, follow-up reminders…"
            class="w-full rounded-xl border-slate-600 bg-slate-800 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm resize-none transition" />
          <div class="flex items-center justify-between mt-1.5">
            <p class="text-xs text-slate-600">Auto-saved on blur</p>
            <span v-if="notesSaved" class="text-xs text-emerald-400 font-medium">✓ Saved</span>
          </div>
        </div>

        <!-- Divider -->
        <div class="border-t border-slate-700/60"></div>

        <!-- Generate Kit -->
        <GenerateKitPanel :card-id="card.id" :job-title="card.title || ''" :company="card.company || ''" />
      </div>
    </div>
  </div>
</template>
