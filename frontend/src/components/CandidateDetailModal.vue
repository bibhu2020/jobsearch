<script setup lang="ts">
import { ref, computed } from 'vue'
import { useInterviewerStore, type Candidate } from '@/stores/interviewer'

const props = defineProps<{
  candidate: Candidate
  projectId: number
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'updated'): void
}>()

const store = useInterviewerStore()
const fileInput = ref<HTMLInputElement>()
const notes = ref(props.candidate.notes ?? '')
const jobDescription = ref('')
const showScanOptions = ref(false)
const savingNotes = ref(false)
const notesSaved = ref(false)

const rec = computed(() => props.candidate.ai_recommendation)
const recLabel: Record<string, string> = {
  strong_yes: 'Strong Yes', yes: 'Yes', consider: 'Consider', no: 'No',
}
const recColor: Record<string, string> = {
  strong_yes: 'bg-emerald-100 text-emerald-700',
  yes: 'bg-green-100 text-green-700',
  consider: 'bg-yellow-100 text-yellow-700',
  no: 'bg-red-100 text-red-700',
}

async function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  await store.uploadResume(props.projectId, props.candidate.id, file)
  emit('updated')
}

async function scan() {
  await store.scanResume(props.projectId, props.candidate.id, jobDescription.value || undefined)
  showScanOptions.value = false
  emit('updated')
}

async function saveNotes() {
  savingNotes.value = true
  try {
    await store.updateNotes(props.projectId, props.candidate.id, notes.value)
    notesSaved.value = true
    setTimeout(() => (notesSaved.value = false), 2000)
    emit('updated')
  } finally {
    savingNotes.value = false
  }
}

async function removeCandidate() {
  if (!confirm(`Remove ${props.candidate.name} from this project?`)) return
  await store.deleteCandidate(props.projectId, props.candidate.id)
  emit('close')
  emit('updated')
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4"
    @click.self="emit('close')">
    <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="emit('close')" />

    <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">

      <!-- Header -->
      <div class="flex items-start justify-between p-5 border-b border-gray-100">
        <div class="flex-1 min-w-0">
          <h2 class="text-lg font-semibold text-gray-900 truncate">{{ candidate.name }}</h2>
          <p v-if="candidate.email" class="text-sm text-gray-500 mt-0.5">{{ candidate.email }}</p>
        </div>
        <div class="flex items-center gap-2 ml-3 shrink-0">
          <button @click="removeCandidate"
            class="text-gray-300 hover:text-red-500 transition p-1">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
          </button>
          <button @click="emit('close')" class="text-gray-400 hover:text-gray-700 p-1 transition">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Body (scrollable) -->
      <div class="flex-1 overflow-y-auto p-5 space-y-5">

        <!-- Stage badge -->
        <div class="flex items-center gap-2">
          <span class="text-xs text-gray-500 font-medium uppercase tracking-wide">Stage</span>
          <span class="px-2.5 py-0.5 bg-indigo-50 text-indigo-700 rounded-full text-xs font-semibold capitalize">
            {{ candidate.stage }}
          </span>
        </div>

        <!-- AI Score panel -->
        <div v-if="candidate.ai_score > 0 || candidate.ai_summary"
          class="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-4 space-y-3 border border-indigo-100">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-semibold text-gray-700">AI Assessment</h3>
            <div class="flex items-center gap-2">
              <div class="flex-1 w-24 bg-white rounded-full h-2 border border-indigo-100">
                <div class="bg-indigo-500 h-2 rounded-full transition-all"
                  :style="{ width: candidate.ai_score + '%' }" />
              </div>
              <span class="text-sm font-bold text-indigo-700">{{ candidate.ai_score }}/100</span>
            </div>
          </div>

          <p v-if="candidate.ai_summary" class="text-sm text-gray-700 leading-relaxed">
            {{ candidate.ai_summary }}
          </p>

          <div v-if="rec" :class="['text-xs px-2 py-1 rounded-full font-semibold w-fit border', recColor[rec]]">
            Recommendation: {{ recLabel[rec] ?? rec }}
          </div>

          <div v-if="candidate.ai_matching?.length" class="space-y-1">
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Strengths</p>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="m in candidate.ai_matching" :key="m"
                class="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-xs rounded-full border border-emerald-100">
                ✓ {{ m }}
              </span>
            </div>
          </div>

          <div v-if="candidate.ai_gaps?.length" class="space-y-1">
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Gaps</p>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="g in candidate.ai_gaps" :key="g"
                class="px-2 py-0.5 bg-red-50 text-red-600 text-xs rounded-full border border-red-100">
                ✗ {{ g }}
              </span>
            </div>
          </div>
        </div>

        <!-- No AI scan yet -->
        <div v-else class="bg-gray-50 rounded-xl p-4 border border-gray-200 text-center text-sm text-gray-400">
          No AI assessment yet. Upload a resume and scan to get an instant evaluation.
        </div>

        <!-- Resume actions -->
        <div class="space-y-2">
          <h3 class="text-sm font-semibold text-gray-700">Resume</h3>
          <div v-if="candidate.resume_path"
            class="text-xs text-emerald-600 bg-emerald-50 px-3 py-2 rounded-lg border border-emerald-100">
            ✓ Resume uploaded
          </div>
          <div class="flex flex-wrap gap-2">
            <input ref="fileInput" type="file" accept=".pdf,.doc,.docx" class="hidden" @change="onFileChange" />
            <button @click="fileInput?.click()" :disabled="store.uploading"
              class="px-3 py-1.5 border border-gray-300 hover:bg-gray-50 rounded-lg text-xs font-medium text-gray-700 transition disabled:opacity-50">
              {{ store.uploading ? 'Uploading…' : '📎 Upload Resume' }}
            </button>
            <button @click="showScanOptions = !showScanOptions"
              :disabled="!candidate.resume_text && !candidate.resume_path || store.scanning"
              class="px-3 py-1.5 bg-violet-600 hover:bg-violet-700 disabled:opacity-40 text-white rounded-lg text-xs font-medium transition flex items-center gap-1.5">
              <svg v-if="store.scanning" class="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              {{ store.scanning ? 'Scanning…' : '🤖 AI Scan' }}
            </button>
          </div>

          <!-- Scan options -->
          <div v-if="showScanOptions" class="bg-violet-50 rounded-lg p-3 border border-violet-100 space-y-2">
            <p class="text-xs text-violet-700 font-medium">Optional: paste job description for a better match score</p>
            <textarea v-model="jobDescription" rows="3"
              placeholder="Paste the job description here…"
              class="w-full rounded-lg border-violet-200 focus:border-violet-500 focus:ring-violet-500 text-xs resize-none" />
            <div class="flex gap-2">
              <button @click="scan" :disabled="store.scanning"
                class="px-3 py-1.5 bg-violet-600 hover:bg-violet-700 disabled:opacity-40 text-white rounded-lg text-xs font-medium transition">
                {{ store.scanning ? 'Scanning…' : 'Run Scan' }}
              </button>
              <button @click="showScanOptions = false"
                class="px-3 py-1.5 border border-violet-200 hover:bg-violet-50 text-violet-700 rounded-lg text-xs transition">
                Cancel
              </button>
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div class="space-y-2">
          <h3 class="text-sm font-semibold text-gray-700">Notes</h3>
          <textarea v-model="notes" rows="4" placeholder="Interview notes, impressions, follow-up items…"
            class="w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-sm resize-y" />
          <div class="flex items-center gap-3">
            <button @click="saveNotes" :disabled="savingNotes"
              class="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white rounded-lg text-xs font-medium transition">
              {{ savingNotes ? 'Saving…' : 'Save Notes' }}
            </button>
            <span v-if="notesSaved" class="text-xs text-emerald-600">✓ Saved</span>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
