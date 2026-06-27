<script setup lang="ts">
import { ref, computed, reactive, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { VueDraggable } from 'vue-draggable-plus'
import Navbar from '@/components/Navbar.vue'
import CandidateDetailModal from '@/components/CandidateDetailModal.vue'
import { useInterviewerStore, type Candidate, type ProjectMember } from '@/stores/interviewer'

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

// ── Resume drag-and-drop ───────────────────────────────────────────────────────

const fileDragCounter = reactive<Record<string, number>>({
  applied: 0, screening: 0, interview: 0, offer: 0, rejected: 0,
})
const columnUploading = reactive<Record<string, boolean>>({
  applied: false, screening: false, interview: false, offer: false, rejected: false,
})
const dropError = ref('')

function isFileDrag(e: DragEvent) {
  return e.dataTransfer?.types.includes('Files') ?? false
}

function onDragEnter(stageKey: string, e: DragEvent) {
  if (isFileDrag(e)) fileDragCounter[stageKey]++
}

function onDragLeave(stageKey: string, e: DragEvent) {
  if (isFileDrag(e)) fileDragCounter[stageKey] = Math.max(0, fileDragCounter[stageKey] - 1)
}

function onDragOver(stageKey: string, e: DragEvent) {
  if (isFileDrag(e)) {
    e.preventDefault()
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy'
  }
}

async function onFileDrop(stageKey: string, e: DragEvent) {
  fileDragCounter[stageKey] = 0
  if (!isFileDrag(e)) return
  e.preventDefault()
  dropError.value = ''

  const file = e.dataTransfer?.files[0]
  if (!file) return

  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  if (!['pdf', 'doc', 'docx'].includes(ext)) {
    dropError.value = 'Only PDF, DOC, and DOCX files are supported.'
    setTimeout(() => { dropError.value = '' }, 4000)
    return
  }

  columnUploading[stageKey] = true
  try {
    await store.addCandidateFromResume(projectId.value, stageKey, file)
  } catch (err: any) {
    dropError.value = err.response?.data?.message || 'Failed to extract resume.'
    setTimeout(() => { dropError.value = '' }, 4000)
  } finally {
    columnUploading[stageKey] = false
  }
}

// ── Share / members panel ──────────────────────────────────────────────────────

const showShare = ref(false)
const members = ref<ProjectMember[]>([])
const inviteEmail = ref('')
const inviting = ref(false)
const inviteError = ref('')
const removingId = ref<number | null>(null)

const isOwner = computed(() => store.currentProject?.is_owner !== false)

async function openShare() {
  showShare.value = true
  members.value = await store.fetchMembers(projectId.value)
}

async function invite() {
  if (!inviteEmail.value.trim()) return
  inviting.value = true
  inviteError.value = ''
  try {
    members.value = await store.inviteMember(projectId.value, inviteEmail.value.trim())
    inviteEmail.value = ''
  } catch (e: any) {
    inviteError.value = e.response?.data?.message || 'Failed to invite'
  } finally {
    inviting.value = false
  }
}

async function removeMember(userId: number) {
  removingId.value = userId
  try {
    members.value = await store.removeMember(projectId.value, userId)
  } finally {
    removingId.value = null
  }
}

// ── Stage definitions ──────────────────────────────────────────────────────────

const STAGES = [
  { key: 'applied',   label: 'Applied',   topBorder: 'border-t-blue-500',    dot: 'bg-blue-500'    },
  { key: 'screening', label: 'Screening', topBorder: 'border-t-yellow-500',  dot: 'bg-yellow-500'  },
  { key: 'interview', label: 'Interview', topBorder: 'border-t-purple-500',  dot: 'bg-purple-500'  },
  { key: 'offer',     label: 'Offer',     topBorder: 'border-t-emerald-500', dot: 'bg-emerald-500' },
  { key: 'rejected',  label: 'Rejected',  topBorder: 'border-t-red-400',     dot: 'bg-red-400'     },
]

// ── Reactive per-stage card lists (same pattern as KanbanBoard) ────────────────

const stageLists = reactive<Record<string, Candidate[]>>({
  applied: [], screening: [], interview: [], offer: [], rejected: [],
})

watch(
  () => store.currentProject?.cards,
  (cards) => {
    if (!cards) return
    for (const stage of STAGES) {
      const next = cards
        .filter(c => c.stage === stage.key)
        .sort((a, b) => a.position - b.position)
      stageLists[stage.key].splice(0, stageLists[stage.key].length, ...next)
    }
  },
  { immediate: true, deep: true },
)

// ── Drag-and-drop handlers (same pattern as KanbanColumn) ─────────────────────

function cardId(evt: any): number {
  return parseInt((evt.item as HTMLElement).dataset.cardId || '0')
}

function onAdd(stageKey: string, evt: any) {
  store.moveCard(cardId(evt), stageKey, evt.newIndex ?? 0)
}

function onUpdate(stageKey: string, evt: any) {
  store.moveCard(cardId(evt), stageKey, evt.newIndex ?? 0)
}

// ── Mobile stage tab scrolling ─────────────────────────────────────────────────

const boardRef = ref<HTMLElement | null>(null)
const activeStage = ref('applied')

function scrollToStage(key: string) {
  const board = boardRef.value
  if (!board) return
  const col = board.querySelector(`[data-stage="${key}"]`) as HTMLElement | null
  if (col) col.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' })
  activeStage.value = key
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

onMounted(async () => {
  await store.fetchProject(projectId.value)
  boardRef.value?.addEventListener('scroll', onScroll, { passive: true })
})
onUnmounted(() => boardRef.value?.removeEventListener('scroll', onScroll))

// ── Add candidate ──────────────────────────────────────────────────────────────

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

// ── Candidate modal ────────────────────────────────────────────────────────────

async function onCandidateUpdated() {
  await store.fetchProject(projectId.value)
  if (selectedCandidate.value) {
    const updated = store.currentProject?.cards?.find(c => c.id === selectedCandidate.value!.id)
    if (updated) selectedCandidate.value = updated
  }
}

// ── Card helpers ───────────────────────────────────────────────────────────────

const REC_LABEL: Record<string, string> = {
  strong_yes: 'Strong Yes', yes: 'Yes', consider: 'Consider', no: 'No',
}
const REC_COLOR: Record<string, string> = {
  strong_yes: 'bg-emerald-900/30 text-emerald-400 border border-emerald-700/40',
  yes:        'bg-green-900/30 text-green-400 border border-green-700/40',
  consider:   'bg-yellow-900/30 text-yellow-400 border border-yellow-700/40',
  no:         'bg-red-900/30 text-red-400 border border-red-700/40',
}

const STAGE_ACCENT: Record<string, string> = {
  applied:   'border-l-blue-500',
  screening: 'border-l-yellow-500',
  interview: 'border-l-purple-500',
  offer:     'border-l-emerald-500',
  rejected:  'border-l-red-400',
}

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const days = Math.floor(diff / 86400000)
  if (days === 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days}d ago`
  if (days < 30) return `${Math.floor(days / 7)}w ago`
  return `${Math.floor(days / 30)}mo ago`
}
</script>

<template>
  <div class="flex flex-col h-screen bg-slate-900">
    <Navbar />

    <div class="flex-1 overflow-hidden flex flex-col">

      <!-- Sub-header -->
      <div class="bg-slate-900 border-b border-slate-700/60 px-4 sm:px-6 py-3 flex items-center gap-3 flex-shrink-0">
        <button @click="router.push('/interviewer')"
          class="text-slate-500 hover:text-slate-200 transition">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
        </button>
        <h1 class="text-base font-semibold text-slate-100 truncate flex-1">
          {{ store.currentProject?.title ?? 'Loading…' }}
        </h1>
        <!-- Share button -->
        <button @click="showShare ? (showShare = false) : openShare()"
          :class="[
            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition border',
            showShare
              ? 'bg-slate-700 border-slate-600 text-slate-200'
              : 'border-slate-700 text-slate-400 hover:text-slate-200 hover:bg-slate-800',
          ]">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
          </svg>
          <span class="hidden sm:inline">Team</span>
        </button>
        <button @click="showAdd = !showAdd"
          class="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          <span class="hidden sm:inline">Add Candidate</span>
        </button>
      </div>

      <!-- Members panel -->
      <div v-if="showShare"
        class="bg-slate-800/80 border-b border-slate-700/60 px-4 sm:px-6 py-4 flex-shrink-0">
        <div class="max-w-lg space-y-3">
          <h2 class="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <svg class="h-4 w-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
            </svg>
            Team access
          </h2>

          <!-- Owner row -->
          <div class="flex items-center gap-3 py-1.5">
            <div class="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0">
              <span class="text-xs font-bold text-white">YOU</span>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-slate-200">You</p>
            </div>
            <span class="text-[10px] px-2 py-0.5 rounded bg-indigo-900/40 text-indigo-400 border border-indigo-700/40 font-semibold">owner</span>
          </div>

          <!-- Member rows -->
          <div v-for="m in members" :key="m.user_id" class="flex items-center gap-3 py-1.5">
            <div class="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
              <span class="text-xs font-bold text-slate-300">{{ (m.name || m.email)[0].toUpperCase() }}</span>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-slate-200 truncate">{{ m.name || m.email }}</p>
              <p class="text-xs text-slate-500 truncate">{{ m.email }}</p>
            </div>
            <span class="text-[10px] px-2 py-0.5 rounded bg-slate-700 text-slate-400 font-medium">{{ m.role }}</span>
            <button v-if="isOwner" @click="removeMember(m.user_id)"
              :disabled="removingId === m.user_id"
              class="text-slate-600 hover:text-red-400 disabled:opacity-40 transition p-1 flex-shrink-0">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <p v-if="members.length === 0 && !isOwner" class="text-xs text-slate-500">
            Only the project owner can invite teammates.
          </p>

          <!-- Invite form (owner only) -->
          <div v-if="isOwner" class="flex gap-2 pt-1">
            <input v-model="inviteEmail" type="email" placeholder="teammate@example.com"
              @keyup.enter="invite"
              class="flex-1 rounded-lg border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm" />
            <button @click="invite" :disabled="!inviteEmail.trim() || inviting"
              class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-lg text-sm font-medium transition whitespace-nowrap">
              {{ inviting ? 'Inviting…' : 'Invite' }}
            </button>
          </div>
          <p v-if="inviteError" class="text-xs text-red-400">{{ inviteError }}</p>
          <p v-if="isOwner" class="text-xs text-slate-600">
            Invited teammates can view and edit all candidates in this project.
            They must already have a Linear Lantern account.
          </p>
        </div>
      </div>

      <!-- Add candidate form -->
      <div v-if="showAdd" class="bg-indigo-900/20 border-b border-indigo-700/40 px-4 sm:px-6 py-4 flex-shrink-0">
        <div class="max-w-2xl space-y-3">
          <h2 class="text-sm font-semibold text-slate-200">Add Candidate</h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input v-model="newName" type="text" placeholder="Full name *"
              class="rounded-lg border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm" />
            <input v-model="newEmail" type="email" placeholder="Email (optional)"
              class="rounded-lg border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm" />
          </div>
          <textarea v-model="newResumeText" rows="2"
            placeholder="Paste resume text (optional — you can upload a file after adding)"
            class="w-full rounded-lg border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm resize-none" />
          <div class="flex gap-2">
            <button @click="addCandidate" :disabled="!newName.trim() || adding"
              class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-lg text-sm font-medium transition">
              {{ adding ? 'Adding…' : 'Add' }}
            </button>
            <button @click="showAdd = false"
              class="px-4 py-2 border border-slate-600 hover:bg-slate-700 rounded-lg text-sm text-slate-400 transition">
              Cancel
            </button>
          </div>
        </div>
      </div>

      <!-- Drop error toast -->
      <Transition name="drop-fade">
        <div v-if="dropError"
          class="flex-shrink-0 flex items-center gap-2 px-4 py-2.5 bg-red-900/30 border-b border-red-700/50 text-sm text-red-300">
          <svg class="h-4 w-4 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"/>
          </svg>
          {{ dropError }}
        </div>
      </Transition>

      <!-- Loading -->
      <div v-if="store.loading" class="flex-1 flex items-center justify-center text-slate-500">
        Loading…
      </div>

      <!-- Kanban board (same layout as candidate pipeline) -->
      <div v-else class="flex-1 overflow-hidden flex flex-col">

        <!-- Mobile stage tabs -->
        <div class="sm:hidden flex items-center gap-1.5 px-3 py-2 bg-slate-900 border-b border-slate-700/60 overflow-x-auto scrollbar-hide flex-shrink-0">
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
            <span :class="['w-1.5 h-1.5 rounded-full flex-shrink-0', stage.dot]"></span>
            {{ stage.label }}
            <span class="text-[10px] font-semibold tabular-nums opacity-70">{{ stageLists[stage.key].length }}</span>
          </button>
        </div>

        <!-- Board -->
        <div ref="boardRef" class="flex-1 flex gap-3 p-3 sm:gap-4 sm:p-4 overflow-x-auto snap-x snap-mandatory scrollbar-hide">

          <div v-for="col in STAGES" :key="col.key"
            class="relative flex flex-col w-[82vw] sm:w-64 flex-shrink-0 h-full min-h-0 snap-center"
            :data-stage="col.key"
            @dragenter="onDragEnter(col.key, $event)"
            @dragleave="onDragLeave(col.key, $event)"
            @dragover="onDragOver(col.key, $event)"
            @drop="onFileDrop(col.key, $event)">

            <!-- File drop overlay -->
            <Transition name="drop-fade">
              <div v-if="fileDragCounter[col.key] > 0 || columnUploading[col.key]"
                class="absolute inset-0 z-20 rounded-xl border-2 border-dashed border-indigo-500 bg-indigo-950/80 backdrop-blur-sm flex flex-col items-center justify-center gap-2 pointer-events-none">
                <template v-if="columnUploading[col.key]">
                  <svg class="animate-spin h-6 w-6 text-indigo-400" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                  </svg>
                  <p class="text-sm text-indigo-300 font-medium">Extracting resume…</p>
                </template>
                <template v-else>
                  <svg class="h-8 w-8 text-indigo-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12l-3-3m0 0l-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                  <p class="text-sm text-indigo-300 font-semibold">Drop resume here</p>
                  <p class="text-xs text-indigo-500">PDF · DOC · DOCX</p>
                </template>
              </div>
            </Transition>

            <!-- Column header -->
            <div class="flex items-center justify-between mb-2.5 px-0.5">
              <div class="flex items-center gap-2">
                <span :class="['w-2 h-2 rounded-full flex-shrink-0', col.dot]"></span>
                <h3 class="text-sm font-semibold text-slate-300">{{ col.label }}</h3>
              </div>
              <span class="text-xs font-medium bg-slate-700 text-slate-400 px-2 py-0.5 rounded-full tabular-nums">
                {{ stageLists[col.key].length }}
              </span>
            </div>

            <!--
              Card list — directly overflow-y-auto, NO overflow-hidden parent.
              Same structure as KanbanColumn to ensure cross-column drag works.
            -->
            <div :class="[
              'flex-1 min-h-0 rounded-xl border border-slate-700/60 border-t-2',
              'bg-slate-800/60 overflow-y-auto p-2 pb-20 sm:pb-2',
              col.topBorder,
            ]">
              <VueDraggable
                v-model="stageLists[col.key]"
                group="interviewer-kanban"
                :animation="150"
                ghost-class="opacity-30"
                drag-class="shadow-xl"
                class="space-y-2 min-h-full"
                @add="onAdd(col.key, $event)"
                @update="onUpdate(col.key, $event)"
              >
                <div v-for="card in stageLists[col.key]" :key="card.card_id" :data-card-id="card.card_id">
                  <div
                    :class="[
                      'bg-slate-800 rounded-lg border border-slate-700/60 border-l-4 p-3 shadow-sm',
                      'hover:shadow-md hover:border-slate-600 hover:-translate-y-px',
                      'cursor-pointer transition-all select-none group',
                      STAGE_ACCENT[col.key] || 'border-l-slate-500',
                    ]"
                    @click="selectedCandidate = card">

                    <!-- Name -->
                    <p class="text-sm font-semibold text-slate-100 leading-snug truncate group-hover:text-indigo-400 transition-colors">
                      {{ card.name }}
                    </p>

                    <!-- Email row -->
                    <div v-if="card.email" class="flex items-center gap-1.5 mt-1.5">
                      <span class="flex-shrink-0 w-4 h-4 rounded bg-slate-700 text-slate-400 text-[9px] font-bold flex items-center justify-center">
                        {{ card.email[0].toUpperCase() }}
                      </span>
                      <p class="text-xs text-slate-400 truncate">{{ card.email }}</p>
                    </div>

                    <!-- Phone + Location row -->
                    <div v-if="card.phone || card.location" class="flex items-center gap-2 mt-1">
                      <span v-if="card.phone" class="flex items-center gap-1 text-[11px] text-slate-500 truncate">
                        <svg class="h-3 w-3 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z"/>
                        </svg>
                        {{ card.phone }}
                      </span>
                      <span v-if="card.location" class="flex items-center gap-1 text-[11px] text-slate-500 truncate">
                        <svg class="h-3 w-3 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z"/>
                          <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z"/>
                        </svg>
                        {{ card.location }}
                      </span>
                    </div>

                    <!-- AI score bar -->
                    <div v-if="card.ai_score > 0" class="flex items-center gap-2 mt-2">
                      <div class="flex-1 bg-slate-700 rounded-full h-1.5">
                        <div class="bg-indigo-500 h-1.5 rounded-full transition-all"
                          :style="{ width: card.ai_score + '%' }" />
                      </div>
                      <span class="text-xs text-slate-500 tabular-nums">{{ card.ai_score }}</span>
                    </div>

                    <!-- Footer -->
                    <div class="flex items-center justify-between mt-2.5 pt-2 border-t border-slate-700/60">
                      <span v-if="card.ai_recommendation"
                        :class="['text-[10px] px-1.5 py-0.5 rounded font-semibold', REC_COLOR[card.ai_recommendation] ?? 'bg-slate-700 text-slate-400']">
                        {{ REC_LABEL[card.ai_recommendation] ?? card.ai_recommendation }}
                      </span>
                      <span v-else-if="card.resume_path" class="text-[10px] text-slate-500 flex items-center gap-1">
                        <svg class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                        CV
                      </span>
                      <span v-else class="flex-1"></span>
                      <span class="text-[11px] text-slate-500 flex-shrink-0">{{ timeAgo(card.created_at) }}</span>
                    </div>
                  </div>
                </div>
              </VueDraggable>

              <!-- Empty column hint -->
              <div v-if="stageLists[col.key].length === 0"
                class="flex flex-col items-center justify-center py-8 text-slate-600">
                <svg class="h-8 w-8 mb-2 opacity-50" fill="none" stroke="currentColor" stroke-width="1" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                <p class="text-xs text-center leading-snug">Drop here or<br/>add a candidate</p>
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

<style scoped>
.drop-fade-enter-active,
.drop-fade-leave-active {
  transition: opacity 0.15s ease;
}
.drop-fade-enter-from,
.drop-fade-leave-to {
  opacity: 0;
}
</style>
