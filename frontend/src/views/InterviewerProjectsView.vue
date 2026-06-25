<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { useInterviewerStore } from '@/stores/interviewer'
import { useRouter } from 'vue-router'

const store = useInterviewerStore()
const router = useRouter()

const showCreate = ref(false)
const newTitle = ref('')
const newDesc = ref('')
const creating = ref(false)

onMounted(() => store.fetchProjects())

async function createProject() {
  if (!newTitle.value.trim()) return
  creating.value = true
  try {
    const p = await store.createProject(newTitle.value.trim(), newDesc.value.trim() || undefined)
    newTitle.value = ''
    newDesc.value = ''
    showCreate.value = false
    router.push(`/interviewer/projects/${p.id}`)
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <div class="flex flex-col h-screen">
    <Navbar />
    <div class="flex-1 overflow-y-auto px-4 sm:px-6 py-4 sm:py-6 pb-24 sm:pb-6">
      <div class="max-w-3xl mx-auto">

        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-xl sm:text-2xl font-semibold text-gray-800">Hiring Projects</h1>
          <button @click="showCreate = !showCreate"
            class="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            New Project
          </button>
        </div>

        <!-- Create form -->
        <div v-if="showCreate" class="bg-white border border-gray-200 rounded-xl p-4 sm:p-6 mb-6 space-y-3">
          <h2 class="text-sm font-semibold text-gray-700">New Hiring Project</h2>
          <input v-model="newTitle" type="text" placeholder="e.g. Senior Backend Engineer"
            class="w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-sm" />
          <textarea v-model="newDesc" rows="2" placeholder="Optional: describe the role or requirements…"
            class="w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-sm resize-none" />
          <div class="flex gap-2">
            <button @click="createProject" :disabled="!newTitle.trim() || creating"
              class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white rounded-lg text-sm font-medium transition">
              {{ creating ? 'Creating…' : 'Create' }}
            </button>
            <button @click="showCreate = false"
              class="px-4 py-2 border border-gray-300 hover:bg-gray-50 rounded-lg text-sm text-gray-700 transition">
              Cancel
            </button>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="store.loading" class="text-center py-16 text-gray-400">Loading…</div>

        <!-- Empty state -->
        <div v-else-if="store.projects.length === 0"
          class="text-center py-16 text-gray-400">
          <div class="text-4xl mb-3">🗂️</div>
          <p class="font-medium text-gray-600">No hiring projects yet</p>
          <p class="text-sm mt-1">Create a project for each open role to track candidates.</p>
        </div>

        <!-- Projects list -->
        <div v-else class="space-y-3">
          <div v-for="p in store.projects" :key="p.id"
            class="bg-white border border-gray-200 rounded-xl p-4 sm:p-5 hover:border-indigo-300 hover:shadow-sm transition cursor-pointer"
            @click="router.push(`/interviewer/projects/${p.id}`)">
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <h3 class="font-semibold text-gray-900 truncate">{{ p.title }}</h3>
                <p v-if="p.description" class="text-sm text-gray-500 mt-0.5 line-clamp-2">{{ p.description }}</p>
              </div>
              <div class="flex items-center gap-3 shrink-0">
                <span class="text-sm text-gray-500">
                  {{ p.candidate_count }} {{ p.candidate_count === 1 ? 'candidate' : 'candidates' }}
                </span>
                <button @click.stop="store.deleteProject(p.id)"
                  class="text-gray-300 hover:text-red-500 transition">
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round"
                      d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
