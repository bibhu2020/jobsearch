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

// How long to keep polling before giving up (in poll ticks of ~12s each)
const MAX_POLL_ATTEMPTS = 30  // ~6 minutes

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

  let _pollIntervalId: ReturnType<typeof setInterval> | null = null
  let _pollTimeoutId: ReturnType<typeof setTimeout> | null = null
  let _pollAttempts = 0

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
    triggerTime.value = Date.now()
    _stopPolling()

    let dispatched = false
    try {
      const { data } = await api.post('/suggestions/trigger-action', {
        keywords: keywords?.trim() || '',
        location: country?.trim() || '',
      })

      if (data?.error) {
        // Application-level errors (no token, no profile) — workflow definitely did not run
        workflowStatus.value = 'error'
        workflowMessage.value = data.error
        return
      }
      dispatched = true
    } catch {
      // HTTP error — the dispatch request may have already reached GitHub before the
      // gateway threw. Treat as "maybe dispatched" and let polling confirm it.
      dispatched = true
    }

    if (dispatched) {
      workflowStatus.value = 'running'
      workflowMessage.value = 'Workflow dispatched — waiting for GitHub Actions to pick it up…'
      _startPolling()
    }
  }

  function _startPolling() {
    _stopPolling()
    _pollAttempts = 0
    // First check at 8s (give GitHub time to register the run), then every 12s
    _pollTimeoutId = setTimeout(() => {
      _pollOnce()
      _pollIntervalId = setInterval(_pollOnce, 12_000)
    }, 8_000)
  }

  function _stopPolling() {
    if (_pollTimeoutId !== null) { clearTimeout(_pollTimeoutId); _pollTimeoutId = null }
    if (_pollIntervalId !== null) { clearInterval(_pollIntervalId); _pollIntervalId = null }
  }

  async function _pollOnce() {
    _pollAttempts++

    // Give up after MAX_POLL_ATTEMPTS with no matching run found
    if (_pollAttempts > MAX_POLL_ATTEMPTS) {
      _stopPolling()
      workflowStatus.value = 'error'
      workflowMessage.value = 'No GitHub Actions run detected. Check the Actions tab on GitHub.'
      return
    }

    try {
      const { data } = await api.get<WorkflowRun | null>('/suggestions/workflow-run')
      if (!data) return

      // Ignore runs that started before our trigger (stale previous runs)
      const runCreated = new Date(data.createdAt).getTime()
      if (runCreated < triggerTime.value - 30_000) return

      // Found our run — reset the timeout counter
      _pollAttempts = 0
      workflowRun.value = data

      if (data.status === 'completed') {
        _stopPolling()
        workflowStatus.value = 'completed'

        if (data.conclusion === 'success' && !autoImported.value) {
          autoImported.value = true
          workflowMessage.value = 'Search complete — importing results…'
          await importResults()
          workflowMessage.value = 'Done! New job suggestions are ready below.'
        } else if (data.conclusion !== 'success') {
          workflowStatus.value = 'error'
          workflowMessage.value = `Workflow ${data.conclusion ?? 'failed'}. See the run link for details.`
        }
      } else {
        workflowMessage.value = data.status === 'in_progress'
          ? 'Agent is running job search across 10 sources…'
          : 'Waiting for a GitHub Actions runner to pick up the job…'
      }
    } catch {
      // network hiccup — keep polling
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
