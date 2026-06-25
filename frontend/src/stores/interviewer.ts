import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export interface Candidate {
  id: number
  project_id: number
  name: string
  email: string | null
  resume_path: string | null
  resume_text: string | null
  ai_summary: string | null
  ai_score: number
  ai_matching: string[]
  ai_gaps: string[]
  ai_recommendation: string
  notes: string | null
  stage: string
  position: number
  card_id: number
}

export interface Project {
  id: number
  title: string
  description: string | null
  candidate_count: number
  created_at: string
  cards?: Candidate[]
}

export const useInterviewerStore = defineStore('interviewer', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const loading = ref(false)
  const scanning = ref(false)
  const uploading = ref(false)

  async function fetchProjects() {
    loading.value = true
    try {
      const { data } = await api.get('/interviewer/projects')
      projects.value = data
    } finally {
      loading.value = false
    }
  }

  async function createProject(title: string, description?: string) {
    const { data } = await api.post('/interviewer/projects', { title, description })
    projects.value.unshift({ ...data, candidate_count: 0 })
    return data
  }

  async function deleteProject(id: number) {
    await api.delete(`/interviewer/projects/${id}`)
    projects.value = projects.value.filter(p => p.id !== id)
  }

  async function fetchProject(id: number) {
    loading.value = true
    try {
      const { data } = await api.get(`/interviewer/projects/${id}`)
      currentProject.value = data
    } finally {
      loading.value = false
    }
  }

  async function addCandidate(projectId: number, name: string, email?: string, resumeText?: string) {
    const { data } = await api.post(`/interviewer/projects/${projectId}/candidates`, {
      name, email, resumeText,
    })
    if (currentProject.value?.cards) {
      currentProject.value.cards.push(data)
    }
    return data
  }

  async function uploadResume(projectId: number, candidateId: number, file: File) {
    uploading.value = true
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await api.post(
        `/interviewer/projects/${projectId}/candidates/${candidateId}/upload-resume`,
        form,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      )
      await refreshCandidate(projectId, candidateId)
      return data
    } finally {
      uploading.value = false
    }
  }

  async function scanResume(projectId: number, candidateId: number, jobDescription?: string) {
    scanning.value = true
    try {
      const { data } = await api.post(
        `/interviewer/projects/${projectId}/candidates/${candidateId}/scan`,
        { jobDescription },
      )
      await refreshCandidate(projectId, candidateId)
      return data
    } finally {
      scanning.value = false
    }
  }

  async function updateNotes(projectId: number, candidateId: number, notes: string) {
    await api.put(
      `/interviewer/projects/${projectId}/candidates/${candidateId}/notes`,
      { notes },
    )
    if (currentProject.value?.cards) {
      const card = currentProject.value.cards.find(c => c.id === candidateId)
      if (card) card.notes = notes
    }
  }

  async function deleteCandidate(projectId: number, candidateId: number) {
    await api.delete(`/interviewer/projects/${projectId}/candidates/${candidateId}`)
    if (currentProject.value?.cards) {
      currentProject.value.cards = currentProject.value.cards.filter(c => c.id !== candidateId)
    }
  }

  async function moveCard(cardId: number, stage: string, position: number) {
    if (!currentProject.value) return
    const { data } = await api.put(`/interviewer/cards/${cardId}/move`, { stage, position })
    currentProject.value = data
  }

  async function refreshCandidate(projectId: number, candidateId: number) {
    const { data } = await api.get(`/interviewer/projects/${projectId}/candidates/${candidateId}`)
    if (currentProject.value?.cards) {
      const idx = currentProject.value.cards.findIndex(c => c.id === candidateId)
      if (idx !== -1) currentProject.value.cards[idx] = data
    }
    return data
  }

  return {
    projects, currentProject, loading, scanning, uploading,
    fetchProjects, createProject, deleteProject,
    fetchProject, addCandidate, uploadResume, scanResume,
    updateNotes, deleteCandidate, moveCard, refreshCandidate,
  }
})
