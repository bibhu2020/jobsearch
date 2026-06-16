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
  <div class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="emit('close')">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
      <div class="flex items-center justify-between p-5 border-b">
        <h2 class="text-lg font-semibold text-gray-800">Add a Job</h2>
        <button @click="emit('close')" class="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
      </div>

      <div class="p-5">
        <div class="flex gap-1 bg-gray-100 p-1 rounded-lg mb-5">
          <button v-for="t in ['url', 'text']" :key="t"
            :class="['flex-1 py-1.5 rounded-md text-sm font-medium transition', tab === t ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700']"
            @click="tab = t as any">
            {{ t === 'url' ? '🔗 Paste URL' : '📋 Paste Text' }}
          </button>
        </div>

        <div v-if="tab === 'url'">
          <label class="block text-sm font-medium text-gray-700 mb-1">Job posting URL</label>
          <input v-model="url" type="url" placeholder="https://company.com/jobs/position"
            class="w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-sm" />
          <p class="text-xs text-gray-400 mt-1">We'll automatically extract the job details</p>
        </div>
        <div v-else>
          <label class="block text-sm font-medium text-gray-700 mb-1">Job description text</label>
          <textarea v-model="text" rows="6" placeholder="Paste the full job description here…"
            class="w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-sm resize-none" />
        </div>

        <p v-if="error" class="text-red-600 text-sm mt-2">{{ error }}</p>
      </div>

      <div class="flex gap-3 p-5 border-t">
        <button @click="emit('close')" class="flex-1 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 transition">
          Cancel
        </button>
        <button @click="submit" :disabled="loading"
          class="flex-1 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition">
          {{ loading ? 'Adding…' : 'Add to Wishlist' }}
        </button>
      </div>
    </div>
  </div>
</template>
