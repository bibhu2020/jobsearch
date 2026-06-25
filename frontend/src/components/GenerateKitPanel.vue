<script setup lang="ts">
import { ref, computed } from 'vue'
import { marked } from 'marked'
import api from '@/api'

const props = defineProps<{ cardId: number; jobTitle: string; company: string }>()

interface Kit { id: number; type: string; content: string }

const kits = ref<Record<string, Kit>>({})
const activeType = ref<string | null>(null)
const editContent = ref('')
const mode = ref<'edit' | 'preview'>('edit')
const generating = ref<string | null>(null)
const saving = ref(false)
const downloading = ref(false)
const error = ref('')

const KIT_TYPES = [
  { key: 'cover_letter',        label: 'Cover Letter',    icon: '✉️',  color: 'indigo' },
  { key: 'resume',              label: 'Tailored Resume', icon: '📄',  color: 'blue'   },
  { key: 'interview_questions', label: 'Interview Prep',  icon: '🎯',  color: 'violet' },
  { key: 'company_brief',       label: 'Company Brief',   icon: '🏢',  color: 'amber'  },
]

const activeKitMeta = computed(() => KIT_TYPES.find(k => k.key === activeType.value))
const preview = computed(() => marked(editContent.value || '') as string)

async function loadKits() {
  const { data } = await api.get(`/kits/card/${props.cardId}`)
  for (const k of data) kits.value[k.type] = k
}

async function generate(type: string) {
  generating.value = type
  error.value = ''
  try {
    const { data } = await api.post('/kits/generate', { cardId: props.cardId, type })
    kits.value[type] = data
    activeType.value = type
    editContent.value = data.content
    mode.value = 'preview'
  } catch {
    error.value = 'Generation failed — please try again.'
  } finally {
    generating.value = null
  }
}

function openKit(type: string) {
  const kit = kits.value[type]
  if (kit) {
    activeType.value = type
    editContent.value = kit.content
    mode.value = 'preview'
  } else {
    generate(type)
  }
}

async function save() {
  if (!activeType.value) return
  saving.value = true
  try {
    const kit = kits.value[activeType.value]
    await api.put(`/kits/${kit.id}`, { content: editContent.value })
    kits.value[activeType.value].content = editContent.value
  } finally {
    saving.value = false
  }
}

async function download() {
  if (!activeType.value) return
  if (editContent.value !== kits.value[activeType.value]?.content) await save()
  downloading.value = true
  try {
    const kit = kits.value[activeType.value]
    const response = await api.get(`/kits/${kit.id}/download`, { responseType: 'blob' })
    const slug = (t: string) => t.replace(/_/g, '-')
    const co = props.company.replace(/[^a-z0-9]/gi, '_').replace(/__+/g, '_')
    const filename = `${co}_${slug(activeType.value!)}.pdf`
    const url = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click()
    URL.revokeObjectURL(url)
  } finally {
    downloading.value = false
  }
}

loadKits()
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Generate Kit</h3>
      <span class="text-xs text-slate-600">Click to generate or open</span>
    </div>

    <!-- Kit type grid -->
    <div class="grid grid-cols-2 gap-2 mb-4">
      <button v-for="kt in KIT_TYPES" :key="kt.key"
        :class="[
          'relative flex flex-col items-start gap-1 px-3 py-3 rounded-xl border text-left transition-all',
          activeType === kt.key
            ? 'border-indigo-500/60 bg-indigo-900/30 shadow-sm'
            : kits[kt.key]
              ? 'border-indigo-700/40 bg-indigo-900/20 hover:border-indigo-600/60'
              : 'border-slate-700/60 bg-slate-800/80 hover:border-slate-600 hover:bg-slate-700/50',
          generating === kt.key ? 'opacity-70 cursor-wait' : 'cursor-pointer',
        ]"
        @click="openKit(kt.key)">
        <div class="flex items-center justify-between w-full">
          <span class="text-base">{{ kt.icon }}</span>
          <svg v-if="generating === kt.key" class="animate-spin h-3.5 w-3.5 text-indigo-400" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          <span v-else-if="kits[kt.key]"
            class="flex items-center justify-center w-4 h-4 bg-emerald-900/40 text-emerald-400 rounded-full border border-emerald-700/40">
            <svg class="h-2.5 w-2.5" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </span>
        </div>
        <span class="text-xs font-semibold text-slate-300 leading-tight">{{ kt.label }}</span>
      </button>
    </div>

    <p v-if="error" class="text-xs text-red-400 bg-red-900/20 border border-red-700/40 rounded-lg px-3 py-2 mb-3">
      {{ error }}
    </p>

    <!-- Kit editor -->
    <div v-if="activeType" class="space-y-2.5">

      <!-- Toolbar -->
      <div class="flex items-center gap-2 flex-wrap">
        <span class="text-sm font-semibold text-slate-200 mr-auto">{{ activeKitMeta?.label }}</span>

        <div class="flex rounded-lg border border-slate-700 overflow-hidden text-xs">
          <button @click="mode = 'preview'"
            :class="['px-3 py-1.5 font-medium transition', mode === 'preview' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200']">
            Preview
          </button>
          <button @click="mode = 'edit'"
            :class="['px-3 py-1.5 font-medium transition border-l border-slate-700', mode === 'edit' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200']">
            Edit
          </button>
        </div>

        <button @click="generate(activeType!)"
          class="flex items-center gap-1 text-xs text-slate-500 hover:text-indigo-400 transition font-medium">
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
          Regenerate
        </button>
      </div>

      <!-- Preview / Edit -->
      <div v-if="mode === 'preview'"
        class="kit-preview rounded-xl border border-slate-700/60 bg-slate-800 p-5 min-h-[260px] overflow-y-auto max-h-[480px]"
        v-html="preview" />
      <textarea v-else v-model="editContent" rows="16"
        class="w-full rounded-xl border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm leading-relaxed resize-y font-sans transition"
        placeholder="Generated content will appear here…" />

      <!-- Actions -->
      <div class="flex gap-2">
        <button @click="save" :disabled="saving"
          class="flex-1 py-2.5 border border-slate-700 hover:bg-slate-700 text-slate-300 text-sm rounded-xl transition font-medium disabled:opacity-50">
          {{ saving ? 'Saving…' : 'Save Edits' }}
        </button>
        <button @click="download" :disabled="downloading"
          class="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm rounded-xl font-semibold transition shadow-sm shadow-indigo-900/50">
          {{ downloading ? 'Preparing…' : '↓ Download PDF' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.kit-preview { font-size: 13px; line-height: 1.7; color: #cbd5e1; }
.kit-preview :deep(h1) { font-size: 1.2rem; font-weight: 700; margin: 0 0 .5rem; color: #f1f5f9; }
.kit-preview :deep(h2) { font-size: .95rem; font-weight: 700; margin: 1rem 0 .3rem; color: #f1f5f9; border-bottom: 1px solid #334155; padding-bottom: .25rem; }
.kit-preview :deep(h3) { font-size: .875rem; font-weight: 600; margin: .75rem 0 .2rem; color: #e2e8f0; }
.kit-preview :deep(p)  { margin: .35rem 0; }
.kit-preview :deep(ul) { margin: .3rem 0 .3rem 1.1rem; list-style: disc; }
.kit-preview :deep(li) { margin: .1rem 0; }
.kit-preview :deep(strong) { font-weight: 600; color: #f1f5f9; }
.kit-preview :deep(hr) { border: none; border-top: 1px solid #334155; margin: .75rem 0; }
</style>
