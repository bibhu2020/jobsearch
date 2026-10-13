import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export type RunStatus =
  | 'queued' | 'running' | 'needs_input' | 'awaiting_review'
  | 'submitting' | 'submitted' | 'failed' | 'cancelled'

export const TERMINAL: RunStatus[] = ['submitted', 'failed', 'cancelled']

export type SessionSite = 'linkedin' | 'dice'
export const SESSION_SITE_LABELS: Record<SessionSite, string> = { linkedin: 'LinkedIn', dice: 'Dice' }

export interface FieldRecord {
  id: string
  label: string
  type: string
  required: boolean
  value: any
  source: 'default' | 'profile' | 'llm' | 'file' | 'user'
  confidence: number
  sensitive?: boolean
}

export interface ApplicationRun {
  id: string
  kind: 'apply' | 'login'
  pipeline_card_id: number | null
  status: RunStatus
  site: string | null
  channel: string | null
  apply_url: string | null
  auto_submitted: boolean
  message: string | null
  fields: FieldRecord[]
  has_screenshot: boolean
  started_at: string
  finished_at: string | null
  live?: {
    screenshot: string | null; log: string[]; step: string
    needs?: { kind: 'verification'; email: string; sender: string } | { kind: 'signin'; site: string; label: string } | null
  } | null
}

export interface ApplicationDefaults {
  firstName?: string; lastName?: string; preferredName?: string; phone?: string
  city?: string; state?: string; country?: string; postalCode?: string
  linkedinUrl?: string; githubUrl?: string; portfolioUrl?: string
  workAuthorizedCountries?: string[]; requiresSponsorship?: boolean
  noticePeriod?: string; earliestStartDate?: string
  salaryExpectation?: string; salaryCurrency?: string
  willingToRelocate?: boolean; remotePreference?: string
  yearsExperience?: string; highestEducation?: string
  gender?: string; race?: string; veteranStatus?: string; disabilityStatus?: string
  customAnswers?: { question: string; answer: string }[]
}

export interface ApplySettings {
  encryptionConfigured: boolean
  gmailConfigured: boolean
  portalPasswordSet: boolean
  autoSubmit: boolean
  easyApplyDailyCap: number
  defaults: ApplicationDefaults
  gmail: { connected: boolean; email: string | null }
  sites: Record<SessionSite, { connected: boolean; updatedAt: string | null }>
}

export const useApplyStore = defineStore('apply', () => {
  const settings = ref<ApplySettings | null>(null)

  async function fetchSettings() {
    const { data } = await api.get('/apply/settings')
    settings.value = data
    return data as ApplySettings
  }

  async function saveSettings(payload: {
    portalPassword?: string; autoSubmit?: boolean; easyApplyDailyCap?: number; defaults?: ApplicationDefaults
  }) {
    const { data } = await api.put('/apply/settings', payload)
    settings.value = data
    return data as ApplySettings
  }

  async function start(cardId: number): Promise<string> {
    const { data } = await api.post(`/apply/cards/${cardId}/start`)
    return data.runId
  }

  async function getRun(runId: string): Promise<ApplicationRun> {
    const { data } = await api.get(`/apply/runs/${runId}`)
    return data
  }

  async function cardRuns(cardId: number): Promise<ApplicationRun[]> {
    const { data } = await api.get(`/apply/cards/${cardId}/runs`)
    return data
  }

  /** Object URL for the stored confirmation screenshot (fetched with the auth header). */
  async function screenshotUrl(runId: string): Promise<string> {
    const { data } = await api.get(`/apply/runs/${runId}/screenshot`, { responseType: 'blob' })
    return URL.createObjectURL(data)
  }

  async function provideVerification(runId: string, value: string) {
    await api.post(`/apply/runs/${runId}/verification`, { value })
  }

  async function connectSite(site: SessionSite): Promise<string> {
    const { data } = await api.post(`/integrations/sites/${site}/connect`)
    return data.runId
  }

  async function disconnectSite(site: SessionSite) {
    await api.delete(`/integrations/sites/${site}`)
    await fetchSettings()
  }

  async function control(runId: string, action: 'resume' | 'submit' | 'cancel' | 'mark-applied' | 'finish-login') {
    await api.post(`/apply/runs/${runId}/${action}`)
  }

  async function input(runId: string, payload: { kind: 'click'; x: number; y: number } | { kind: 'type'; text: string } | { kind: 'key'; key: string } | { kind: 'scroll'; dy: number }) {
    await api.post(`/apply/runs/${runId}/input`, payload)
  }

  async function connectGmail() {
    const { data } = await api.get('/integrations/gmail/auth-url')
    window.location.href = data.url
  }

  async function disconnectGmail() {
    await api.delete('/integrations/gmail')
    await fetchSettings()
  }

  return { settings, fetchSettings, saveSettings, start, getRun, cardRuns, screenshotUrl, provideVerification, connectSite, disconnectSite, control, input, connectGmail, disconnectGmail }
})
