<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useApplyStore, type ApplicationRun } from '@/stores/apply'

const props = defineProps<{ cardId: number }>()
const store = useApplyStore()
const runs = ref<ApplicationRun[]>([])
const expanded = ref(false)
const shotUrl = ref<string | null>(null)
const shotError = ref('')

const showShot = ref(false)

async function toggleScreenshot() {
  showShot.value = !showShot.value
  if (!showShot.value || shotUrl.value) return
  try {
    shotUrl.value = await store.screenshotUrl(runs.value[0].id)
  } catch {
    shotError.value = 'Screenshot unavailable'
    showShot.value = false
  }
}

onUnmounted(() => { if (shotUrl.value) URL.revokeObjectURL(shotUrl.value) })

const STATUS_CLS: Record<string, string> = {
  submitted: 'text-emerald-400', failed: 'text-red-400', cancelled: 'text-slate-400',
}

onMounted(async () => {
  try { runs.value = await store.cardRuns(props.cardId) } catch { /* no record */ }
})

function fmt(d: string | null) {
  return d ? new Date(d).toLocaleString() : ''
}

function fieldValue(v: any) {
  if (v === true) return 'Checked'
  if (v === false) return 'Not checked'
  if (Array.isArray(v)) return v.join(', ')
  return v || '—'
}
</script>

<template>
  <div v-if="runs.length" class="rounded-xl bg-slate-800 border border-slate-700/60 p-4">
    <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Application</h3>
    <div class="text-sm space-y-1">
      <p>
        <span :class="['font-semibold capitalize', STATUS_CLS[runs[0].status] || 'text-amber-400']">{{ runs[0].status.replace('_', ' ') }}</span>
        <span v-if="runs[0].site" class="text-slate-400"> · {{ runs[0].site }}</span>
        <span v-if="runs[0].status === 'submitted'" class="text-slate-400"> · {{ runs[0].auto_submitted ? 'submitted automatically' : 'submitted after review' }}</span>
      </p>
      <p v-if="runs[0].message" class="text-slate-400">{{ runs[0].message }}</p>
      <p v-if="shotError" class="text-xs text-red-400">{{ shotError }}</p>
      <p class="text-xs text-slate-500">{{ fmt(runs[0].finished_at || runs[0].started_at) }}</p>
      <div class="flex gap-3 pt-1">
        <button v-if="runs[0].has_screenshot" @click="toggleScreenshot" class="text-xs text-indigo-400 hover:text-indigo-300">
          {{ showShot ? 'Hide' : 'Show' }} confirmation
        </button>
        <a v-if="runs[0].apply_url" :href="runs[0].apply_url" target="_blank" class="text-xs text-indigo-400 hover:text-indigo-300">Application page</a>
        <button v-if="runs[0].fields.length" @click="expanded = !expanded" class="text-xs text-indigo-400 hover:text-indigo-300">
          {{ expanded ? 'Hide' : 'Show' }} answers ({{ runs[0].fields.length }})
        </button>
      </div>
    </div>
    <img v-if="showShot && shotUrl" :src="shotUrl" alt="Confirmation page after submitting"
      class="mt-3 w-full rounded-lg border border-slate-700/60" />
    <dl v-if="expanded" class="mt-3 space-y-2 border-t border-slate-700/60 pt-3">
      <div v-for="f in runs[0].fields" :key="f.id">
        <dt class="text-xs text-slate-500">{{ f.label }}</dt>
        <dd class="text-sm text-slate-200 whitespace-pre-line break-words">{{ fieldValue(f.value) }}</dd>
      </div>
    </dl>
  </div>
</template>
