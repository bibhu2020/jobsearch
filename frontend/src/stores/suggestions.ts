import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export interface Suggestion {
  id: number
  title: string
  company: string
  location: string
  description: string
  url: string | null
  match_reason: string
  match_score: number
  matching: string[]
  gaps: string[]
  recommendation: 'apply' | 'consider' | 'skip'
  source: string
  status: 'pending' | 'added' | 'dismissed'
  search_date: string
}

export type WorkflowStatus = 'idle' | 'dispatching' | 'dispatched' | 'error'

export const useSuggestionsStore = defineStore('suggestions', () => {
  const suggestions = ref<Suggestion[]>([])
  const loading = ref(false)
  const syncing = ref(false)
  const detectedCountry = ref('')
  const detectingCountry = ref(false)
  const workflowStatus = ref<WorkflowStatus>('idle')
  const workflowMessage = ref('')

  async function detectCountry() {
    if (detectedCountry.value || detectingCountry.value) return
    detectingCountry.value = true
    try {
      const res = await fetch('https://ipapi.co/json/')
      const data = await res.json()
      detectedCountry.value = data.country_name || ''
    } catch {
      detectedCountry.value = ''
    } finally {
      detectingCountry.value = false
    }
  }

  async function fetchSuggestions() {
    loading.value = true
    try {
      const { data } = await api.get('/suggestions')
      suggestions.value = data
    } finally {
      loading.value = false
    }
  }

  async function triggerAction(keywords?: string, country?: string) {
    workflowStatus.value = 'dispatching'
    workflowMessage.value = ''
    try {
      await api.post('/suggestions/trigger-action', {
        keywords: keywords?.trim() || '',
        location: country?.trim() || '',
      })
      workflowStatus.value = 'dispatched'
      workflowMessage.value =
        'GitHub Actions search started — results will be committed in ~5 minutes. Click "Import Results" once it finishes.'
    } catch {
      workflowStatus.value = 'error'
      workflowMessage.value = 'Failed to trigger GitHub Actions workflow. Check GITHUB_TOKEN.'
    }
  }

  async function importResults() {
    loading.value = true
    try {
      const { data } = await api.post('/suggestions/import')
      await fetchSuggestions()
      return data.imported as number
    } finally {
      loading.value = false
    }
  }

  async function sync(keywords?: string, country?: string) {
    syncing.value = true
    try {
      await api.post('/suggestions/import')
      await api.post('/suggestions/search', {
        keywords: keywords || '',
        country: country !== undefined ? country : detectedCountry.value,
      })
      await fetchSuggestions()
    } finally {
      syncing.value = false
    }
  }

  async function addToWishlist(id: number) {
    await api.post(`/suggestions/${id}/add-to-wishlist`)
    suggestions.value = suggestions.value.filter(s => s.id !== id)
  }

  async function dismiss(id: number) {
    await api.put(`/suggestions/${id}/dismiss`)
    suggestions.value = suggestions.value.filter(s => s.id !== id)
  }

  return {
    suggestions, loading, syncing,
    detectedCountry, detectingCountry,
    workflowStatus, workflowMessage,
    fetchSuggestions, sync, triggerAction, importResults, addToWishlist, dismiss, detectCountry,
  }
})
