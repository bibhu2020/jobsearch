import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<{ id: number; email: string; name?: string } | null>(null)
  const mode = ref<'candidate' | 'interviewer'>(
    (localStorage.getItem('mode') as 'candidate' | 'interviewer') || 'candidate',
  )
  const isAuthenticated = computed(() => !!token.value)
  const isInterviewer = computed(() => mode.value === 'interviewer')

  /** Sign-in is Google-only: the browser leaves the app and returns to /auth/callback. */
  function loginWithGoogle() {
    window.location.href = '/api/auth/google'
  }

  /** Called by AuthCallbackView with the session token from the Google redirect. */
  async function completeLogin(newToken: string) {
    token.value = newToken
    localStorage.setItem('token', newToken)
    await fetchMode()
    router.replace(mode.value === 'interviewer' ? '/interviewer' : '/pipeline')
  }

  async function fetchMode() {
    try {
      const { data } = await api.get('/interviewer/mode')
      mode.value = data.mode ?? 'candidate'
      localStorage.setItem('mode', mode.value)
    } catch { /* ignore */ }
  }

  async function switchMode(newMode: 'candidate' | 'interviewer') {
    await api.put('/interviewer/mode', { mode: newMode })
    mode.value = newMode
    localStorage.setItem('mode', newMode)
    router.push(newMode === 'interviewer' ? '/interviewer' : '/pipeline')
  }

  function logout() {
    token.value = null
    user.value = null
    mode.value = 'candidate'
    localStorage.removeItem('token')
    localStorage.removeItem('mode')
    router.push('/login')
  }

  return { token, user, mode, isAuthenticated, isInterviewer, loginWithGoogle, completeLogin, logout, fetchMode, switchMode }
})
