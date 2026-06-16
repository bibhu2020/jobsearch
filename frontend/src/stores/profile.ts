import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useProfileStore = defineStore('profile', () => {
  const profile = ref<any>(null)
  const analyzing = ref(false)
  const uploading = ref(false)

  async function fetchProfile() {
    const { data } = await api.get('/profile')
    profile.value = data
  }

  async function update(payload: { name?: string; linkedinUrl?: string; location?: string; profileSummary?: string; skills?: string[] }) {
    const { data } = await api.put('/profile', payload)
    profile.value = data
  }

  async function uploadResume(file: File) {
    uploading.value = true
    try {
      const form = new FormData()
      form.append('file', file)
      await api.post('/profile/resume', form, { headers: { 'Content-Type': 'multipart/form-data' } })
      await fetchProfile()
    } finally {
      uploading.value = false
    }
  }

  async function analyze() {
    analyzing.value = true
    try {
      const { data } = await api.post('/profile/analyze')
      await fetchProfile()
      return data
    } finally {
      analyzing.value = false
    }
  }

  return { profile, analyzing, uploading, fetchProfile, update, uploadResume, analyze }
})
