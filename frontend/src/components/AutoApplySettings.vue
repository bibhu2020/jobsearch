<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApplyStore, type ApplicationDefaults } from '@/stores/apply'

const store = useApplyStore()
const route = useRoute()
const router = useRouter()

const password = ref('')
const passwordMsg = ref('')
const defaultsMsg = ref('')
const errorMsg = ref('')
const gmailMsg = ref('')
const saving = ref(false)

const DECLINE = 'Decline to answer'
const form = reactive<Required<Omit<ApplicationDefaults, 'workAuthorizedCountries' | 'requiresSponsorship' | 'willingToRelocate' | 'customAnswers'>> & {
  workAuthorizedCountries: string; requiresSponsorship: '' | 'yes' | 'no'; willingToRelocate: '' | 'yes' | 'no'
  customAnswers: { question: string; answer: string }[]
}>({
  firstName: '', lastName: '', preferredName: '', phone: '',
  city: '', state: '', country: '', postalCode: '',
  linkedinUrl: '', githubUrl: '', portfolioUrl: '',
  workAuthorizedCountries: '', requiresSponsorship: '',
  noticePeriod: '', earliestStartDate: '',
  salaryExpectation: '', salaryCurrency: 'USD',
  willingToRelocate: '', remotePreference: 'any',
  yearsExperience: '', highestEducation: '',
  gender: DECLINE, race: DECLINE, veteranStatus: DECLINE, disabilityStatus: DECLINE,
  customAnswers: [],
})

const TEXT_FIELDS: { key: keyof typeof form; label: string; placeholder?: string; required?: boolean; wide?: boolean }[] = [
  { key: 'firstName', label: 'Legal first name', required: true },
  { key: 'lastName', label: 'Legal last name', required: true },
  { key: 'preferredName', label: 'Preferred name' },
  { key: 'phone', label: 'Phone', placeholder: '+1 555 010 0100', required: true },
  { key: 'city', label: 'City' },
  { key: 'state', label: 'State / province' },
  { key: 'country', label: 'Country' },
  { key: 'postalCode', label: 'Postal code' },
  { key: 'linkedinUrl', label: 'LinkedIn URL', wide: true },
  { key: 'githubUrl', label: 'GitHub URL' },
  { key: 'portfolioUrl', label: 'Portfolio / website' },
  { key: 'salaryExpectation', label: 'Salary expectation', placeholder: '150000' },
  { key: 'salaryCurrency', label: 'Currency', placeholder: 'USD' },
  { key: 'noticePeriod', label: 'Notice period', placeholder: '2 weeks' },
  { key: 'earliestStartDate', label: 'Earliest start date', placeholder: 'Immediately / 2026-11-01' },
  { key: 'yearsExperience', label: 'Years of experience', placeholder: '8' },
  { key: 'highestEducation', label: 'Highest education', placeholder: "Bachelor's degree" },
]

const DEMOGRAPHIC_FIELDS: { key: 'gender' | 'race' | 'veteranStatus' | 'disabilityStatus'; label: string }[] = [
  { key: 'gender', label: 'Gender' },
  { key: 'race', label: 'Race / ethnicity' },
  { key: 'veteranStatus', label: 'Veteran status' },
  { key: 'disabilityStatus', label: 'Disability status' },
]

const inputCls = 'w-full rounded-xl border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-500 focus:bg-slate-700 focus:border-indigo-500 focus:ring-indigo-500 text-sm transition'
const labelCls = 'block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5'

function flash(target: typeof passwordMsg, msg: string) {
  target.value = msg
  setTimeout(() => { target.value = '' }, 3000)
}

function errorText(err: any) {
  const m = err?.response?.data?.message
  return Array.isArray(m) ? m.join(', ') : m || 'Something went wrong'
}

function loadForm() {
  const d = store.settings?.defaults || {}
  for (const f of TEXT_FIELDS) (form as any)[f.key] = (d as any)[f.key] ?? (form as any)[f.key]
  for (const f of DEMOGRAPHIC_FIELDS) form[f.key] = d[f.key] || DECLINE
  form.remotePreference = d.remotePreference || 'any'
  form.workAuthorizedCountries = (d.workAuthorizedCountries || []).join(', ')
  form.requiresSponsorship = d.requiresSponsorship === undefined ? '' : d.requiresSponsorship ? 'yes' : 'no'
  form.willingToRelocate = d.willingToRelocate === undefined ? '' : d.willingToRelocate ? 'yes' : 'no'
  form.customAnswers = (d.customAnswers || []).map(qa => ({ ...qa }))
}

onMounted(async () => {
  await store.fetchSettings()
  loadForm()
  const g = route.query.gmail
  if (g) {
    gmailMsg.value = g === 'connected' ? 'Gmail connected.' : 'Gmail connection failed — please try again.'
    router.replace({ query: { ...route.query, gmail: undefined } })
  }
})

async function savePassword() {
  errorMsg.value = ''
  try {
    await store.saveSettings({ portalPassword: password.value })
    password.value = ''
    flash(passwordMsg, 'Password saved')
  } catch (err) {
    errorMsg.value = errorText(err)
  }
}

async function toggleAutoSubmit(value: boolean) {
  errorMsg.value = ''
  try {
    await store.saveSettings({ autoSubmit: value })
  } catch (err) {
    errorMsg.value = errorText(err)
  }
}

async function saveDefaults() {
  saving.value = true
  errorMsg.value = ''
  try {
    const defaults: ApplicationDefaults = {}
    for (const f of TEXT_FIELDS) (defaults as any)[f.key] = String((form as any)[f.key] || '').trim()
    for (const f of DEMOGRAPHIC_FIELDS) defaults[f.key] = form[f.key].trim() || DECLINE
    defaults.remotePreference = form.remotePreference
    defaults.workAuthorizedCountries = form.workAuthorizedCountries.split(',').map(s => s.trim()).filter(Boolean)
    if (form.requiresSponsorship) defaults.requiresSponsorship = form.requiresSponsorship === 'yes'
    if (form.willingToRelocate) defaults.willingToRelocate = form.willingToRelocate === 'yes'
    defaults.customAnswers = form.customAnswers.filter(qa => qa.question.trim() && qa.answer.trim())
    await store.saveSettings({ defaults })
    flash(defaultsMsg, 'Application defaults saved')
  } catch (err) {
    errorMsg.value = errorText(err)
  } finally {
    saving.value = false
  }
}

async function connectGmail() {
  errorMsg.value = ''
  try {
    await store.connectGmail()
  } catch (err) {
    errorMsg.value = errorText(err)
  }
}
</script>

<template>
  <section class="bg-slate-800 rounded-2xl border border-slate-700/60 shadow-sm overflow-hidden">
    <div class="px-5 py-4 border-b border-slate-700/60">
      <h2 class="text-sm font-semibold text-slate-100">Auto-Apply</h2>
      <p class="text-xs text-slate-500 mt-0.5">Used when you click Apply on a Wishlist job</p>
    </div>

    <div v-if="!store.settings" class="px-5 py-6 text-sm text-slate-500">Loading…</div>

    <div v-else class="px-5 py-5 space-y-6">
      <p v-if="!store.settings.encryptionConfigured" class="text-sm text-amber-300 bg-amber-900/20 border border-amber-700/60 rounded-xl px-3 py-2">
        The server has no encryption key (CREDENTIALS_ENC_KEY), so passwords can't be saved yet.
      </p>
      <p v-if="errorMsg" class="text-sm text-red-400">{{ errorMsg }}</p>

      <!-- Portal password -->
      <div>
        <label :class="labelCls">Job portal password</label>
        <p class="text-xs text-slate-500 mb-2">
          Used with your login email to create and sign in to job-site accounts. Use a dedicated password — never your email password.
          <span :class="store.settings.portalPasswordSet ? 'text-emerald-400' : 'text-amber-400'">
            {{ store.settings.portalPasswordSet ? 'Saved.' : 'Not set.' }}
          </span>
        </p>
        <form class="flex gap-2" @submit.prevent="savePassword">
          <input v-model="password" type="password" autocomplete="new-password" minlength="8"
            :placeholder="store.settings.portalPasswordSet ? 'Enter a new password to replace it' : 'At least 8 characters'"
            :class="inputCls" />
          <button type="submit" :disabled="password.length < 8"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-medium disabled:opacity-40 flex-shrink-0">Save</button>
        </form>
        <p v-if="passwordMsg" class="text-xs text-emerald-400 mt-1.5">✓ {{ passwordMsg }}</p>
      </div>

      <!-- Auto-submit -->
      <label class="flex items-start gap-3 cursor-pointer">
        <input type="checkbox" :checked="store.settings.autoSubmit"
          @change="toggleAutoSubmit(($event.target as HTMLInputElement).checked)"
          class="mt-0.5 rounded border-slate-600 bg-slate-700 text-indigo-600 focus:ring-indigo-500" />
        <span>
          <span class="block text-sm text-slate-100 font-medium">Submit automatically</span>
          <span class="block text-xs text-slate-500">When every answer is known with confidence. Turn off to review every application before it's sent.</span>
        </span>
      </label>

      <!-- Gmail -->
      <div>
        <label :class="labelCls">Email verification</label>
        <div class="flex flex-wrap items-center gap-3">
          <template v-if="store.settings.gmail.connected">
            <span class="text-sm text-emerald-400">✓ Gmail connected<span v-if="store.settings.gmail.email" class="text-slate-400"> ({{ store.settings.gmail.email }})</span></span>
            <button @click="store.disconnectGmail()" class="text-xs text-red-400 hover:text-red-300">Disconnect</button>
          </template>
          <template v-else-if="store.settings.gmailConfigured">
            <button @click="connectGmail"
              class="px-3 py-1.5 text-sm border border-slate-600 rounded-lg text-slate-200 hover:bg-slate-700 transition">Connect Gmail (read-only)</button>
            <span class="text-xs text-slate-500">Optional — lets the agent read verification codes itself. Without it, you'll be asked to type the code during the application.</span>
          </template>
          <span v-else class="text-xs text-slate-500">When a job site sends a verification code, you'll be asked to type it during the application.</span>
        </div>
        <p v-if="gmailMsg" class="text-xs mt-1.5" :class="gmailMsg.includes('failed') ? 'text-red-400' : 'text-emerald-400'">{{ gmailMsg }}</p>
      </div>

      <!-- Application defaults -->
      <form class="space-y-4" @submit.prevent="saveDefaults">
        <div>
          <h3 class="text-sm font-semibold text-slate-100">Application defaults</h3>
          <p class="text-xs text-slate-500">Standard answers reused on every application. Fields marked * are required to use Apply.</p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div v-for="f in TEXT_FIELDS" :key="f.key" :class="f.wide ? 'sm:col-span-2' : ''">
            <label :class="labelCls">{{ f.label }}<span v-if="f.required" class="text-red-400"> *</span></label>
            <input v-model="(form as any)[f.key]" type="text" :placeholder="f.placeholder" :class="inputCls" />
          </div>

          <div class="sm:col-span-2">
            <label :class="labelCls">Countries you can work in without sponsorship<span class="text-red-400"> *</span></label>
            <input v-model="form.workAuthorizedCountries" type="text" placeholder="United States, Canada" :class="inputCls" />
          </div>
          <div>
            <label :class="labelCls">Require visa sponsorship?<span class="text-red-400"> *</span></label>
            <select v-model="form.requiresSponsorship" :class="inputCls">
              <option value="">Select…</option><option value="no">No</option><option value="yes">Yes</option>
            </select>
          </div>
          <div>
            <label :class="labelCls">Willing to relocate?</label>
            <select v-model="form.willingToRelocate" :class="inputCls">
              <option value="">Select…</option><option value="yes">Yes</option><option value="no">No</option>
            </select>
          </div>
          <div>
            <label :class="labelCls">Work arrangement</label>
            <select v-model="form.remotePreference" :class="inputCls">
              <option value="any">Any</option><option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option><option value="onsite">On-site</option>
            </select>
          </div>
        </div>

        <div>
          <h4 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Voluntary self-identification</h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div v-for="f in DEMOGRAPHIC_FIELDS" :key="f.key">
              <label :class="labelCls">{{ f.label }}</label>
              <input v-model="form[f.key]" type="text" :placeholder="DECLINE" :class="inputCls" />
            </div>
          </div>
        </div>

        <div>
          <h4 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Custom answers</h4>
          <p class="text-xs text-slate-500 mb-2">Answers to questions you see often. The agent uses them when a question closely matches.</p>
          <div v-for="(qa, i) in form.customAnswers" :key="i" class="flex flex-col sm:flex-row gap-2 mb-2">
            <input v-model="qa.question" type="text" placeholder="Question" :class="inputCls" />
            <input v-model="qa.answer" type="text" placeholder="Answer" :class="inputCls" />
            <button type="button" @click="form.customAnswers.splice(i, 1)"
              class="text-xs text-red-400 hover:text-red-300 px-2 self-start sm:self-center">Remove</button>
          </div>
          <button type="button" @click="form.customAnswers.push({ question: '', answer: '' })"
            class="text-xs text-indigo-400 hover:text-indigo-300 font-medium">+ Add answer</button>
        </div>

        <div class="flex items-center gap-3">
          <button type="submit" :disabled="saving"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-medium disabled:opacity-50">
            {{ saving ? 'Saving…' : 'Save defaults' }}
          </button>
          <span v-if="defaultsMsg" class="text-xs text-emerald-400">✓ {{ defaultsMsg }}</span>
        </div>
      </form>
    </div>
  </section>
</template>
