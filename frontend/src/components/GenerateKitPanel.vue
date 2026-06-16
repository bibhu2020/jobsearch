<script setup lang="ts">
import { ref, computed } from 'vue'
import { marked } from 'marked'
import api from '@/api'

const props = defineProps<{
  cardId: number
  jobTitle: string
  company: string
}>()

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
  { key: 'cover_letter',        label: 'Cover Letter',        icon: '✉️',  doc: true },
  { key: 'resume',              label: 'Tailored Resume',     icon: '📄',  doc: true },
  { key: 'interview_questions', label: 'Interview Questions', icon: '🎯',  doc: false },
  { key: 'company_brief',       label: 'Company Brief',       icon: '🏢',  doc: false },
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
    mode.value = 'preview'   // show preview immediately after generation
  } catch {
    error.value = 'Generation failed. Please try again.'
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
  // Auto-save any unsaved edits first
  if (editContent.value !== kits.value[activeType.value]?.content) await save()
  downloading.value = true
  try {
    const kit = kits.value[activeType.value]
    const response = await api.get(`/kits/${kit.id}/download`, { responseType: 'blob' })
    const slug = (t: string) => t.replace(/_/g, '-')
    const co = props.company.replace(/[^a-z0-9]/gi, '_').replace(/__+/g, '_')
    const filename = `${co}_${slug(activeType.value)}.pdf`
    const url = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    downloading.value = false
  }
}

loadKits()
</script>

<template>
  <div class="mt-4">
    <h3 class="text-sm font-semibold text-gray-700 mb-3">Generate Kit</h3>

    <!-- Kit type buttons -->
    <div class="grid grid-cols-2 gap-2 mb-4">
      <button v-for="kt in KIT_TYPES" :key="kt.key"
        :class="[
          'flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium transition',
          activeType === kt.key
            ? 'border-indigo-400 bg-indigo-100 text-indigo-800'
            : kits[kt.key]
              ? 'border-indigo-300 bg-indigo-50 text-indigo-700'
              : 'border-gray-200 bg-white text-gray-700 hover:border-indigo-200 hover:bg-indigo-50',
          generating === kt.key ? 'opacity-70 cursor-wait' : 'cursor-pointer',
        ]"
        @click="openKit(kt.key)">
        <span>{{ kt.icon }}</span>
        <span class="truncate">{{ kt.label }}</span>
        <svg v-if="generating === kt.key" class="animate-spin h-3.5 w-3.5 ml-auto shrink-0" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
        <span v-else-if="kits[kt.key]" class="ml-auto text-emerald-500 text-xs shrink-0">✓</span>
      </button>
    </div>

    <p v-if="error" class="text-red-500 text-sm mb-3">{{ error }}</p>

    <div v-if="activeType" class="space-y-2">
      <!-- Toolbar: label + tabs + regenerate -->
      <div class="flex items-center justify-between gap-2">
        <span class="text-sm font-medium text-gray-700">{{ activeKitMeta?.label }}</span>
        <div class="flex items-center gap-2 ml-auto">
          <div class="flex rounded-md border border-gray-200 overflow-hidden text-xs">
            <button @click="mode = 'preview'"
              :class="['px-3 py-1 transition', mode === 'preview' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50']">
              Preview
            </button>
            <button @click="mode = 'edit'"
              :class="['px-3 py-1 transition', mode === 'edit' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50']">
              Edit
            </button>
          </div>
          <button @click="generate(activeType!)"
            class="text-xs text-indigo-500 hover:text-indigo-700 transition whitespace-nowrap">
            ↺ Regenerate
          </button>
        </div>
      </div>

      <!-- PREVIEW mode: rendered markdown document -->
      <div v-if="mode === 'preview'"
        class="kit-preview rounded-lg border border-gray-200 bg-white p-5 min-h-[280px] overflow-y-auto max-h-[480px]"
        v-html="preview" />

      <!-- EDIT mode: clean textarea -->
      <textarea v-else v-model="editContent" rows="18"
        class="w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-sm leading-relaxed resize-y font-sans"
        placeholder="Generated content will appear here…" />

      <!-- Actions -->
      <div class="flex gap-2 pt-1">
        <button @click="save" :disabled="saving"
          class="flex-1 py-2 border border-gray-300 hover:bg-gray-50 text-gray-700 text-sm rounded-lg transition disabled:opacity-50">
          {{ saving ? 'Saving…' : '💾 Save Edits' }}
        </button>
        <button @click="download" :disabled="downloading"
          class="flex-1 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm rounded-lg font-medium transition">
          {{ downloading ? 'Preparing…' : '⬇️ Download PDF' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.kit-preview { font-size: 13px; line-height: 1.65; color: #1f2937; }
.kit-preview :deep(h1) { font-size: 1.25rem; font-weight: 700; margin: 0 0 .6rem; color: #111827; }
.kit-preview :deep(h2) { font-size: 1rem; font-weight: 700; margin: 1rem 0 .35rem; color: #111827; border-bottom: 1px solid #e5e7eb; padding-bottom: .2rem; }
.kit-preview :deep(h3) { font-size: .9rem; font-weight: 600; margin: .75rem 0 .2rem; color: #374151; }
.kit-preview :deep(p)  { margin: .4rem 0; }
.kit-preview :deep(ul) { margin: .3rem 0 .3rem 1.25rem; list-style: disc; }
.kit-preview :deep(li) { margin: .15rem 0; }
.kit-preview :deep(strong) { font-weight: 600; }
.kit-preview :deep(hr) { border: none; border-top: 1px solid #e5e7eb; margin: .75rem 0; }
</style>
