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

export interface WorkflowStep {
  name: string
  status: 'queued' | 'in_progress' | 'completed'
  conclusion: 'success' | 'failure' | 'skipped' | null
}

export interface WorkflowRun {
  runId: number
  status: 'queued' | 'in_progress' | 'completed'
  conclusion: 'success' | 'failure' | 'cancelled' | null
  createdAt: string
  runUrl: string
  steps: WorkflowStep[]
}

export type WorkflowStatus = 'idle' | 'dispatching' | 'running' | 'completed' | 'error'

export const useSuggestionsStore = defineStore('suggestions', () => {
  const suggestions = ref<Suggestion[]>([])
  const loading = ref(false)
  const syncing = ref(false)
  const detectedCountry = ref('')
  const detectingCountry = ref(false)

  // Workflow lifecycle state
  const workflowStatus = ref<WorkflowStatus>('idle')
  const workflowMessage = ref('')
  const workflowRun = ref<WorkflowRun | null>(null)
  const triggerTime = ref<number>(0)
  const autoImported = ref(false)

  let _pollTimer: ReturnType<typeof setInterval> | null = null

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
    workflowRun.value = null
    autoImported.value = false
    _stopPolling()

    try {
      const { data } = await api.post('/suggestions/trigger-action', {
        keywords: keywords?.trim() || '',
        location: country?.trim() || '',
      })

      if (data?.error) {
        workflowStatus.value = 'error'
        workflowMessage.value = data.error
        return
      }

      triggerTime.value = Date.now()
      workflowStatus.value = 'running'
      workflowMessage.value = 'Workflow dispatched — waiting for GitHub Actions to pick it up…'
      _startPolling()
    } catch (err: any) {
      workflowStatus.value = 'error'
      workflowMessage.value =
        err?.response?.data?.error || err?.response?.data?.message || 'Failed to trigger GitHub Actions workflow.'
    }
  }

  function _startPolling() {
    _stopPolling()
    // First check after 8s to give GitHub time to register the run
    const firstCheck = setTimeout(() => _pollOnce(), 8000)
    _pollTimer = setInterval(() => _pollOnce(), 12000) as any
    // Store the initial timeout ref so we can clear it
    ;((_pollTimer as any)._initialTimeout = firstCheck)
  }

  function _stopPolling() {
    if (_pollTimer !== null) {
      clearInterval(_pollTimer)
      const t = (_pollTimer as any)._initialTimeout
      if (t) clearTimeout(t)
      _pollTimer = null
    }
  }

  async function _pollOnce() {
    try {
      const { data } = await api.get<WorkflowRun | null>('/suggestions/workflow-run')
      if (!data) return

      // Ignore stale runs from before our trigger
      const runCreated = new Date(data.createdAt).getTime()
      if (runCreated < triggerTime.value - 30_000) return

      workflowRun.value = data

      if (data.status === 'completed') {
        _stopPolling()
        workflowStatus.value = 'completed'

        if (data.conclusion === 'success' && !autoImported.value) {
          autoImported.value = true
          workflowMessage.value = 'Search complete — importing results…'
          await importResults()
          workflowMessage.value = 'Done! Results imported and ready below.'
        } else if (data.conclusion !== 'success') {
          workflowStatus.value = 'error'
          workflowMessage.value = `Workflow ${data.conclusion ?? 'failed'}. Click the run link for details.`
        }
      } else {
        workflowMessage.value = data.status === 'in_progress'
          ? 'Agent is running job search across 10 sources…'
          : 'Waiting for a GitHub Actions runner to pick up the job…'
      }
    } catch {
      // network error — keep polling
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

  function dismissWorkflow() {
    _stopPolling()
    workflowStatus.value = 'idle'
    workflowMessage.value = ''
    workflowRun.value = null
  }

  return {
    suggestions, loading, syncing,
    detectedCountry, detectingCountry,
    workflowStatus, workflowMessage, workflowRun,
    fetchSuggestions, sync, triggerAction, importResults,
    addToWishlist, dismiss, detectCountry, dismissWorkflow,
  }
})
