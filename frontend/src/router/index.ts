import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/pipeline' },
    { path: '/login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
    { path: '/register', redirect: '/login' },
    { path: '/auth/callback', component: () => import('@/views/AuthCallbackView.vue'), meta: { public: true } },
    { path: '/pipeline', component: () => import('@/views/PipelineView.vue') },
    { path: '/suggestions', component: () => import('@/views/SuggestionsView.vue') },
    { path: '/profile', component: () => import('@/views/ProfileView.vue') },
    { path: '/guide', component: () => import('@/views/GuideView.vue') },
    { path: '/interviewer', component: () => import('@/views/InterviewerProjectsView.vue') },
    { path: '/interviewer/projects/:id', component: () => import('@/views/InterviewerProjectView.vue') },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!to.meta.public && !token) return '/login'
})

export default router
