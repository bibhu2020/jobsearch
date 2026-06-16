<script setup lang="ts">
import type { PipelineCard } from '@/stores/pipeline'

defineProps<{ card: PipelineCard }>()
defineEmits<{ (e: 'click'): void }>()

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const days = Math.floor(diff / 86400000)
  if (days === 0) return 'Today'
  if (days === 1) return 'Yesterday'
  return `${days}d ago`
}
</script>

<template>
  <div
    @click="$emit('click')"
    class="bg-white rounded-lg border border-gray-200 p-3 shadow-sm hover:shadow-md cursor-pointer transition select-none"
  >
    <p class="text-sm font-semibold text-gray-900 truncate">{{ card.title || 'Untitled Position' }}</p>
    <p class="text-xs text-gray-500 truncate mt-0.5">{{ card.company }}</p>
    <div class="flex items-center justify-between mt-2">
      <span v-if="card.location" class="text-xs text-gray-400 truncate max-w-[120px]">📍 {{ card.location }}</span>
      <span class="text-xs text-gray-400 ml-auto">{{ timeAgo(card.created_at) }}</span>
    </div>
  </div>
</template>
