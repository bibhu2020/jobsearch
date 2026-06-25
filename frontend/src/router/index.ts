import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/pipeline' },
    { path: '/login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
    { path: '/register', component: () => import('@/views/RegisterView.vue'), meta: { public: true } },
    { path: '/pipeline', component: () => import('@/views/PipelineView.vue') },
    { path: '/suggestions', component: () => import('@/views/SuggestionsView.vue') },
    { path: '/profile', component: () => import('@/views/ProfileView.vue') },
    { path: '/interviewer', component: () => import('@/views/InterviewerProjectsView.vue') },
    { path: '/interviewer/projects/:id', component: () => import('@/views/InterviewerProjectView.vue') },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!to.meta.public && !token) return '/login'
})

export default router
