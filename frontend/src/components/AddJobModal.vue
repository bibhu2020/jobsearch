<script setup lang="ts">
import { ref } from 'vue'
import { usePipelineStore } from '@/stores/pipeline'

const emit = defineEmits<{ (e: 'close'): void }>()
const store = usePipelineStore()
const tab = ref<'url' | 'text'>('url')
const url = ref('')
const text = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  loading.value = true
  try {
    if (tab.value === 'url') {
      if (!url.value.trim()) return
      await store.addJob({ url: url.value.trim() })
    } else {
      if (!text.value.trim()) return
      await store.addJob({ text: text.value.trim() })
    }
    emit('close')
  } catch (e: any) {
    error.value = e.response?.data?.message || 'Failed to add job'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" @click.self="emit('close')">
    <div class="bg-slate-800 rounded-2xl shadow-2xl w-full max-w-lg border border-slate-700/60">

      <!-- Header -->
      <div class="flex items-center justify-between px-6 pt-6 pb-4">
        <div>
          <h2 class="text-base font-bold text-slate-100">Add a Job</h2>
          <p class="text-xs text-slate-500 mt-0.5">AI will extract the details automatically</p>
        </div>
        <button @click="emit('close')"
          class="w-8 h-8 flex items-center justify-center rounded-lg text-slate-500 hover:text-slate-200 hover:bg-slate-700 transition">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Tabs -->
      <div class="px-6 pb-4">
        <div class="flex gap-1 bg-slate-900/60 p-1 rounded-xl border border-slate-700/40">
          <button v-for="t in [
            { key: 'url', label: 'Paste URL', icon: '🔗' },
            { key: 'text', label: 'Paste Text', icon: '📋' },
          ]" :key="t.key"
            :class="[
              'flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-all',
              tab === t.key
                ? 'bg-slate-700 shadow-sm text-slate-100'
                : 'text-slate-500 hover:text-slate-300',
            ]"
            @click="tab = t.key as any">
            <span>{{ t.icon }}</span>
            {{ t.label }}
          </button>
        </div>
      </div>

      <!-- Input area -->
      <div class="px-6 pb-2">
        <div v-if="tab === 'url'">
          <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Job posting URL</label>
          <input v-model="url" type="url" placeholder="https://company.com/jobs/senior-engineer"
            class="w-full rounded-xl border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm transition"
            @keydown.enter="submit" />
          <p class="text-xs text-slate-600 mt-2 flex items-center gap-1">
            <svg class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
            </svg>
            We'll scrape and extract job title, company, and description
          </p>
        </div>
        <div v-else>
          <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Job description text</label>
          <textarea v-model="text" rows="7" placeholder="Paste the full job posting here — title, company, description, requirements…"
            class="w-full rounded-xl border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm resize-none transition" />
        </div>

        <div v-if="error"
          class="flex items-center gap-2 mt-3 text-sm text-red-400 bg-red-900/20 border border-red-700/40 rounded-lg px-3 py-2">
          <svg class="h-4 w-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd"/>
          </svg>
          {{ error }}
        </div>
      </div>

      <!-- Footer -->
      <div class="flex gap-3 px-6 py-4 border-t border-slate-700/60 mt-2">
        <button @click="emit('close')"
          class="flex-1 py-2.5 border border-slate-600 rounded-xl text-sm text-slate-400 hover:bg-slate-700 hover:text-slate-200 transition font-medium">
          Cancel
        </button>
        <button @click="submit" :disabled="loading"
          class="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-sm font-semibold transition shadow-sm shadow-indigo-900/50">
          <span v-if="loading" class="flex items-center justify-center gap-2">
            <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Adding…
          </span>
          <span v-else>Add to Wishlist</span>
        </button>
      </div>
    </div>
  </div>
</template>
