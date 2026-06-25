<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import RichTextEditor from '@/components/RichTextEditor.vue'
import { useInterviewerStore } from '@/stores/interviewer'
import { useRouter } from 'vue-router'

const store = useInterviewerStore()
const router = useRouter()

// ── Create ────────────────────────────────────────────────────────────────────

const showCreate = ref(false)
const newTitle    = ref('')
const newDesc     = ref('')
const newLocation = ref('')
const creating    = ref(false)
const createFormatState = ref<'idle' | 'formatting'>('idle')

// ── Edit ──────────────────────────────────────────────────────────────────────

const editingId   = ref<number | null>(null)
const editTitle   = ref('')
const editDesc    = ref('')
const editLocation = ref('')
const saving      = ref(false)
const editFormatState = ref<'idle' | 'formatting'>('idle')

onMounted(() => store.fetchProjects())

async function handleFormatRequest(text: string, target: 'create' | 'edit') {
  if (!text.trim()) return
  const stateRef = target === 'create' ? createFormatState : editFormatState
  const descRef  = target === 'create' ? newDesc : editDesc
  stateRef.value = 'formatting'
  try {
    descRef.value = await store.formatJd(text)
  } catch {
    // silently fall back — user keeps their plain-text paste
  } finally {
    stateRef.value = 'idle'
  }
}

async function createProject() {
  if (!newTitle.value.trim()) return
  creating.value = true
  try {
    const p = await store.createProject(
      newTitle.value.trim(),
      newDesc.value || undefined,
      newLocation.value.trim() || undefined,
    )
    newTitle.value    = ''
    newDesc.value     = ''
    newLocation.value = ''
    showCreate.value  = false
    router.push(`/interviewer/projects/${p.id}`)
  } finally {
    creating.value = false
  }
}

function startEdit(p: { id: number; title: string; description?: string | null; location?: string | null }) {
  editingId.value    = p.id
  editTitle.value    = p.title
  editDesc.value     = p.description || ''
  editLocation.value = p.location || ''
}

async function saveEdit() {
  if (!editTitle.value.trim() || editingId.value === null) return
  saving.value = true
  try {
    await store.updateProject(
      editingId.value,
      editTitle.value.trim(),
      editDesc.value || undefined,
      editLocation.value.trim() || undefined,
    )
    editingId.value = null
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="flex flex-col h-screen bg-slate-900">
    <Navbar />
    <div class="flex-1 overflow-y-auto px-4 sm:px-6 py-4 sm:py-6 pb-24 sm:pb-6">
      <div class="max-w-3xl mx-auto">

        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-xl sm:text-2xl font-semibold text-slate-100">Hiring Projects</h1>
          <button @click="showCreate = !showCreate"
            class="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            New Project
          </button>
        </div>

        <!-- Create form -->
        <div v-if="showCreate" class="bg-slate-800 border border-slate-700/60 rounded-xl p-4 sm:p-6 mb-6 space-y-3">
          <h2 class="text-sm font-semibold text-slate-200">New Hiring Project</h2>

          <!-- Title + Location row -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1">Role title <span class="text-red-400">*</span></label>
              <input v-model="newTitle" type="text" placeholder="e.g. Senior Backend Engineer"
                class="w-full rounded-lg border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1">Location</label>
              <input v-model="newLocation" type="text" placeholder="e.g. Remote · US · London"
                class="w-full rounded-lg border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm" />
            </div>
          </div>

          <!-- Job description rich editor -->
          <div>
            <label class="block text-xs font-medium text-slate-400 mb-1">Job description</label>
            <p class="text-xs text-slate-500 mb-2">Paste a job description — AI will format it automatically. You can also edit and format manually.</p>
            <RichTextEditor
              v-model="newDesc"
              :formatting="true"
              :format-state="createFormatState"
              placeholder="Paste or type a job description…"
              @format-request="handleFormatRequest($event, 'create')"
            />
          </div>

          <div class="flex gap-2 pt-1">
            <button @click="createProject" :disabled="!newTitle.trim() || creating"
              class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-lg text-sm font-medium transition">
              {{ creating ? 'Creating…' : 'Create' }}
            </button>
            <button @click="showCreate = false"
              class="px-4 py-2 border border-slate-600 hover:bg-slate-700 rounded-lg text-sm text-slate-400 transition">
              Cancel
            </button>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="store.loading" class="text-center py-16 text-slate-500">Loading…</div>

        <!-- Empty state -->
        <div v-else-if="store.projects.length === 0" class="text-center py-16">
          <div class="text-4xl mb-3">🗂️</div>
          <p class="font-medium text-slate-400">No hiring projects yet</p>
          <p class="text-sm mt-1 text-slate-500">Create a project for each open role to track candidates.</p>
        </div>

        <!-- Projects list -->
        <div v-else class="space-y-3">
          <div v-for="p in store.projects" :key="p.id"
            class="bg-slate-800 border border-slate-700/60 rounded-xl overflow-hidden hover:border-slate-600 transition">

            <!-- Edit mode -->
            <div v-if="editingId === p.id" class="p-4 sm:p-5 space-y-3">
              <h2 class="text-sm font-semibold text-slate-200">Edit Project</h2>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-medium text-slate-400 mb-1">Role title</label>
                  <input v-model="editTitle" type="text" placeholder="Project title"
                    class="w-full rounded-lg border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-slate-400 mb-1">Location</label>
                  <input v-model="editLocation" type="text" placeholder="e.g. Remote · US · London"
                    class="w-full rounded-lg border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm" />
                </div>
              </div>

              <div>
                <label class="block text-xs font-medium text-slate-400 mb-1">Job description</label>
                <RichTextEditor
                  v-model="editDesc"
                  :formatting="true"
                  :format-state="editFormatState"
                  placeholder="Paste or type a job description…"
                  @format-request="handleFormatRequest($event, 'edit')"
                />
              </div>

              <div class="flex gap-2">
                <button @click="saveEdit" :disabled="!editTitle.trim() || saving"
                  class="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-lg text-sm font-medium transition">
                  {{ saving ? 'Saving…' : 'Save' }}
                </button>
                <button @click="editingId = null"
                  class="px-4 py-1.5 border border-slate-600 hover:bg-slate-700 rounded-lg text-sm text-slate-400 transition">
                  Cancel
                </button>
              </div>
            </div>

            <!-- View mode -->
            <div v-else class="p-4 sm:p-5 cursor-pointer group" @click="router.push(`/interviewer/projects/${p.id}`)">
              <div class="flex items-start justify-between gap-3">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <h3 class="font-semibold text-slate-100 truncate group-hover:text-indigo-400 transition">{{ p.title }}</h3>
                    <span v-if="p.is_owner === false"
                      class="flex-shrink-0 text-[10px] px-1.5 py-0.5 rounded bg-violet-900/30 text-violet-400 border border-violet-700/40 font-semibold">
                      shared
                    </span>
                  </div>
                  <!-- Location badge -->
                  <div v-if="p.location" class="flex items-center gap-1 mt-1">
                    <svg class="h-3 w-3 text-slate-500 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z"/>
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z"/>
                    </svg>
                    <span class="text-xs text-slate-500">{{ p.location }}</span>
                  </div>
                  <!-- JD preview (strip HTML tags) -->
                  <p v-if="p.description"
                    class="text-sm text-slate-500 mt-1 line-clamp-2"
                    v-html="p.description.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()">
                  </p>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                  <span class="text-sm text-slate-500">
                    {{ p.candidate_count }} {{ p.candidate_count === 1 ? 'candidate' : 'candidates' }}
                  </span>
                  <template v-if="p.is_owner !== false">
                    <button @click.stop="startEdit(p)"
                      class="text-slate-600 hover:text-slate-300 transition p-1">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round"
                          d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                      </svg>
                    </button>
                    <button @click.stop="store.deleteProject(p.id)"
                      class="text-slate-600 hover:text-red-400 transition p-1">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round"
                          d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                      </svg>
                    </button>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
