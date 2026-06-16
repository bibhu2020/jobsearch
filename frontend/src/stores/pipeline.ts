import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export type Stage = 'wishlist' | 'applied' | 'interviewing' | 'offer' | 'rejected'

export interface PipelineCard {
  id: number
  job_id: number
  stage: Stage
  position: number
  notes: string | null
  title: string
  company: string
  location: string
  description: string
  url: string | null
  created_at: string
}

export const STAGES: { key: Stage; label: string; color: string }[] = [
  { key: 'wishlist',     label: 'Wishlist',     color: 'bg-violet-50  border-violet-200' },
  { key: 'applied',      label: 'Applied',      color: 'bg-blue-50    border-blue-200' },
  { key: 'interviewing', label: 'Interviewing', color: 'bg-amber-50   border-amber-200' },
  { key: 'offer',        label: 'Offer',        color: 'bg-emerald-50 border-emerald-200' },
  { key: 'rejected',     label: 'Rejected',     color: 'bg-red-50     border-red-200' },
]

export const usePipelineStore = defineStore('pipeline', () => {
  const cards = ref<PipelineCard[]>([])
  const loading = ref(false)

  const byStage = computed(() => {
    const map: Record<Stage, PipelineCard[]> = {
      wishlist: [], applied: [], interviewing: [], offer: [], rejected: [],
    }
    for (const c of cards.value) {
      if (map[c.stage]) map[c.stage].push(c)
    }
    for (const stage of Object.keys(map) as Stage[]) {
      map[stage].sort((a, b) => a.position - b.position)
    }
    return map
  })

  async function fetchCards() {
    loading.value = true
    try {
      const { data } = await api.get('/pipeline/cards')
      cards.value = data
    } finally {
      loading.value = false
    }
  }

  async function addJob(payload: { url?: string; text?: string }) {
    await api.post('/jobs', payload)
    await fetchCards()
  }

  async function moveCard(cardId: number, stage: Stage, position: number) {
    cards.value = cards.value.map(c =>
      c.id === cardId ? { ...c, stage, position } : c,
    )
    await api.put(`/pipeline/cards/${cardId}/move`, { stage, position })
  }

  async function updateNotes(cardId: number, notes: string) {
    await api.put(`/pipeline/cards/${cardId}/notes`, { notes })
    cards.value = cards.value.map(c => c.id === cardId ? { ...c, notes } : c)
  }

  async function deleteCard(cardId: number) {
    await api.delete(`/pipeline/cards/${cardId}`)
    cards.value = cards.value.filter(c => c.id !== cardId)
  }

  return { cards, byStage, loading, fetchCards, addJob, moveCard, updateNotes, deleteCard }
})
