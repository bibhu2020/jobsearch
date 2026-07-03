<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

type GuideMode = 'candidate' | 'hiring'
const activeGuide = ref<GuideMode>(auth.isInterviewer ? 'hiring' : 'candidate')

const candidateSections = [
  { id: 'profile', label: 'Build your profile', icon: '👤' },
  { id: 'pipeline', label: 'Track your pipeline', icon: '📋' },
  { id: 'search', label: 'Let AI find jobs', icon: '🔍' },
  { id: 'kits', label: 'Generate documents', icon: '✨' },
]
const hiringSections = [
  { id: 'h-project', label: 'Create a project', icon: '🗂️' },
  { id: 'h-candidates', label: 'Add candidates', icon: '📥' },
  { id: 'h-score', label: 'AI scoring', icon: '🤖' },
  { id: 'h-collab', label: 'Track & collaborate', icon: '🤝' },
]
const sections = computed(() => (activeGuide.value === 'hiring' ? hiringSections : candidateSections))

const activeSection = ref(sections.value[0].id)
let sectionObserver: IntersectionObserver | null = null
let revealObserver: IntersectionObserver | null = null

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function setupObservers() {
  sectionObserver?.disconnect()
  revealObserver?.disconnect()

  const revealEls = document.querySelectorAll('[data-reveal]')
  revealObserver = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) entry.target.classList.add('is-visible')
      }
    },
    { threshold: 0.15 },
  )
  revealEls.forEach((el) => revealObserver!.observe(el))

  activeSection.value = sections.value[0].id
  sectionObserver = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) activeSection.value = entry.target.id
      }
    },
    { rootMargin: '-40% 0px -50% 0px' },
  )
  sections.value.forEach((s) => {
    const el = document.getElementById(s.id)
    if (el) sectionObserver!.observe(el)
  })
}

function selectGuide(mode: GuideMode) {
  if (activeGuide.value === mode) return
  activeGuide.value = mode
  nextTick(() => {
    window.scrollTo({ top: 0 })
    setupObservers()
  })
}

onMounted(() => setupObservers())
onBeforeUnmount(() => {
  sectionObserver?.disconnect()
  revealObserver?.disconnect()
})
</script>

<template>
  <div class="flex flex-col h-screen bg-slate-900">
    <Navbar />

    <div class="flex-1 overflow-y-auto pb-24 sm:pb-6">
      <!-- Hero -->
      <div class="relative overflow-hidden border-b border-slate-700/60">
        <div class="hero-blob hero-blob-a" :class="{ 'hero-blob-hiring': activeGuide === 'hiring' }"></div>
        <div class="hero-blob hero-blob-b" :class="{ 'hero-blob-hiring': activeGuide === 'hiring' }"></div>
        <div class="relative max-w-3xl mx-auto px-4 sm:px-6 py-12 sm:py-16 text-center">
          <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl shadow-lg text-3xl logo-pulse mb-5 transition-colors"
            :class="activeGuide === 'hiring' ? 'bg-purple-600 shadow-purple-900/50' : 'bg-indigo-600 shadow-indigo-900/50'">
            {{ activeGuide === 'hiring' ? '🧑‍💼' : '🎯' }}
          </div>
          <h1 class="text-2xl sm:text-3xl font-bold text-slate-100">How JobQuest AI works</h1>
          <p class="text-sm sm:text-base text-slate-400 mt-3 max-w-xl mx-auto leading-relaxed">
            <span v-if="activeGuide === 'candidate'">
              Everything you need to run your job search on autopilot — build a profile once, let AI find and
              score matching roles, track them on a Kanban board, and generate tailored documents in one click.
            </span>
            <span v-else>
              Everything you need to run a hiring pipeline — spin up a project per role, drop in candidate
              resumes, let AI score them against the job description, and collaborate with your team.
            </span>
          </p>

          <!-- Mode toggle -->
          <div class="inline-flex items-center gap-1 mt-6 p-1 rounded-full bg-slate-800 border border-slate-700/60">
            <button @click="selectGuide('candidate')"
              class="flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-semibold transition-all"
              :class="activeGuide === 'candidate' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'">
              🔍 Job Hunt guide
            </button>
            <button @click="selectGuide('hiring')"
              class="flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-semibold transition-all"
              :class="activeGuide === 'hiring' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'">
              🧑‍💼 Hiring guide
            </button>
          </div>
          <p class="text-xs text-slate-600 mt-2">
            Showing the guide for your current mode
            (<span class="font-medium text-slate-400">{{ auth.isInterviewer ? 'Hiring' : 'Job Hunt' }}</span>) —
            switch the tab above to preview the other.
          </p>

          <div>
            <button @click="scrollTo(sections[0].id)"
              class="mt-6 inline-flex items-center gap-2 px-5 py-2.5 text-white rounded-xl text-sm font-semibold transition shadow-sm"
              :class="activeGuide === 'hiring' ? 'bg-purple-600 hover:bg-purple-500 shadow-purple-900/50' : 'bg-indigo-600 hover:bg-indigo-500 shadow-indigo-900/50'">
              Get started
              <svg class="h-4 w-4 bounce-down" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Sticky section nav -->
      <div class="sticky top-0 z-20 bg-slate-900/95 backdrop-blur border-b border-slate-700/60">
        <div class="max-w-5xl mx-auto px-2 sm:px-6 flex gap-1 overflow-x-auto no-scrollbar">
          <button v-for="s in sections" :key="s.id" @click="scrollTo(s.id)"
            class="flex items-center gap-1.5 px-3 py-3 text-xs sm:text-sm font-medium whitespace-nowrap border-b-2 transition-colors flex-shrink-0"
            :class="activeSection === s.id
              ? (activeGuide === 'hiring' ? 'text-white border-purple-500' : 'text-white border-indigo-500')
              : 'text-slate-500 border-transparent hover:text-slate-300'">
            <span>{{ s.icon }}</span>{{ s.label }}
          </button>
        </div>
      </div>

      <!-- ══════════════════════════ CANDIDATE / JOB HUNT GUIDE ══════════════════════════ -->
      <div v-if="activeGuide === 'candidate'" class="max-w-3xl mx-auto px-4 sm:px-6 py-10 space-y-16">

        <!-- 1. Profile -->
        <section id="profile" data-reveal class="reveal grid gap-6 sm:grid-cols-2 items-center">
          <div>
            <span class="text-xs font-bold text-indigo-400 uppercase tracking-wider">Step 1</span>
            <h2 class="text-lg font-bold text-slate-100 mt-1">Build your profile</h2>
            <p class="text-sm text-slate-400 mt-2 leading-relaxed">
              Drop your resume onto the <router-link to="/profile" class="text-indigo-400 hover:underline">Profile</router-link>
              page — AI reads it and fills in your summary, skills, location, phone, and email automatically.
              Nothing to type by hand.
            </p>
            <ul class="mt-4 space-y-2 text-sm text-slate-400">
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Drag &amp; drop or browse — PDF, DOC, DOCX</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Review &amp; edit the AI-extracted fields anytime</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> This profile powers job matching and every generated document</li>
            </ul>
          </div>

          <!-- animated demo: dropzone -> extraction -->
          <div class="bg-slate-800 rounded-2xl border border-slate-700/60 p-5 shadow-sm overflow-hidden">
            <div class="demo-dropzone rounded-xl border-2 border-dashed border-slate-600 flex flex-col items-center justify-center py-6 gap-2">
              <svg class="h-7 w-7 text-slate-500 demo-upload-icon" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
              <span class="text-xs text-slate-500">resume.pdf</span>
            </div>
            <div class="flex flex-wrap gap-2 mt-4">
              <span class="demo-tag demo-tag-1 text-xs font-medium px-2.5 py-1 rounded-full bg-indigo-900/30 border border-indigo-700/40 text-indigo-300">React · Python</span>
              <span class="demo-tag demo-tag-2 text-xs font-medium px-2.5 py-1 rounded-full bg-violet-900/30 border border-violet-700/40 text-violet-300">📍 Austin, TX</span>
              <span class="demo-tag demo-tag-3 text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-900/30 border border-emerald-700/40 text-emerald-300">✉ jane@mail.com</span>
              <span class="demo-tag demo-tag-4 text-xs font-medium px-2.5 py-1 rounded-full bg-amber-900/30 border border-amber-700/40 text-amber-300">📞 (555) 010-2020</span>
            </div>
          </div>
        </section>

        <!-- 2. Pipeline -->
        <section id="pipeline" data-reveal class="reveal grid gap-6 sm:grid-cols-2 items-center">
          <!-- animated demo: card moving through kanban columns (order swapped on sm for variety) -->
          <div class="bg-slate-800 rounded-2xl border border-slate-700/60 p-5 shadow-sm order-2 sm:order-1 overflow-hidden">
            <div class="grid grid-cols-3 gap-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
              <span>Wishlist</span><span>Applied</span><span>Interview</span>
            </div>
            <div class="relative grid grid-cols-3 gap-2 h-24 bg-slate-900/50 rounded-lg p-2">
              <div class="border border-dashed border-slate-700 rounded-md"></div>
              <div class="border border-dashed border-slate-700 rounded-md"></div>
              <div class="border border-dashed border-slate-700 rounded-md"></div>
              <div class="demo-card absolute top-2 left-2 w-[calc(33.333%-0.55rem)] bg-slate-700 rounded-md px-2 py-1.5 shadow-md">
                <div class="text-[11px] font-semibold text-slate-100 truncate">Frontend Engineer</div>
                <div class="text-[9px] text-slate-400 truncate">Acme Corp</div>
              </div>
            </div>
          </div>
          <div class="order-1 sm:order-2">
            <span class="text-xs font-bold text-indigo-400 uppercase tracking-wider">Step 2</span>
            <h2 class="text-lg font-bold text-slate-100 mt-1">Track your pipeline</h2>
            <p class="text-sm text-slate-400 mt-2 leading-relaxed">
              Every job lives on your <router-link to="/pipeline" class="text-indigo-400 hover:underline">Pipeline</router-link> board.
              Drag cards between stages — Wishlist, Applied, Interview, Offer — exactly like a physical board.
            </p>
            <ul class="mt-4 space-y-2 text-sm text-slate-400">
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Add a job by pasting a URL or raw text — details are extracted for you</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Drag &amp; drop cards to update stage and order</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Open a card to see notes, dates, and generated documents</li>
            </ul>
          </div>
        </section>

        <!-- 3. Job Search -->
        <section id="search" data-reveal class="reveal grid gap-6 sm:grid-cols-2 items-center">
          <div>
            <span class="text-xs font-bold text-indigo-400 uppercase tracking-wider">Step 3</span>
            <h2 class="text-lg font-bold text-slate-100 mt-1">Let AI find jobs for you</h2>
            <p class="text-sm text-slate-400 mt-2 leading-relaxed">
              Hit <span class="font-semibold text-slate-200">Run Job Search</span> on the
              <router-link to="/suggestions" class="text-indigo-400 hover:underline">Job Search</router-link> page.
              It searches 9 job boards in parallel and an AI scorer only keeps roles that are a strong match for your profile.
            </p>
            <ul class="mt-4 space-y-2 text-sm text-slate-400">
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Runs in the background (~5 min) — you can navigate away</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Only roles scoring 70%+ match show up</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Add a suggestion straight to your Pipeline, or dismiss it</li>
            </ul>
          </div>

          <!-- animated demo: sources lighting up + match score -->
          <div class="bg-slate-800 rounded-2xl border border-slate-700/60 p-5 shadow-sm overflow-hidden">
            <div class="flex items-center gap-2 mb-4">
              <svg class="h-5 w-5 text-indigo-400 demo-radar" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803a7.5 7.5 0 0010.607 0z" />
              </svg>
              <span class="text-xs text-slate-400">Searching 9 sources…</span>
            </div>
            <div class="grid grid-cols-3 gap-2 mb-4">
              <span v-for="i in 9" :key="i" class="demo-dot w-full h-2 rounded-full bg-slate-700" :style="{ animationDelay: `${i * 0.15}s` }"></span>
            </div>
            <div class="demo-score flex items-center justify-between bg-emerald-900/20 border border-emerald-700/40 rounded-xl px-3 py-2">
              <span class="text-xs font-medium text-slate-200">Senior Frontend Engineer</span>
              <span class="text-xs font-bold text-emerald-400 bg-emerald-900/40 px-2 py-0.5 rounded-full">92% match</span>
            </div>
          </div>
        </section>

        <!-- 4. Kits -->
        <section id="kits" data-reveal class="reveal grid gap-6 sm:grid-cols-2 items-center">
          <!-- animated demo: typing effect -->
          <div class="bg-slate-800 rounded-2xl border border-slate-700/60 p-5 shadow-sm order-2 sm:order-1 overflow-hidden">
            <div class="flex gap-1.5 mb-3">
              <span class="text-[10px] font-semibold px-2 py-1 rounded-full bg-violet-900/30 border border-violet-700/40 text-violet-300">Cover Letter</span>
              <span class="text-[10px] font-semibold px-2 py-1 rounded-full bg-slate-700/50 border border-slate-600 text-slate-400">Resume</span>
              <span class="text-[10px] font-semibold px-2 py-1 rounded-full bg-slate-700/50 border border-slate-600 text-slate-400">Interview Qs</span>
            </div>
            <div class="bg-slate-900/60 rounded-lg p-3 font-mono text-[11px] text-slate-300 leading-relaxed h-20 overflow-hidden">
              <span class="demo-typewriter">Dear Hiring Manager, I'm excited to apply for the Frontend Engineer role at Acme Corp...</span>
            </div>
          </div>
          <div class="order-1 sm:order-2">
            <span class="text-xs font-bold text-indigo-400 uppercase tracking-wider">Step 4</span>
            <h2 class="text-lg font-bold text-slate-100 mt-1">Generate tailored documents</h2>
            <p class="text-sm text-slate-400 mt-2 leading-relaxed">
              Open any card on your Pipeline and generate a cover letter, resume rewrite, interview prep questions,
              or a company brief — tailored to that specific job using your profile.
            </p>
            <ul class="mt-4 space-y-2 text-sm text-slate-400">
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> One click per document type, ready in seconds</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Edit the generated text before exporting</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Download as a polished PDF, attached to that job's card</li>
            </ul>
          </div>
        </section>

        <!-- CTA -->
        <div data-reveal class="reveal text-center pt-4">
          <router-link to="/pipeline"
            class="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold transition shadow-sm shadow-indigo-900/50">
            Got it — take me to my Pipeline
          </router-link>
        </div>
      </div>

      <!-- ══════════════════════════ HIRING GUIDE ══════════════════════════ -->
      <div v-else class="max-w-3xl mx-auto px-4 sm:px-6 py-10 space-y-16">

        <!-- 1. Create a project -->
        <section id="h-project" data-reveal class="reveal grid gap-6 sm:grid-cols-2 items-center">
          <div>
            <span class="text-xs font-bold text-purple-400 uppercase tracking-wider">Step 1</span>
            <h2 class="text-lg font-bold text-slate-100 mt-1">Create a hiring project</h2>
            <p class="text-sm text-slate-400 mt-2 leading-relaxed">
              On <router-link to="/interviewer" class="text-purple-400 hover:underline">Hiring Projects</router-link>,
              start one project per open role. Paste the raw job description and AI formats it into clean sections automatically.
            </p>
            <ul class="mt-4 space-y-2 text-sm text-slate-400">
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Title, location, and a rich-text job description per project</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Paste-and-format — no manual reformatting needed</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Edit anytime; the JD is what AI scores every candidate against</li>
            </ul>
          </div>

          <!-- animated demo: project card + JD formatting -->
          <div class="bg-slate-800 rounded-2xl border border-slate-700/60 p-5 shadow-sm overflow-hidden">
            <div class="flex items-center justify-between mb-3">
              <span class="text-sm font-semibold text-slate-100">Senior Backend Engineer</span>
              <span class="text-[10px] font-medium text-slate-500 bg-slate-700/50 border border-slate-600 px-2 py-0.5 rounded-full">Remote · US</span>
            </div>
            <div class="space-y-1.5">
              <div class="demo-tag demo-tag-1 h-2 rounded bg-purple-900/40 w-full"></div>
              <div class="demo-tag demo-tag-2 h-2 rounded bg-purple-900/40 w-5/6"></div>
              <div class="demo-tag demo-tag-3 h-2 rounded bg-purple-900/40 w-4/6"></div>
              <div class="demo-tag demo-tag-4 h-2 rounded bg-purple-900/40 w-3/6"></div>
            </div>
            <div class="mt-4 flex items-center gap-1.5 text-[10px] text-purple-400">
              <svg class="h-3 w-3 demo-radar" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
              </svg>
              AI-formatted from your paste
            </div>
          </div>
        </section>

        <!-- 2. Add candidates -->
        <section id="h-candidates" data-reveal class="reveal grid gap-6 sm:grid-cols-2 items-center">
          <!-- animated demo: dropzone -> candidate card appears in column -->
          <div class="bg-slate-800 rounded-2xl border border-slate-700/60 p-5 shadow-sm order-2 sm:order-1 overflow-hidden">
            <div class="demo-dropzone rounded-xl border-2 border-dashed border-purple-700/50 flex flex-col items-center justify-center py-5 gap-1.5 mb-3">
              <svg class="h-6 w-6 text-purple-400 demo-upload-icon" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
              <span class="text-xs text-slate-500">candidate_resume.pdf</span>
            </div>
            <div class="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Applied</div>
            <div class="demo-tag demo-tag-3 bg-slate-700 rounded-md px-2.5 py-2 shadow-md">
              <div class="text-[11px] font-semibold text-slate-100 truncate">Priya Nair</div>
              <div class="text-[9px] text-slate-400 truncate">priya@mail.com · Bengaluru</div>
            </div>
          </div>
          <div class="order-1 sm:order-2">
            <span class="text-xs font-bold text-purple-400 uppercase tracking-wider">Step 2</span>
            <h2 class="text-lg font-bold text-slate-100 mt-1">Add candidates by dropping resumes</h2>
            <p class="text-sm text-slate-400 mt-2 leading-relaxed">
              Open a project and drag &amp; drop a candidate's resume onto any pipeline column — a candidate card is
              created instantly with their name, email, phone, and location extracted automatically.
            </p>
            <ul class="mt-4 space-y-2 text-sm text-slate-400">
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Drop directly onto Applied, Screening, Interview, Offer, or Rejected</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> PDF, DOC, or DOCX — same as your own resume upload</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> This is separate from your own Job Hunt profile — here you're uploading someone else's resume</li>
            </ul>
          </div>
        </section>

        <!-- 3. AI scoring -->
        <section id="h-score" data-reveal class="reveal grid gap-6 sm:grid-cols-2 items-center">
          <div>
            <span class="text-xs font-bold text-purple-400 uppercase tracking-wider">Step 3</span>
            <h2 class="text-lg font-bold text-slate-100 mt-1">Let AI score every candidate</h2>
            <p class="text-sm text-slate-400 mt-2 leading-relaxed">
              Open a candidate card and click <span class="font-semibold text-slate-200">AI Scan</span>. AI compares
              their resume against the project's job description and returns a score, strengths, gaps, and a hire recommendation.
            </p>
            <ul class="mt-4 space-y-2 text-sm text-slate-400">
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> 0–100 match score plus a Strong Yes / Yes / Consider / No recommendation</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Called-out strengths and gaps versus the JD</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Add your own interview notes alongside the AI assessment</li>
            </ul>
          </div>

          <!-- animated demo: score bar + recommendation + strengths/gaps -->
          <div class="bg-slate-800 rounded-2xl border border-slate-700/60 p-5 shadow-sm overflow-hidden">
            <div class="flex items-center justify-between mb-3">
              <span class="text-xs font-semibold text-slate-300">AI Assessment</span>
              <div class="flex items-center gap-2">
                <div class="w-20 bg-slate-900 rounded-full h-1.5 border border-slate-700 overflow-hidden">
                  <div class="demo-score-bar bg-purple-500 h-full rounded-full"></div>
                </div>
                <span class="text-xs font-bold text-purple-400">87/100</span>
              </div>
            </div>
            <span class="demo-tag demo-tag-1 inline-block text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-900/30 text-emerald-400 border border-emerald-700/40 mb-3">
              Recommendation: Strong Yes
            </span>
            <div class="flex flex-wrap gap-1.5">
              <span class="demo-tag demo-tag-2 text-[10px] px-2 py-0.5 bg-emerald-900/30 text-emerald-400 rounded-full border border-emerald-700/40">✓ Node.js</span>
              <span class="demo-tag demo-tag-3 text-[10px] px-2 py-0.5 bg-emerald-900/30 text-emerald-400 rounded-full border border-emerald-700/40">✓ System Design</span>
              <span class="demo-tag demo-tag-4 text-[10px] px-2 py-0.5 bg-red-900/30 text-red-400 rounded-full border border-red-700/40">✗ Kubernetes</span>
            </div>
          </div>
        </section>

        <!-- 4. Track & collaborate -->
        <section id="h-collab" data-reveal class="reveal grid gap-6 sm:grid-cols-2 items-center">
          <!-- animated demo: candidate card moving across stages + team avatars -->
          <div class="bg-slate-800 rounded-2xl border border-slate-700/60 p-5 shadow-sm order-2 sm:order-1 overflow-hidden">
            <div class="grid grid-cols-3 gap-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
              <span>Applied</span><span>Interview</span><span>Offer</span>
            </div>
            <div class="relative grid grid-cols-3 gap-2 h-20 bg-slate-900/50 rounded-lg p-2 mb-4">
              <div class="border border-dashed border-slate-700 rounded-md"></div>
              <div class="border border-dashed border-slate-700 rounded-md"></div>
              <div class="border border-dashed border-slate-700 rounded-md"></div>
              <div class="demo-card-hiring absolute top-2 left-2 w-[calc(33.333%-0.55rem)] bg-slate-700 rounded-md px-2 py-1.5 shadow-md">
                <div class="text-[11px] font-semibold text-slate-100 truncate">Priya Nair</div>
                <div class="text-[9px] text-slate-400 truncate">Backend Engineer</div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <div class="flex -space-x-2">
                <span class="demo-tag demo-tag-1 w-6 h-6 rounded-full bg-purple-600 border-2 border-slate-800 flex items-center justify-center text-[9px] font-bold text-white">JD</span>
                <span class="demo-tag demo-tag-2 w-6 h-6 rounded-full bg-indigo-600 border-2 border-slate-800 flex items-center justify-center text-[9px] font-bold text-white">MK</span>
              </div>
              <span class="text-[10px] text-slate-500">reviewing together</span>
            </div>
          </div>
          <div class="order-1 sm:order-2">
            <span class="text-xs font-bold text-purple-400 uppercase tracking-wider">Step 4</span>
            <h2 class="text-lg font-bold text-slate-100 mt-1">Track stages &amp; collaborate</h2>
            <p class="text-sm text-slate-400 mt-2 leading-relaxed">
              Drag candidate cards across Applied, Screening, Interview, Offer, and Rejected — the same drag-and-drop
              board pattern as your own Job Hunt Pipeline. Invite teammates to a project so everyone reviews from the same board.
            </p>
            <ul class="mt-4 space-y-2 text-sm text-slate-400">
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Drag &amp; drop cards between stages to update status</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Invite teammates by email to share a project</li>
              <li class="flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span> Notes and AI assessments are visible to everyone on the project</li>
            </ul>
          </div>
        </section>

        <p data-reveal class="reveal text-xs text-slate-600 text-center max-w-lg mx-auto">
          Hiring mode is still under active development — expect new capabilities here soon.
        </p>

        <!-- CTA -->
        <div data-reveal class="reveal text-center pt-4">
          <router-link to="/interviewer"
            class="inline-flex items-center gap-2 px-5 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-sm font-semibold transition shadow-sm shadow-purple-900/50">
            Got it — take me to my Hiring Projects
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { scrollbar-width: none; }

/* Hero */
.hero-blob {
  position: absolute;
  border-radius: 9999px;
  filter: blur(60px);
  opacity: 0.25;
  pointer-events: none;
  transition: background 0.4s ease;
}
.hero-blob-a {
  width: 22rem; height: 22rem;
  top: -8rem; left: -6rem;
  background: radial-gradient(circle, theme('colors.indigo.500'), transparent 70%);
  animation: float-a 14s ease-in-out infinite;
}
.hero-blob-b {
  width: 18rem; height: 18rem;
  bottom: -8rem; right: -4rem;
  background: radial-gradient(circle, theme('colors.violet.500'), transparent 70%);
  animation: float-b 16s ease-in-out infinite;
}
.hero-blob-a.hero-blob-hiring { background: radial-gradient(circle, theme('colors.purple.500'), transparent 70%); }
.hero-blob-b.hero-blob-hiring { background: radial-gradient(circle, theme('colors.fuchsia.500'), transparent 70%); }
@keyframes float-a {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(2rem, 3rem); }
}
@keyframes float-b {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-2rem, -2rem); }
}
.logo-pulse { animation: pulse-ring 2.4s ease-in-out infinite; }
@keyframes pulse-ring {
  0%, 100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); }
  50% { box-shadow: 0 0 0 12px rgba(99, 102, 241, 0); }
}
.bounce-down { animation: bounce-down 1.6s ease-in-out infinite; }
@keyframes bounce-down {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(4px); }
}

/* Scroll reveal */
.reveal { opacity: 0; transform: translateY(16px); transition: opacity 0.6s ease, transform 0.6s ease; }
.reveal.is-visible { opacity: 1; transform: translateY(0); }

/* Shared dropzone / tag-pop demos */
.demo-upload-icon { animation: upload-bob 2.4s ease-in-out infinite; }
@keyframes upload-bob {
  0%, 100% { transform: translateY(0); opacity: 0.6; }
  50% { transform: translateY(-4px); opacity: 1; }
}
.demo-tag { opacity: 0; animation: tag-pop 4s ease-in-out infinite; }
.demo-tag-1 { animation-delay: 0.2s; }
.demo-tag-2 { animation-delay: 0.6s; }
.demo-tag-3 { animation-delay: 1s; }
.demo-tag-4 { animation-delay: 1.4s; }
@keyframes tag-pop {
  0% { opacity: 0; transform: scale(0.8); }
  8%, 90% { opacity: 1; transform: scale(1); }
  100% { opacity: 1; transform: scale(1); }
}

/* Pipeline demo (candidate) */
.demo-card {
  animation: card-move 5s ease-in-out infinite;
}
@keyframes card-move {
  0%, 12% { left: 0.5rem; }
  40%, 55% { left: calc(33.333% + 0.35rem); }
  80%, 100% { left: calc(66.666% + 0.15rem); }
}

/* Stage demo (hiring) — same motion, separate class to keep concepts distinct */
.demo-card-hiring {
  animation: card-move 5s ease-in-out infinite;
}

/* Search demo */
.demo-radar { animation: spin 3s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.demo-dot { animation: dot-light 3s ease-in-out infinite; }
@keyframes dot-light {
  0%, 100% { background-color: theme('colors.slate.700'); }
  50% { background-color: theme('colors.indigo.500'); }
}
.demo-score { animation: score-in 3s ease-in-out infinite; opacity: 0; }
@keyframes score-in {
  0%, 55% { opacity: 0; transform: translateY(6px); }
  70%, 95% { opacity: 1; transform: translateY(0); }
  100% { opacity: 0; transform: translateY(6px); }
}

/* AI score bar (hiring) */
.demo-score-bar {
  width: 0%;
  animation: score-fill 4s ease-in-out infinite;
}
@keyframes score-fill {
  0% { width: 0%; }
  40%, 90% { width: 87%; }
  100% { width: 0%; }
}

/* Kits demo */
.demo-typewriter {
  display: inline-block;
  overflow: hidden;
  white-space: normal;
  border-right: 2px solid theme('colors.violet.400');
  animation: type-fade 6s steps(60, end) infinite;
}
@keyframes type-fade {
  0% { clip-path: inset(0 100% 0 0); opacity: 1; }
  55% { clip-path: inset(0 0 0 0); opacity: 1; }
  80% { clip-path: inset(0 0 0 0); opacity: 1; }
  95%, 100% { clip-path: inset(0 0 0 0); opacity: 0; }
}

@media (prefers-reduced-motion: reduce) {
  .hero-blob, .logo-pulse, .bounce-down, .demo-upload-icon, .demo-tag,
  .demo-card, .demo-card-hiring, .demo-radar, .demo-dot, .demo-score,
  .demo-score-bar, .demo-typewriter {
    animation: none !important;
  }
  .reveal { opacity: 1; transform: none; transition: none; }
}
</style>
