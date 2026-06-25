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
  await store.update({ name: name.value, linkedinUrl: linkedinUrl.value, location: location.value, profileSummary: profileSummary.value, skills })
  successMsg.value = 'Profile saved!'
  setTimeout(() => (successMsg.value = ''), 3000)
}

async function analyze() {
  await store.analyze()
  profileSummary.value = store.profile?.profile?.profile_summary || ''
  skillsText.value = (store.profile?.profile?.skills || []).join(', ')
  successMsg.value = 'Profile analyzed — review and save any edits.'
  setTimeout(() => (successMsg.value = ''), 4000)
}

const skillList = () => skillsText.value.split(',').map(s => s.trim()).filter(Boolean)
</script>

<template>
  <div class="flex flex-col h-screen bg-slate-900">
    <Navbar />

    <div class="flex-1 overflow-y-auto">
      <div class="max-w-2xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-5 pb-24 sm:pb-8">

        <!-- Page header -->
        <div>
          <h1 class="text-xl font-bold text-slate-100">My Profile</h1>
          <p class="text-sm text-slate-500 mt-0.5">This data powers AI job matching and document generation</p>
        </div>

        <!-- Basic Info -->
        <section class="bg-slate-800 rounded-2xl border border-slate-700/60 shadow-sm overflow-hidden">
          <div class="px-5 py-4 border-b border-slate-700/60">
            <h2 class="text-sm font-semibold text-slate-100">Basic Information</h2>
          </div>
          <div class="px-5 py-5 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Full Name</label>
              <input v-model="name" type="text" placeholder="Jane Smith"
                class="w-full rounded-xl border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm transition" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Location</label>
              <input v-model="location" type="text" placeholder="United States, India, Remote…"
                class="w-full rounded-xl border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm transition" />
            </div>
            <div class="sm:col-span-2">
              <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">LinkedIn URL</label>
              <input v-model="linkedinUrl" type="url" placeholder="https://linkedin.com/in/yourname"
                class="w-full rounded-xl border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm transition" />
            </div>
          </div>
        </section>

        <!-- Resume Upload -->
        <section class="bg-slate-800 rounded-2xl border border-slate-700/60 shadow-sm overflow-hidden">
          <div class="px-5 py-4 border-b border-slate-700/60 flex items-center justify-between">
            <div>
              <h2 class="text-sm font-semibold text-slate-100">Resume</h2>
              <p class="text-xs text-slate-500 mt-0.5">PDF, DOC, or DOCX · up to 10 MB</p>
            </div>
            <div v-if="store.profile?.profile?.resume_path"
              class="flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-900/20 border border-emerald-700/40 px-3 py-1.5 rounded-full">
              <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              Uploaded
            </div>
          </div>
          <div class="px-5 py-5">
            <input ref="fileInput" type="file" accept=".pdf,.doc,.docx" class="hidden" @change="onFileChange" />
            <div class="flex flex-col sm:flex-row gap-3">
              <button @click="fileInput?.click()" :disabled="store.uploading"
                class="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 px-4 py-2.5 border border-slate-600 hover:bg-slate-700 hover:border-slate-500 rounded-xl text-sm font-medium text-slate-300 transition disabled:opacity-50">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
                </svg>
                {{ store.uploading ? 'Uploading…' : 'Upload Resume' }}
              </button>
              <button @click="analyze" :disabled="store.analyzing || !store.profile?.profile?.resume_path"
                class="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white rounded-xl text-sm font-semibold transition shadow-sm shadow-violet-900/50">
                <svg v-if="store.analyzing" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                </svg>
                {{ store.analyzing ? 'Analyzing…' : 'AI Analyze Resume' }}
              </button>
            </div>
            <p v-if="!store.profile?.profile?.resume_path" class="text-xs text-slate-500 mt-2">
              Upload your resume first, then click "AI Analyze" to auto-fill your profile.
            </p>
          </div>
        </section>

        <!-- AI Summary & Skills -->
        <section class="bg-slate-800 rounded-2xl border border-slate-700/60 shadow-sm overflow-hidden">
          <div class="px-5 py-4 border-b border-slate-700/60 flex items-center justify-between">
            <h2 class="text-sm font-semibold text-slate-100">Profile Summary &amp; Skills</h2>
            <span class="text-xs text-slate-500 bg-slate-700/50 border border-slate-600 px-2.5 py-1 rounded-full">Auto-filled by AI · edit freely</span>
          </div>
          <div class="px-5 py-5 space-y-4">
            <div>
              <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Summary</label>
              <textarea v-model="profileSummary" rows="5"
                placeholder="Describe your background, expertise, and career goals…"
                class="w-full rounded-xl border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm resize-y transition" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                Skills <span class="normal-case font-normal text-slate-600">(comma-separated)</span>
              </label>
              <input v-model="skillsText" type="text" placeholder="Python, Azure DevOps, Kubernetes, React…"
                class="w-full rounded-xl border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm transition" />
              <div v-if="skillList().length" class="flex flex-wrap gap-1.5 mt-3">
                <span v-for="s in skillList()" :key="s"
                  class="px-2.5 py-1 bg-indigo-900/30 text-indigo-400 border border-indigo-700/40 rounded-full text-xs font-medium">
                  {{ s }}
                </span>
              </div>
            </div>
          </div>
        </section>

        <!-- Save row -->
        <div class="flex items-center gap-4 pb-2">
          <button @click="saveProfile"
            class="inline-flex items-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold transition shadow-sm shadow-indigo-900/50">
            Save Profile
          </button>
          <transition name="fade">
            <span v-if="successMsg" class="text-sm text-emerald-400 font-medium flex items-center gap-1">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              {{ successMsg }}
            </span>
          </transition>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
