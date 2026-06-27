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
  strong_yes: 'bg-emerald-900/30 text-emerald-400 border-emerald-700/40',
  yes:        'bg-green-900/30 text-green-400 border-green-700/40',
  consider:   'bg-yellow-900/30 text-yellow-400 border-yellow-700/40',
  no:         'bg-red-900/30 text-red-400 border-red-700/40',
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
    <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="emit('close')" />

    <div class="relative bg-slate-800 border border-slate-700/60 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">

      <!-- Header -->
      <div class="flex items-start justify-between p-5 border-b border-slate-700/60">
        <div class="flex-1 min-w-0">
          <h2 class="text-lg font-semibold text-slate-100 truncate">{{ candidate.name }}</h2>
          <div class="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-1">
            <a v-if="candidate.email" :href="`mailto:${candidate.email}`"
              class="flex items-center gap-1 text-sm text-slate-400 hover:text-indigo-400 transition truncate">
              <svg class="h-3.5 w-3.5 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"/>
              </svg>
              {{ candidate.email }}
            </a>
            <a v-if="candidate.phone" :href="`tel:${candidate.phone}`"
              class="flex items-center gap-1 text-sm text-slate-400 hover:text-indigo-400 transition">
              <svg class="h-3.5 w-3.5 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z"/>
              </svg>
              {{ candidate.phone }}
            </a>
            <span v-if="candidate.location"
              class="flex items-center gap-1 text-sm text-slate-400">
              <svg class="h-3.5 w-3.5 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z"/>
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z"/>
              </svg>
              {{ candidate.location }}
            </span>
          </div>
        </div>
        <div class="flex items-center gap-2 ml-3 shrink-0">
          <button @click="removeCandidate"
            class="text-slate-600 hover:text-red-400 transition p-1">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
          </button>
          <button @click="emit('close')" class="text-slate-500 hover:text-slate-200 p-1 transition">
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
          <span class="text-xs text-slate-500 font-medium uppercase tracking-wide">Stage</span>
          <span class="px-2.5 py-0.5 bg-indigo-900/30 text-indigo-400 border border-indigo-700/40 rounded-full text-xs font-semibold capitalize">
            {{ candidate.stage }}
          </span>
        </div>

        <!-- AI Score panel -->
        <div v-if="candidate.ai_score > 0 || candidate.ai_summary"
          class="bg-gradient-to-br from-indigo-900/30 to-purple-900/30 rounded-xl p-4 space-y-3 border border-indigo-700/40">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-semibold text-slate-200">AI Assessment</h3>
            <div class="flex items-center gap-2">
              <div class="flex-1 w-24 bg-slate-800 rounded-full h-2 border border-slate-700">
                <div class="bg-indigo-500 h-2 rounded-full transition-all"
                  :style="{ width: candidate.ai_score + '%' }" />
              </div>
              <span class="text-sm font-bold text-indigo-400">{{ candidate.ai_score }}/100</span>
            </div>
          </div>

          <p v-if="candidate.ai_summary" class="text-sm text-slate-300 leading-relaxed">
            {{ candidate.ai_summary }}
          </p>

          <div v-if="rec" :class="['text-xs px-2 py-1 rounded-full font-semibold w-fit border', recColor[rec] ?? 'bg-slate-700 text-slate-400 border-slate-600']">
            Recommendation: {{ recLabel[rec] ?? rec }}
          </div>

          <div v-if="candidate.ai_matching?.length" class="space-y-1">
            <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide">Strengths</p>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="m in candidate.ai_matching" :key="m"
                class="px-2 py-0.5 bg-emerald-900/30 text-emerald-400 text-xs rounded-full border border-emerald-700/40">
                ✓ {{ m }}
              </span>
            </div>
          </div>

          <div v-if="candidate.ai_gaps?.length" class="space-y-1">
            <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide">Gaps</p>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="g in candidate.ai_gaps" :key="g"
                class="px-2 py-0.5 bg-red-900/30 text-red-400 text-xs rounded-full border border-red-700/40">
                ✗ {{ g }}
              </span>
            </div>
          </div>
        </div>

        <!-- No AI scan yet -->
        <div v-else class="bg-slate-900/60 rounded-xl p-4 border border-slate-700/40 text-center text-sm text-slate-500">
          No AI assessment yet. Upload a resume and scan to get an instant evaluation.
        </div>

        <!-- Resume actions -->
        <div class="space-y-2">
          <h3 class="text-sm font-semibold text-slate-300">Resume</h3>
          <div v-if="candidate.resume_path"
            class="text-xs text-emerald-400 bg-emerald-900/20 px-3 py-2 rounded-lg border border-emerald-700/40">
            ✓ Resume uploaded
          </div>
          <div class="flex flex-wrap gap-2">
            <input ref="fileInput" type="file" accept=".pdf,.doc,.docx" class="hidden" @change="onFileChange" />
            <button @click="fileInput?.click()" :disabled="store.uploading"
              class="px-3 py-1.5 border border-slate-600 hover:bg-slate-700 rounded-lg text-xs font-medium text-slate-300 transition disabled:opacity-50">
              {{ store.uploading ? 'Uploading…' : '📎 Upload Resume' }}
            </button>
            <button @click="showScanOptions = !showScanOptions"
              :disabled="!candidate.resume_text && !candidate.resume_path || store.scanning"
              class="px-3 py-1.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white rounded-lg text-xs font-medium transition flex items-center gap-1.5">
              <svg v-if="store.scanning" class="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              {{ store.scanning ? 'Scanning…' : '🤖 AI Scan' }}
            </button>
          </div>

          <!-- Scan options -->
          <div v-if="showScanOptions" class="bg-violet-900/20 rounded-lg p-3 border border-violet-700/40 space-y-2">
            <p class="text-xs text-violet-300 font-medium">Optional: paste job description for a better match score</p>
            <textarea v-model="jobDescription" rows="3"
              placeholder="Paste the job description here…"
              class="w-full rounded-lg border-violet-700/60 bg-slate-800 text-slate-200 placeholder-slate-500 focus:border-violet-500 focus:ring-violet-500 text-xs resize-none" />
            <div class="flex gap-2">
              <button @click="scan" :disabled="store.scanning"
                class="px-3 py-1.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white rounded-lg text-xs font-medium transition">
                {{ store.scanning ? 'Scanning…' : 'Run Scan' }}
              </button>
              <button @click="showScanOptions = false"
                class="px-3 py-1.5 border border-violet-700/40 hover:bg-slate-700 text-violet-400 rounded-lg text-xs transition">
                Cancel
              </button>
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div class="space-y-2">
          <h3 class="text-sm font-semibold text-slate-300">Notes</h3>
          <textarea v-model="notes" rows="4" placeholder="Interview notes, impressions, follow-up items…"
            class="w-full rounded-lg border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:ring-indigo-500 text-sm resize-y" />
          <div class="flex items-center gap-3">
            <button @click="saveNotes" :disabled="savingNotes"
              class="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-lg text-xs font-medium transition">
              {{ savingNotes ? 'Saving…' : 'Save Notes' }}
            </button>
            <span v-if="notesSaved" class="text-xs text-emerald-400">✓ Saved</span>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
