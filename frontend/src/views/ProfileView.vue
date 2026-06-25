<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { useProfileStore } from '@/stores/profile'

const store = useProfileStore()
const fileInput = ref<HTMLInputElement>()
const name = ref('')
const linkedinUrl = ref('')
const location = ref('')
const profileSummary = ref('')
const skillsText = ref('')
const successMsg = ref('')

onMounted(async () => {
  await store.fetchProfile()
  name.value = store.profile?.name || ''
  linkedinUrl.value = store.profile?.profile?.linkedin_url || ''
  location.value = store.profile?.profile?.location || ''
  profileSummary.value = store.profile?.profile?.profile_summary || ''
  skillsText.value = (store.profile?.profile?.skills || []).join(', ')
})

async function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) await store.uploadResume(file)
}

async function saveProfile() {
  const skills = skillsText.value.split(',').map(s => s.trim()).filter(Boolean)
  await store.update({
    name: name.value,
    linkedinUrl: linkedinUrl.value,
    location: location.value,
    profileSummary: profileSummary.value,
    skills,
  })
  successMsg.value = 'Profile saved!'
  setTimeout(() => (successMsg.value = ''), 3000)
}

async function analyze() {
  await store.analyze()
  profileSummary.value = store.profile?.profile?.profile_summary || ''
  skillsText.value = (store.profile?.profile?.skills || []).join(', ')
  successMsg.value = 'Profile analyzed — review and save any edits below.'
  setTimeout(() => (successMsg.value = ''), 4000)
}
</script>

<template>
  <div class="flex flex-col h-screen">
    <Navbar />
    <div class="flex-1 overflow-y-auto px-4 sm:px-6 py-4 sm:py-6 pb-24 sm:pb-6">
      <div class="max-w-2xl mx-auto space-y-4 sm:space-y-6">
        <h1 class="text-xl sm:text-2xl font-semibold text-gray-800">My Profile</h1>

        <!-- Basic Info -->
        <div class="bg-white rounded-xl border border-gray-200 p-4 sm:p-6 space-y-4">
          <h2 class="text-base font-semibold text-gray-700">Basic Information</h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-600 mb-1">Full Name</label>
              <input v-model="name" type="text"
                class="w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-sm" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-600 mb-1">Country / Location</label>
              <input v-model="location" type="text" placeholder="e.g. United States, India, Remote"
                class="w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-sm" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">LinkedIn URL</label>
            <input v-model="linkedinUrl" type="url" placeholder="https://linkedin.com/in/yourname"
              class="w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-sm" />
          </div>
        </div>

        <!-- Resume Upload -->
        <div class="bg-white rounded-xl border border-gray-200 p-4 sm:p-6 space-y-4">
          <h2 class="text-base font-semibold text-gray-700">Resume</h2>
          <div v-if="store.profile?.profile?.resume_path"
            class="text-sm text-emerald-600 bg-emerald-50 px-3 py-2 rounded-lg">
            ✓ Resume uploaded
          </div>
          <div class="flex flex-col sm:flex-row gap-3">
            <input ref="fileInput" type="file" accept=".pdf,.doc,.docx" class="hidden" @change="onFileChange" />
            <button @click="fileInput?.click()" :disabled="store.uploading"
              class="flex-1 sm:flex-none px-4 py-2 border border-gray-300 hover:bg-gray-50 rounded-lg text-sm font-medium text-gray-700 transition disabled:opacity-50">
              {{ store.uploading ? 'Uploading…' : '📎 Upload Resume' }}
            </button>
            <button @click="analyze" :disabled="store.analyzing || !store.profile?.profile?.resume_path"
              class="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-700 disabled:opacity-40 text-white rounded-lg text-sm font-medium transition">
              <svg v-if="store.analyzing" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              {{ store.analyzing ? 'Analyzing…' : '🤖 Analyze Resume' }}
            </button>
          </div>
        </div>

        <!-- AI Summary + Skills -->
        <div class="bg-white rounded-xl border border-gray-200 p-4 sm:p-6 space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-semibold text-gray-700">Profile Summary</h2>
            <span class="text-xs text-gray-400">Auto-filled by AI · edit freely</span>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Summary</label>
            <textarea v-model="profileSummary" rows="5" placeholder="Describe your background, expertise, and career goals…"
              class="w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-sm resize-y" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">
              Skills <span class="font-normal text-gray-400 ml-1">(comma-separated)</span>
            </label>
            <input v-model="skillsText" type="text" placeholder="Python, Azure DevOps, Kubernetes, Terraform…"
              class="w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-sm" />
            <div v-if="skillsText" class="flex flex-wrap gap-1.5 mt-2">
              <span v-for="s in skillsText.split(',').map(x => x.trim()).filter(Boolean)" :key="s"
                class="px-2.5 py-0.5 bg-indigo-50 text-indigo-700 rounded-full text-xs font-medium">
                {{ s }}
              </span>
            </div>
          </div>
        </div>

        <!-- Save -->
        <div class="flex items-center gap-4 pb-6">
          <button @click="saveProfile"
            class="w-full sm:w-auto px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold transition">
            Save Profile
          </button>
          <p v-if="successMsg" class="text-emerald-600 text-sm font-medium">✓ {{ successMsg }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
