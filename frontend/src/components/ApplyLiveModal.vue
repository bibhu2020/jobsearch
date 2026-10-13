<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useApplyStore, TERMINAL, type ApplicationRun } from '@/stores/apply'
import { usePipelineStore, type PipelineCard } from '@/stores/pipeline'

const props = defineProps<{ card: PipelineCard }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const apply = useApplyStore()
const pipeline = usePipelineStore()

const VIEWPORT_W = 1280
const VIEWPORT_H = 900
const POLL_MS = 1500

const run = ref<ApplicationRun | null>(null)
const runId = ref<string | null>(null)
const startError = ref('')
const missing = ref<string[]>([])
const actionError = ref('')
const busy = ref(false)
const takeOver = ref(false)
const typeText = ref('')
const showLog = ref(false)
const verificationValue = ref('')
const lastShot = ref<string | null>(null)
let timer: ReturnType<typeof setTimeout> | null = null
let stopped = false

const status = computed(() => run.value?.status)
const isTerminal = computed(() => !!status.value && TERMINAL.includes(status.value))
const waitingForUser = computed(() => status.value === 'needs_input' || status.value === 'awaiting_review')
const verification = computed(() => run.value?.live?.needs?.kind === 'verification' ? run.value.live.needs : null)
const otherCard = computed(() => run.value && run.value.pipeline_card_id !== props.card.id)

const STATUS_UI: Record<string, { label: string; cls: string }> = {
  queued:          { label: 'Waiting for a browser',  cls: 'bg-slate-700/60 text-slate-300 border-slate-600' },
  running:         { label: 'Filling the application', cls: 'bg-indigo-900/40 text-indigo-300 border-indigo-700/60' },
  needs_input:     { label: 'Needs you',               cls: 'bg-amber-900/40 text-amber-300 border-amber-700/60' },
  awaiting_review: { label: 'Review before submitting', cls: 'bg-amber-900/40 text-amber-300 border-amber-700/60' },
  submitting:      { label: 'Submitting',              cls: 'bg-indigo-900/40 text-indigo-300 border-indigo-700/60' },
  submitted:       { label: 'Applied',                 cls: 'bg-emerald-900/40 text-emerald-300 border-emerald-700/60' },
  failed:          { label: 'Failed',                  cls: 'bg-red-900/40 text-red-300 border-red-700/60' },
  cancelled:       { label: 'Cancelled',               cls: 'bg-slate-700/60 text-slate-300 border-slate-600' },
}

const SOURCE_LABEL: Record<string, string> = {
  default: 'Your defaults', profile: 'Profile', llm: 'AI', file: 'File', user: 'You',
}

function fieldValue(v: any) {
  if (v === true) return 'Checked'
  if (v === false) return 'Not checked'
  if (Array.isArray(v)) return v.join(', ')
  return v || '—'
}

function needsAttention(f: { required: boolean; value: any; confidence: number }) {
  const empty = f.value === '' || f.value === null || f.value === false || (Array.isArray(f.value) && !f.value.length)
  return (f.required && empty) || (!empty && f.confidence < 0.8)
}

async function poll() {
  if (!runId.value || stopped) return
  try {
    const data = await apply.getRun(runId.value)
    run.value = data
    if (data.live?.screenshot) lastShot.value = data.live.screenshot
    if (TERMINAL.includes(data.status)) {
      takeOver.value = false
      if (data.status === 'submitted') pipeline.fetchCards()
      return
    }
  } catch { /* transient — keep polling */ }
  timer = setTimeout(poll, POLL_MS)
}

onMounted(async () => {
  try {
    runId.value = await apply.start(props.card.id)
    poll()
  } catch (err: any) {
    const data = err?.response?.data
    startError.value = (typeof data?.message === 'string' ? data.message : data?.message?.message) || 'Could not start the application'
    missing.value = data?.missing || data?.message?.missing || []
  }
})

onUnmounted(() => {
  stopped = true
  if (timer) clearTimeout(timer)
})

async function act(action: 'resume' | 'submit' | 'cancel' | 'mark-applied') {
  if (!runId.value) return
  busy.value = true
  actionError.value = ''
  try {
    await apply.control(runId.value, action)
    takeOver.value = false
  } catch (err: any) {
    actionError.value = err?.response?.data?.message || 'Action failed'
  } finally {
    busy.value = false
  }
}

async function sendVerification() {
  if (!runId.value || !verificationValue.value.trim()) return
  busy.value = true
  actionError.value = ''
  try {
    await apply.provideVerification(runId.value, verificationValue.value.trim())
    verificationValue.value = ''
  } catch (err: any) {
    actionError.value = err?.response?.data?.message || 'Could not send the code'
  } finally {
    busy.value = false
  }
}

async function onShotClick(e: MouseEvent) {
  if (!takeOver.value || !runId.value || isTerminal.value) return
  const img = e.currentTarget as HTMLImageElement
  const rect = img.getBoundingClientRect()
  const x = Math.round(((e.clientX - rect.left) / rect.width) * VIEWPORT_W)
  const y = Math.round(((e.clientY - rect.top) / rect.height) * VIEWPORT_H)
  await apply.input(runId.value, { kind: 'click', x, y }).catch(() => {})
}

async function sendText() {
  if (!runId.value || !typeText.value) return
  await apply.input(runId.value, { kind: 'type', text: typeText.value }).catch(() => {})
  typeText.value = ''
}

async function sendKey(key: string) {
  if (runId.value) await apply.input(runId.value, { kind: 'key', key }).catch(() => {})
}

async function scroll(dy: number) {
  if (runId.value) await apply.input(runId.value, { kind: 'scroll', dy }).catch(() => {})
}
</script>

<template>
  <div class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-stretch sm:items-center justify-center sm:p-4" @click.self="emit('close')">
    <div class="bg-slate-900 w-full sm:max-w-5xl sm:rounded-2xl border border-slate-700/60 shadow-2xl flex flex-col max-h-full overflow-hidden">

      <!-- Header -->
      <div class="flex items-start justify-between gap-3 px-5 py-4 border-b border-slate-700/60">
        <div class="min-w-0">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Auto-apply</p>
          <h2 class="text-base font-bold text-slate-100 truncate">{{ card.title || 'Untitled Position' }}</h2>
          <p class="text-sm text-slate-400 truncate">{{ card.company }}<span v-if="run?.site" class="text-slate-500"> · {{ run.site }}</span></p>
        </div>
        <div class="flex items-center gap-2 flex-shrink-0">
          <span v-if="status" :class="['text-xs font-semibold px-2.5 py-1 rounded-full border', STATUS_UI[status]?.cls]">
            {{ STATUS_UI[status]?.label || status }}
          </span>
          <button @click="emit('close')" title="Close (the application keeps running)"
            class="w-8 h-8 flex items-center justify-center rounded-lg text-slate-500 hover:text-slate-200 hover:bg-slate-800 transition">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto px-5 py-4 space-y-4">

        <!-- Start errors / missing setup -->
        <div v-if="startError" class="rounded-xl border border-amber-700/60 bg-amber-900/20 p-4">
          <p class="text-sm font-semibold text-amber-300">{{ startError }}</p>
          <ul v-if="missing.length" class="mt-2 text-sm text-amber-200/90 list-disc pl-5 space-y-0.5">
            <li v-for="m in missing" :key="m">{{ m }}</li>
          </ul>
          <RouterLink v-if="missing.length" to="/profile"
            class="inline-block mt-3 text-sm font-medium text-indigo-400 hover:text-indigo-300">Open Profile → Auto-Apply</RouterLink>
        </div>

        <div v-else-if="!run" class="py-16 text-center text-sm text-slate-500">Starting…</div>

        <template v-else>
          <p v-if="otherCard" class="text-xs text-amber-300">
            Another application is already in progress — showing it here. Start this one when it finishes.
          </p>

          <!-- Status message -->
          <div v-if="run.message || run.live?.step"
            :class="['rounded-xl border px-4 py-3 text-sm',
              waitingForUser ? 'border-amber-700/60 bg-amber-900/20 text-amber-200'
              : status === 'failed' ? 'border-red-700/60 bg-red-900/20 text-red-200'
              : status === 'submitted' ? 'border-emerald-700/60 bg-emerald-900/20 text-emerald-200'
              : 'border-slate-700/60 bg-slate-800 text-slate-300']">
            {{ run.message || run.live?.step }}
          </div>

          <!-- Email verification fallback (no Gmail, or nothing found there) -->
          <form v-if="verification" class="rounded-xl border border-amber-700/60 bg-amber-900/10 p-4 space-y-2" @submit.prevent="sendVerification">
            <label class="block text-sm text-amber-200">
              Check <span class="font-semibold">{{ verification.email }}</span> for an email from
              <span class="font-semibold">{{ verification.sender }}</span>, then enter the code or paste the verification link.
            </label>
            <div class="flex gap-2">
              <input v-model="verificationValue" type="text" autocomplete="one-time-code" placeholder="123456 or https://…"
                class="flex-1 rounded-lg border-slate-600 bg-slate-800 text-slate-100 placeholder-slate-500 text-sm focus:border-indigo-500 focus:ring-indigo-500" />
              <button type="submit" :disabled="busy || !verificationValue.trim()"
                class="px-4 py-2 text-sm rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold disabled:opacity-50">Continue</button>
            </div>
          </form>

          <!-- Live browser -->
          <div v-if="lastShot" class="space-y-2">
            <div :class="['relative rounded-xl overflow-hidden border', takeOver ? 'border-amber-500 ring-2 ring-amber-500/40' : 'border-slate-700/60']">
              <img :src="`data:image/jpeg;base64,${lastShot}`"
                :class="['w-full block select-none', takeOver ? 'cursor-crosshair' : '']"
                alt="Live view of the application browser" draggable="false" @click="onShotClick" />
              <span v-if="takeOver" class="absolute top-2 left-2 text-[11px] font-semibold bg-amber-500 text-slate-900 px-2 py-0.5 rounded">
                You're in control — click to interact
              </span>
            </div>

            <!-- Take-over controls -->
            <div v-if="takeOver && !isTerminal" class="flex flex-wrap items-center gap-2">
              <form class="flex flex-1 min-w-[220px] gap-2" @submit.prevent="sendText">
                <input v-model="typeText" type="text" placeholder="Type into the focused field…"
                  class="flex-1 rounded-lg border-slate-600 bg-slate-800 text-slate-100 placeholder-slate-500 text-sm focus:border-indigo-500 focus:ring-indigo-500" />
                <button type="submit" class="px-3 py-1.5 text-sm rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-100">Type</button>
              </form>
              <button v-for="k in ['Enter', 'Tab', 'Backspace', 'Escape']" :key="k" @click="sendKey(k)"
                class="px-2.5 py-1.5 text-xs rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800">{{ k }}</button>
              <button @click="scroll(-500)" class="px-2.5 py-1.5 text-xs rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800">Scroll ↑</button>
              <button @click="scroll(500)" class="px-2.5 py-1.5 text-xs rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800">Scroll ↓</button>
            </div>
          </div>

          <!-- Answers -->
          <div v-if="run.fields.length && (waitingForUser || isTerminal)" class="rounded-xl border border-slate-700/60 overflow-hidden">
            <div class="px-4 py-2.5 bg-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">What the agent filled in</div>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <tbody>
                  <tr v-for="f in run.fields" :key="f.id"
                    :class="['border-t border-slate-700/60', needsAttention(f) ? 'bg-amber-900/15' : '']">
                    <td class="px-4 py-2 text-slate-400 align-top w-2/5">
                      {{ f.label }}<span v-if="f.required" class="text-red-400"> *</span>
                    </td>
                    <td class="px-4 py-2 text-slate-100 align-top whitespace-pre-line break-words">{{ fieldValue(f.value) }}</td>
                    <td class="px-4 py-2 text-[11px] text-right align-top whitespace-nowrap">
                      <span :class="needsAttention(f) ? 'text-amber-400 font-semibold' : 'text-slate-500'">
                        {{ needsAttention(f) ? 'Check' : SOURCE_LABEL[f.source] || f.source }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Step log -->
          <div v-if="run.live?.log?.length">
            <button @click="showLog = !showLog" class="text-xs text-slate-500 hover:text-slate-300">
              {{ showLog ? 'Hide' : 'Show' }} activity log
            </button>
            <pre v-if="showLog" class="mt-2 text-[11px] text-slate-400 bg-slate-800 rounded-lg p-3 overflow-x-auto max-h-48">{{ run.live.log.join('\n') }}</pre>
          </div>
        </template>
      </div>

      <!-- Actions -->
      <div v-if="run && !startError" class="border-t border-slate-700/60 px-5 py-3 flex flex-wrap items-center gap-2 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
        <p v-if="actionError" class="w-full text-xs text-red-400">{{ actionError }}</p>
        <template v-if="!isTerminal">
          <button @click="takeOver = !takeOver"
            :class="['px-3 py-2 text-sm rounded-lg border font-medium transition',
              takeOver ? 'border-amber-500 text-amber-300 bg-amber-900/20' : 'border-slate-700 text-slate-300 hover:bg-slate-800']">
            {{ takeOver ? 'Stop controlling' : 'Take over' }}
          </button>
          <button v-if="waitingForUser" :disabled="busy" @click="act('resume')"
            class="px-3 py-2 text-sm rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800 font-medium disabled:opacity-50">
            Resume agent
          </button>
          <button v-if="waitingForUser" :disabled="busy" @click="act('mark-applied')"
            class="px-3 py-2 text-sm rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800 font-medium disabled:opacity-50">
            Mark applied
          </button>
          <button :disabled="busy" @click="act('cancel')"
            class="px-3 py-2 text-sm rounded-lg text-red-400 hover:bg-red-900/20 font-medium disabled:opacity-50 ml-auto">
            Cancel
          </button>
          <button v-if="status === 'awaiting_review'" :disabled="busy" @click="act('submit')"
            class="px-4 py-2 text-sm rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold disabled:opacity-50">
            Submit application
          </button>
        </template>
        <button v-else @click="emit('close')"
          class="ml-auto px-4 py-2 text-sm rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-100 font-medium">
          Close
        </button>
      </div>
    </div>
  </div>
</template>
