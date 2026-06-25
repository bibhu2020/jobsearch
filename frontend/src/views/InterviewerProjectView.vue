<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import CandidateDetailModal from '@/components/CandidateDetailModal.vue'
import { useInterviewerStore, type Candidate } from '@/stores/interviewer'

const route = useRoute()
const router = useRouter()
const store = useInterviewerStore()

const projectId = computed(() => parseInt(route.params.id as string))
const showAdd = ref(false)
const adding = ref(false)
const newName = ref('')
const newEmail = ref('')
const newResumeText = ref('')
const selectedCandidate = ref<Candidate | null>(null)

const STAGES = [
  { key: 'applied',   label: 'Applied',   color: 'blue'   },
  { key: 'screening', label: 'Screening', color: 'yellow' },
  { key: 'interview', label: 'Interview', color: 'purple' },
  { key: 'offer',     label: 'Offer',     color: 'green'  },
  { key: 'rejected',  label: 'Rejected',  color: 'red'    },
]

const STAGE_COLORS: Record<string, string> = {
  blue:   'bg-blue-50   border-blue-200  text-blue-700',
  yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700',
  purple: 'bg-purple-50 border-purple-200 text-purple-700',
  green:  'bg-green-50  border-green-200  text-green-700',
  red:    'bg-red-50    border-red-200    text-red-700',
}

function cardsForStage(stage: string) {
  return (store.currentProject?.cards ?? [])
    .filter(c => c.stage === stage)
    .sort((a, b) => a.position - b.position)
}

onMounted(() => store.fetchProject(projectId.value))

async function addCandidate() {
  if (!newName.value.trim()) return
  adding.value = true
  try {
    await store.addCandidate(
      projectId.value,
      newName.value.trim(),
      newEmail.value.trim() || undefined,
      newResumeText.value.trim() || undefined,
    )
    newName.value = ''
    newEmail.value = ''
    newResumeText.value = ''
    showAdd.value = false
  } finally {
    adding.value = false
  }
}

function recommendationLabel(rec: string) {
  const map: Record<string, string> = {
    strong_yes: 'Strong Yes',
    yes: 'Yes',
    consider: 'Consider',
    no: 'No',
  }
  return map[rec] ?? rec
}

function recommendationColor(rec: string) {
  const map: Record<string, string> = {
    strong_yes: 'bg-emerald-100 text-emerald-700',
    yes: 'bg-green-100 text-green-700',
    consider: 'bg-yellow-100 text-yellow-700',
    no: 'bg-red-100 text-red-700',
  }
  return map[rec] ?? 'bg-gray-100 text-gray-600'
}

async function onMoveCard(candidate: Candidate, stage: string, stageCards: Candidate[]) {
  const position = stageCards.length
  await store.moveCard(candidate.card_id, stage, position)
}

function openCandidate(c: Candidate) {
  selectedCandidate.value = c
}

async function onCandidateUpdated() {
  await store.fetchProject(projectId.value)
  if (selectedCandidate.value) {
    const updated = store.currentProject?.cards?.find(c => c.id === selectedCandidate.value!.id)
    if (updated) selectedCandidate.value = updated
  }
}
</script>

<template>
  <div class="flex flex-col h-screen">
    <Navbar />

    <div class="flex-1 overflow-hidden flex flex-col">

      <!-- Sub-header -->
      <div class="bg-white border-b border-gray-200 px-4 sm:px-6 py-3 flex items-center gap-3">
        <button @click="router.push('/interviewer')"
          class="text-gray-400 hover:text-gray-700 transition">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
        </button>
        <h1 class="text-base font-semibold text-gray-800 truncate flex-1">
          {{ store.currentProject?.title ?? 'Loading…' }}
        </h1>
        <button @click="showAdd = !showAdd"
          class="flex items-center gap-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          <span class="hidden sm:inline">Add Candidate</span>
        </button>
      </div>

      <!-- Add candidate form -->
      <div v-if="showAdd" class="bg-indigo-50 border-b border-indigo-100 px-4 sm:px-6 py-4">
        <div class="max-w-2xl space-y-3">
          <h2 class="text-sm font-semibold text-gray-700">Add Candidate</h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input v-model="newName" type="text" placeholder="Full name *"
              class="rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-sm" />
            <input v-model="newEmail" type="email" placeholder="Email (optional)"
              class="rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-sm" />
          </div>
          <textarea v-model="newResumeText" rows="3"
            placeholder="Paste resume text (optional — you can upload a file after adding)"
            class="w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-sm resize-none" />
          <div class="flex gap-2">
            <button @click="addCandidate" :disabled="!newName.trim() || adding"
              class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white rounded-lg text-sm font-medium transition">
              {{ adding ? 'Adding…' : 'Add' }}
            </button>
            <button @click="showAdd = false"
              class="px-4 py-2 border border-gray-300 hover:bg-gray-50 rounded-lg text-sm text-gray-700 transition">
              Cancel
            </button>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="store.loading" class="flex-1 flex items-center justify-center text-gray-400">
        Loading…
      </div>

      <!-- Kanban board -->
      <div v-else class="flex-1 overflow-x-auto pb-24 sm:pb-4">
        <div class="flex gap-3 h-full p-4 sm:p-6 min-w-max">

          <div v-for="col in STAGES" :key="col.key"
            class="flex flex-col w-56 sm:w-64 shrink-0 bg-gray-50 rounded-xl border border-gray-200">

            <!-- Column header -->
            <div class="px-3 py-2.5 border-b border-gray-200 flex items-center justify-between">
              <span :class="['px-2 py-0.5 rounded-full text-xs font-semibold border', STAGE_COLORS[col.color]]">
                {{ col.label }}
              </span>
              <span class="text-xs text-gray-400">{{ cardsForStage(col.key).length }}</span>
            </div>

            <!-- Cards -->
            <div class="flex-1 overflow-y-auto p-2 space-y-2">
              <div v-for="card in cardsForStage(col.key)" :key="card.card_id"
                class="bg-white rounded-lg border border-gray-200 p-3 shadow-sm hover:shadow-md hover:border-indigo-300 transition cursor-pointer group"
                @click="openCandidate(card)">
                <div class="font-medium text-sm text-gray-900 truncate">{{ card.name }}</div>
                <div v-if="card.email" class="text-xs text-gray-400 truncate mt-0.5">{{ card.email }}</div>

                <div v-if="card.ai_score > 0" class="flex items-center gap-2 mt-2">
                  <div class="flex-1 bg-gray-100 rounded-full h-1.5">
                    <div class="bg-indigo-500 h-1.5 rounded-full"
                      :style="{ width: card.ai_score + '%' }" />
                  </div>
                  <span class="text-xs text-gray-500">{{ card.ai_score }}</span>
                </div>

                <div v-if="card.ai_recommendation && card.ai_recommendation !== 'consider'"
                  :class="['mt-2 text-xs px-1.5 py-0.5 rounded font-medium w-fit', recommendationColor(card.ai_recommendation)]">
                  {{ recommendationLabel(card.ai_recommendation) }}
                </div>

                <!-- Move buttons -->
                <div class="hidden group-hover:flex gap-1 mt-2 pt-2 border-t border-gray-100">
                  <button v-for="s in STAGES.filter(s => s.key !== col.key)" :key="s.key"
                    @click.stop="onMoveCard(card, s.key, cardsForStage(s.key))"
                    :class="['flex-1 text-[10px] py-0.5 rounded border transition', STAGE_COLORS[s.color], 'hover:opacity-80']">
                    → {{ s.label }}
                  </button>
                </div>
              </div>

              <!-- Empty column -->
              <div v-if="cardsForStage(col.key).length === 0"
                class="text-center py-6 text-gray-300 text-xs">
                Drop candidates here
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>

    <!-- Candidate detail modal -->
    <CandidateDetailModal
      v-if="selectedCandidate"
      :candidate="selectedCandidate"
      :project-id="projectId"
      @close="selectedCandidate = null"
      @updated="onCandidateUpdated"
    />
  </div>
</template>
